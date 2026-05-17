from flask import Flask, request, jsonify
from functools import wraps
import os
from datetime import datetime
from database import APIKeyDatabase

app = Flask(__name__)
db = APIKeyDatabase()

# ============= TIER DEFINITIONS =============
TIERS = {
    'free': {
        'name': 'Free Tier',
        'limits': {'daily': 100, 'rate_per_minute': 2, 'is_admin': False},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': False},
            'document_search': {'enabled': False},
            'memory_long_term': {'enabled': False}
        },
        'description': '2 requests per minute, chat only'
    },
    'pro': {
        'name': 'Pro Tier',
        'limits': {'daily': 5000, 'rate_per_minute': 50, 'is_admin': False},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': True},
            'document_search': {'enabled': True},
            'memory_long_term': {'enabled': True}
        },
        'description': 'Full features'
    },
    'enterprise': {
        'name': 'Enterprise Tier',
        'limits': {'daily': None, 'rate_per_minute': 200, 'is_admin': False},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': True},
            'document_search': {'enabled': True},
            'memory_long_term': {'enabled': True}
        },
        'description': 'Unlimited'
    },
    'admin': {
        'name': 'Admin',
        'limits': {'daily': None, 'rate_per_minute': 500, 'is_admin': True},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': True},
            'document_search': {'enabled': True},
            'memory_long_term': {'enabled': True}
        },
        'description': 'Admin access'
    }
}

# ============= AUTHENTICATION =============
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        validation = db.validate_key(api_key)
        if 'error' in validation:
            return jsonify({'error': validation['error']}), 429
        
        request.key_data = validation['key_data']
        request.api_key = api_key
        db.increment_usage(api_key)
        return f(*args, **kwargs)
    return decorated

def require_feature(feature):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not db.has_feature_access(api_key, feature):
                return jsonify({'error': f'Feature {feature} not available in your tier', 
                              'upgrade_message': 'Upgrade to access this feature'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============= PUBLIC ENDPOINTS =============
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': '2.0.0'})

@app.route('/api/chat', methods=['POST'])
@require_api_key
@require_feature('chat')
def chat():
    data = request.json
    message = data.get('message', '')
    
    # Simple response based on tier
    tier = 'free' if request.key_data['limits'].get('rate_per_minute') == 2 else 'pro'
    
    response = f"Jai (Joshua's AI) - {TIERS[tier]['name']} says: I heard '{message}'"
    
    return jsonify({
        'reply': response,
        'tier': tier,
        'rate_limit': f"{request.key_data['limits'].get('rate_per_minute', 'unlimited')} req/min"
    })

@app.route('/api/document/upload', methods=['POST'])
@require_api_key
@require_feature('document_upload')
def upload_document():
    return jsonify({'message': 'Document uploaded', 'status': 'success'})

@app.route('/api/document/search', methods=['POST'])
@require_api_key
@require_feature('document_search')
def search_document():
    return jsonify({'message': 'Document search results', 'results': []})

# ============= ADMIN ENDPOINTS =============
@app.route('/admin/keys/create', methods=['POST'])
def admin_create_key():
    api_key = request.headers.get('X-API-Key')
    key_info = db.get_key_info(api_key)
    
    if not key_info or not key_info.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    data = request.json
    tier = data.get('tier', 'free')
    
    if tier not in TIERS:
        return jsonify({'error': f'Invalid tier. Options: {list(TIERS.keys())}'}), 400
    
    tier_config = TIERS[tier]
    new_key = db.create_key(
        name=data.get('name', f'{tier} User'),
        limits=tier_config['limits'],
        features=tier_config['features'],
        user_id=data.get('user_id')
    )
    
    return jsonify({
        'success': True,
        'api_key': new_key['api_key'],
        'key_id': new_key['key_id'],
        'tier': tier,
        'description': tier_config['description']
    })

@app.route('/admin/keys/list', methods=['GET'])
def admin_list_keys():
    api_key = request.headers.get('X-API-Key')
    key_info = db.get_key_info(api_key)
    
    if not key_info or not key_info.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    return jsonify({'keys': db.list_keys()})

@app.route('/admin/keys/revoke', methods=['POST'])
def admin_revoke_key():
    api_key = request.headers.get('X-API-Key')
    key_info = db.get_key_info(api_key)
    
    if not key_info or not key_info.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    key_to_revoke = request.json.get('api_key')
    if db.revoke_key(key_to_revoke):
        return jsonify({'success': True})
    return jsonify({'error': 'Key not found'}), 404

@app.route('/')
def index():
    return jsonify({
        'name': 'Jai - Joshua\'s Artificial Intelligence',
        'version': '2.0.0',
        'auth_required': True,
        'tiers': ['free (2 req/min)', 'pro', 'enterprise', 'admin']
    })

if __name__ == '__main__':
    # Create default admin key if none exists
    admin_keys = [k for k, v in db.keys.items() if v.get('limits', {}).get('is_admin')]
    
    if not admin_keys:
        admin_key = db.create_key(
            name="Master Admin",
            limits=TIERS['admin']['limits'],
            features=TIERS['admin']['features'],
            user_id="admin"
        )
        print("\n" + "="*60)
        print("🔑 ADMIN API KEY (SAVE THIS!)")
        print("="*60)
        print(f"API Key: {admin_key['api_key']}")
        print("="*60 + "\n")
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)