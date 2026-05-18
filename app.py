from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

# ============= CONFIGURATION =============
JAI_API_URL = os.getenv('JAI_API_URL', 'https://jai-api-g740.onrender.com')

# Rate limiting storage (per API key, in memory)
# Structure: {api_key: {'timestamps': [], 'daily_count': 0, 'last_reset': date}}
rate_limit_store = {}

# ============= HELPER FUNCTIONS =============

def validate_with_jai_api(api_key, session_token):
    """
    Validate API key and session with jai-api
    Returns limits and user info if valid, None otherwise
    """
    try:
        response = requests.post(
            f"{JAI_API_URL}/api/validate-key",
            json={
                'api_key': api_key,
                'session_token': session_token
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                return {
                    'valid': True,
                    'username': data.get('username'),
                    'key_name': data.get('key_name'),
                    'tier': data.get('tier'),
                    'rate_per_minute': data.get('rate_per_minute', 2),
                    'daily_limit': data.get('daily_limit', 100),
                    'total_requests': data.get('total_requests', 0)
                }
        
        return {'valid': False, 'error': 'Invalid credentials'}
    
    except requests.exceptions.Timeout:
        return {'valid': False, 'error': 'Authentication service timeout'}
    except requests.exceptions.ConnectionError:
        return {'valid': False, 'error': 'Cannot connect to authentication service'}
    except Exception as e:
        return {'valid': False, 'error': f'Authentication error: {str(e)}'}

def check_rate_limit(api_key, rate_per_minute, daily_limit):
    """
    Enforce rate limits locally
    Returns {'allowed': bool, 'reason': str, 'remaining': int}
    """
    now = datetime.now()
    today = now.date()
    
    # Initialize store for this API key if not exists
    if api_key not in rate_limit_store:
        rate_limit_store[api_key] = {
            'timestamps': [],
            'daily_count': 0,
            'last_reset': today.isoformat()
        }
    
    store = rate_limit_store[api_key]
    
    # Reset daily counter if new day
    if store['last_reset'] != today.isoformat():
        store['daily_count'] = 0
        store['last_reset'] = today.isoformat()
    
    # Check daily limit
    if daily_limit and store['daily_count'] >= daily_limit:
        return {
            'allowed': False, 
            'reason': f'Daily limit of {daily_limit} requests exceeded. Resets at midnight UTC.',
            'remaining': 0
        }
    
    # Clean old timestamps (older than 1 minute)
    minute_ago = now - timedelta(minutes=1)
    store['timestamps'] = [
        ts for ts in store['timestamps']
        if datetime.fromisoformat(ts) > minute_ago
    ]
    
    # Check per-minute rate
    current_minute_requests = len(store['timestamps'])
    if current_minute_requests >= rate_per_minute:
        return {
            'allowed': False,
            'reason': f'Rate limit of {rate_per_minute} requests per minute exceeded. Please wait.',
            'remaining': 0
        }
    
    # Calculate remaining for this minute
    remaining_this_minute = rate_per_minute - current_minute_requests - 1
    
    # Record this request
    store['timestamps'].append(now.isoformat())
    store['daily_count'] += 1
    
    # Report usage back to jai-api asynchronously (don't wait for response)
    try:
        # Use a separate thread or just fire and forget
        requests.post(
            f"{JAI_API_URL}/api/track-usage",
            json={'api_key': api_key},
            timeout=1
        )
    except:
        pass  # Non-critical, don't block the request
    
    return {
        'allowed': True,
        'remaining_this_minute': remaining_this_minute,
        'daily_remaining': (daily_limit - store['daily_count']) if daily_limit else 'unlimited'
    }

# ============= AUTHENTICATION DECORATOR =============

def require_auth(f):
    """
    Decorator that requires both API key and session token
    Validates both with jai-api before allowing access
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        session_token = request.headers.get('X-Session-Token')
        
        # Check if both headers are present
        if not api_key:
            return jsonify({
                'error': 'API key required',
                'message': 'Please provide X-API-Key header'
            }), 401
        
        if not session_token:
            return jsonify({
                'error': 'Session token required',
                'message': 'Please provide X-Session-Token header. Login at the dashboard first.'
            }), 401
        
        # Validate with jai-api
        validation = validate_with_jai_api(api_key, session_token)
        
        if not validation.get('valid'):
            return jsonify({
                'error': validation.get('error', 'Invalid API key or session'),
                'message': 'Please check your API key and ensure you are logged in'
            }), 401
        
        # Check rate limits
        rate_check = check_rate_limit(
            api_key,
            validation['rate_per_minute'],
            validation['daily_limit']
        )
        
        if not rate_check['allowed']:
            return jsonify({
                'error': rate_check['reason'],
                'retry_after': 60  # Suggest retry after 60 seconds
            }), 429
        
        # Store validation data for the endpoint
        request.key_info = {
            'api_key': api_key,
            'username': validation['username'],
            'key_name': validation['key_name'],
            'tier': validation['tier'],
            'rate_per_minute': validation['rate_per_minute'],
            'daily_limit': validation['daily_limit']
        }
        
        # Store rate limit info for response headers
        request.rate_info = {
            'remaining_this_minute': rate_check.get('remaining_this_minute', 0),
            'daily_remaining': rate_check.get('daily_remaining', 0)
        }
        
        return f(*args, **kwargs)
    
    return decorated

# ============= SYNC ENDPOINT (for dashboard) =============

@app.route('/api/sync-key', methods=['POST'])
def sync_api_key():
    """
    Endpoint for dashboard to sync new API keys
    This is called when user creates a key in the dashboard
    """
    data = request.json
    api_key = data.get('api_key')
    key_data = data.get('key_data')
    session_token = request.headers.get('X-Session-Token')
    
    if not api_key or not key_data:
        return jsonify({'error': 'API key and key data required'}), 400
    
    # Verify session with jai-api first
    try:
        response = requests.post(
            f"{JAI_API_URL}/api/verify-session",
            json={'session_token': session_token},
            timeout=5
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Invalid session'}), 401
        
        session_data = response.json()
        if not session_data.get('valid'):
            return jsonify({'error': 'Invalid session'}), 401
        
        # Add username to key data
        key_data['username'] = session_data.get('username')
        
    except Exception as e:
        return jsonify({'error': f'Session verification failed: {str(e)}'}), 401
    
    # Store the key locally (jai1 only needs basic info for rate limiting)
    # In production, jai1 might not even need to store keys - it just validates each time
    # For performance, we could cache but for now we'll just acknowledge
    
    return jsonify({
        'success': True,
        'message': 'API key synced successfully',
        'note': 'jai1 will validate this key with jai-api on each request'
    })

# ============= API ENDPOINTS =============

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """
    Main chat endpoint
    Requires X-API-Key and X-Session-Token headers
    """
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Generate response based on tier
    tier = request.key_info['tier']
    key_name = request.key_info['key_name']
    username = request.key_info['username']
    rate_per_minute = request.key_info['rate_per_minute']
    
    # Simple response logic (can be enhanced)
    message_lower = message.lower()
    
    if 'hello' in message_lower or 'hi' in message_lower:
        reply = f"Hello {username}! I'm Jai (Joshua's AI) using your '{key_name}' key on {tier.upper()} tier. How can I help you today?"
    elif 'who are you' in message_lower:
        reply = f"I'm Jai - Joshua's Artificial Intelligence. You're using the {tier.upper()} tier with rate limit of {rate_per_minute} requests per minute."
    elif 'rate' in message_lower or 'limit' in message_lower:
        reply = f"Your {tier.upper()} tier allows {rate_per_minute} requests per minute. You have {request.rate_info['remaining_this_minute']} remaining this minute."
    else:
        reply = f"Jai ({tier.upper()} Tier) says: '{message}'"
    
    return jsonify({
        'success': True,
        'reply': reply,
        'tier': tier,
        'key_name': key_name,
        'user': username,
        'rate_limit': {
            'per_minute': rate_per_minute,
            'remaining_this_minute': request.rate_info['remaining_this_minute'],
            'daily_remaining': request.rate_info['daily_remaining']
        }
    })

@app.route('/api/me', methods=['GET'])
@require_auth
def get_me():
    """
    Get current user and key information
    """
    return jsonify({
        'success': True,
        'user': request.key_info['username'],
        'key_name': request.key_info['key_name'],
        'tier': request.key_info['tier'],
        'rate_per_minute': request.key_info['rate_per_minute'],
        'daily_limit': request.key_info['daily_limit']
    })

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    # Check if jai-api is reachable
    jai_api_status = 'unknown'
    try:
        response = requests.get(f"{JAI_API_URL}/health", timeout=2)
        jai_api_status = 'healthy' if response.status_code == 200 else 'unhealthy'
    except:
        jai_api_status = 'unreachable'
    
    return jsonify({
        'status': 'healthy',
        'service': 'jai1',
        'version': '2.0.0',
        'jai_api_status': jai_api_status,
        'jai_api_url': JAI_API_URL,
        'active_rate_limits': len(rate_limit_store)
    })

@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint with service info
    """
    return jsonify({
        'name': 'Jai1 - Joshua\'s AI Gateway',
        'version': '2.0.0',
        'description': 'API gateway for Jai AI services',
        'authentication': {
            'required_headers': ['X-API-Key', 'X-Session-Token'],
            'get_session': 'Login at https://jai-api-g740.onrender.com'
        },
        'endpoints': {
            'POST /api/chat': 'Send a message to Jai AI',
            'GET /api/me': 'Get current user and key info',
            'GET /health': 'Health check',
            'POST /api/sync-key': 'Sync API key from dashboard'
        },
        'rate_limits': {
            'free': '2 requests per minute, 100 per day',
            'pro': '15 requests per minute, 10,000 per day',
            'enterprise': '1000 requests per minute, unlimited daily'
        }
    })

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============= MAIN =============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*60)
    print("🚀 JAI1 - Joshua's AI Gateway")
    print("="*60)
    print(f"Port: {port}")
    print(f"JAI API URL: {JAI_API_URL}")
    print(f"Rate limit store size: {len(rate_limit_store)}")
    print("\nRequired Headers for /api/* endpoints:")
    print("  X-API-Key: Your API key from dashboard")
    print("  X-Session-Token: Your session token from login")
    print("\nEndpoints:")
    print("  POST /api/chat - Send message")
    print("  GET  /api/me - Get user info")
    print("  GET  /health - Health check")
    print("  POST /api/sync-key - Sync API key")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port)