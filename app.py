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
rate_limit_store = {}  # api_key -> {'timestamps': [], 'daily_count': 0, 'last_reset': iso}

def get_rate_limits(api_key, session_token):
    """Ask jai-api for the limits of this API key"""
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
            return {
                'valid': True,
                'username': data.get('username'),
                'key_name': data.get('key_name'),
                'tier': data.get('tier'),
                'rate_per_minute': data.get('rate_per_minute', 2),
                'daily_limit': data.get('daily_limit', 100),
                'total_requests': data.get('total_requests', 0)
            }
    except Exception as e:
        print(f"Error validating with jai-api: {e}")
    
    return {'valid': False, 'error': 'Invalid API key or session'}

def check_rate_limit(api_key, rate_per_minute, daily_limit):
    """Enforce rate limits locally (jai1's responsibility)"""
    now = datetime.now()
    today = now.date()
    
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
        return {'allowed': False, 'reason': f'Daily limit of {daily_limit} exceeded'}
    
    # Clean old timestamps (older than 1 minute)
    minute_ago = now - timedelta(minutes=1)
    store['timestamps'] = [
        ts for ts in store['timestamps']
        if datetime.fromisoformat(ts) > minute_ago
    ]
    
    # Check per-minute rate
    if len(store['timestamps']) >= rate_per_minute:
        return {'allowed': False, 'reason': f'Rate limit of {rate_per_minute} requests per minute exceeded'}
    
    # Record this request
    store['timestamps'].append(now.isoformat())
    store['daily_count'] += 1
    
    # Also report back to jai-api for total counting
    report_usage_to_api(api_key)
    
    return {'allowed': True}

def report_usage_to_api(api_key):
    """Report usage back to jai-api for total request counting"""
    try:
        requests.post(
            f"{JAI_API_URL}/api/track-usage",
            json={'api_key': api_key},
            timeout=2
        )
    except:
        pass  # Non-critical, don't block the request

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        session_token = request.headers.get('X-Session-Token')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not session_token:
            return jsonify({'error': 'Session token required'}), 401
        
        # Validate with jai-api (gets limits)
        validation = get_rate_limits(api_key, session_token)
        
        if not validation.get('valid'):
            return jsonify({'error': validation.get('error', 'Invalid credentials')}), 401
        
        # Store key info for the endpoint
        request.key_info = {
            'api_key': api_key,
            'username': validation['username'],
            'key_name': validation['key_name'],
            'tier': validation['tier'],
            'rate_per_minute': validation['rate_per_minute'],
            'daily_limit': validation['daily_limit']
        }
        
        # Enforce rate limits
        rate_check = check_rate_limit(
            api_key,
            validation['rate_per_minute'],
            validation['daily_limit']
        )
        
        if not rate_check['allowed']:
            return jsonify({'error': rate_check['reason']}), 429
        
        return f(*args, **kwargs)
    return decorated

# ============= API ENDPOINTS =============

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    data = request.json
    message = data.get('message', '')
    
    return jsonify({
        'reply': f"Jai (Joshua's AI) - {request.key_info['tier'].upper()} Tier says: '{message}'",
        'tier': request.key_info['tier'],
        'rate_limit': f"{request.key_info['rate_per_minute']} req/min",
        'key_name': request.key_info['key_name'],
        'user': request.key_info['username']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'jai1'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n🚀 Jai1 Server running on port {port}")
    print(f"   Validates with: {JAI_API_URL}")
    print(f"   Headers required: X-API-Key + X-Session-Token\n")
    app.run(host='0.0.0.0', port=port)