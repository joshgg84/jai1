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

# Rate limiting storage
rate_limit_store = {}

# ============= HELPER FUNCTIONS =============

def validate_with_jai_api(api_key, session_token):
    """Validate API key and session with jai-api"""
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
    
    except Exception as e:
        return {'valid': False, 'error': f'Authentication error: {str(e)}'}

def check_rate_limit(api_key, rate_per_minute, daily_limit):
    """Enforce rate limits locally"""
    now = datetime.now()
    today = now.date()
    
    if api_key not in rate_limit_store:
        rate_limit_store[api_key] = {
            'timestamps': [],
            'daily_count': 0,
            'last_reset': today.isoformat()
        }
    
    store = rate_limit_store[api_key]
    
    if store['last_reset'] != today.isoformat():
        store['daily_count'] = 0
        store['last_reset'] = today.isoformat()
    
    if daily_limit and store['daily_count'] >= daily_limit:
        return {
            'allowed': False,
            'reason': f'Daily limit of {daily_limit} requests exceeded',
            'remaining': 0
        }
    
    minute_ago = now - timedelta(minutes=1)
    store['timestamps'] = [
        ts for ts in store['timestamps']
        if datetime.fromisoformat(ts) > minute_ago
    ]
    
    current_minute_requests = len(store['timestamps'])
    if current_minute_requests >= rate_per_minute:
        return {
            'allowed': False,
            'reason': f'Rate limit of {rate_per_minute} requests per minute exceeded',
            'remaining': 0
        }
    
    remaining_this_minute = rate_per_minute - current_minute_requests - 1
    
    store['timestamps'].append(now.isoformat())
    store['daily_count'] += 1
    
    # Report usage asynchronously
    try:
        requests.post(
            f"{JAI_API_URL}/api/track-usage",
            json={'api_key': api_key},
            timeout=1
        )
    except:
        pass
    
    return {
        'allowed': True,
        'remaining_this_minute': remaining_this_minute,
        'daily_remaining': (daily_limit - store['daily_count']) if daily_limit else 'unlimited'
    }

# ============= AUTHENTICATION DECORATOR =============

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        session_token = request.headers.get('X-Session-Token')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not session_token:
            return jsonify({'error': 'Session token required'}), 401
        
        validation = validate_with_jai_api(api_key, session_token)
        
        if not validation.get('valid'):
            return jsonify({'error': validation.get('error', 'Invalid credentials')}), 401
        
        rate_check = check_rate_limit(
            api_key,
            validation['rate_per_minute'],
            validation['daily_limit']
        )
        
        if not rate_check['allowed']:
            return jsonify({'error': rate_check['reason']}), 429
        
        request.key_info = {
            'api_key': api_key,
            'username': validation['username'],
            'key_name': validation['key_name'],
            'tier': validation['tier'],
            'rate_per_minute': validation['rate_per_minute'],
            'daily_limit': validation['daily_limit']
        }
        
        request.rate_info = {
            'remaining_this_minute': rate_check.get('remaining_this_minute', 0),
            'daily_remaining': rate_check.get('daily_remaining', 0)
        }
        
        return f(*args, **kwargs)
    return decorated

# ============= HOME ROUTE =============

@app.route('/', methods=['GET'])
def home():
    """Simple home route"""
    return jsonify({"Jai": "ok"})

# ============= API ENDPOINTS =============

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    tier = request.key_info['tier']
    key_name = request.key_info['key_name']
    username = request.key_info['username']
    rate_per_minute = request.key_info['rate_per_minute']
    
    message_lower = message.lower()
    
    if 'hello' in message_lower or 'hi' in message_lower:
        reply = f"Hello {username}! I'm Jai using your '{key_name}' key on {tier.upper()} tier."
    elif 'who are you' in message_lower:
        reply = f"I'm Jai - Joshua's Artificial Intelligence. You're on {tier.upper()} tier with {rate_per_minute} req/min."
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
    jai_api_status = 'unknown'
    try:
        response = requests.get(f"{JAI_API_URL}/health", timeout=2)
        jai_api_status = 'healthy' if response.status_code == 200 else 'unhealthy'
    except:
        jai_api_status = 'unreachable'
    
    return jsonify({
        'status': 'healthy',
        'service': 'jai1',
        'jai_api_status': jai_api_status,
        'active_rate_limits': len(rate_limit_store)
    })

# ============= MAIN =============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*60)
    print("🚀 JAI1 - Joshua's AI Gateway")
    print("="*60)
    print(f"Port: {port}")
    print(f"JAI API URL: {JAI_API_URL}")
    print("\n✅ Home route: GET / -> {'Jai': 'ok'}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port)