from flask import Flask, request, jsonify
from functools import wraps
import os
import secrets
import hashlib
from datetime import datetime
from database import APIKeyDatabase

app = Flask(__name__)
db = APIKeyDatabase()

# ============= CONFIGURATION =============
# Admin API key from environment variable (REQUIRED)
ADMIN_API_KEY = os.getenv('JAI_ADMIN_KEY')
if not ADMIN_API_KEY:
    print("\n❌ ERROR: JAI_ADMIN_KEY environment variable not set!")
    print("Set it in Render dashboard: Environment Variables -> JAI_ADMIN_KEY")
    print("Example: jai_admin_32chars_long_secret_key_here\n")
    exit(1)

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
        }
    },
    'pro': {
        'name': 'Pro Tier',
        'limits': {'daily': 5000, 'rate_per_minute': 50, 'is_admin': False},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': True},
            'document_search': {'enabled': True},
            'memory_long_term': {'enabled': True}
        }
    },
    'admin': {
        'name': 'Admin',
        'limits': {'daily': None, 'rate_per_minute': 500, 'is_admin': True},
        'features': {
            'chat': {'enabled': True},
            'document_upload': {'enabled': True},
            'document_search': {'enabled': True},
            'memory_long_term': {'enabled': True}
        }
    }
}

# ============= SECURE AUTHENTICATION =============

def require_api_key(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        validation = db.validate_key(api_key)
        if not validation or 'error' in validation:
            return jsonify({'error': validation.get('error', 'Invalid API key')}), 401
        
        request.key_data = validation['key_data']
        request.api_key = api_key
        db.increment_usage(api_key)
        return func(*args, **kwargs)
    return decorated

def require_admin(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        # Check if the key matches the admin key from env var
        if not api_key or api_key != ADMIN_API_KEY:
            return jsonify({'error': 'Admin access required'}), 403
        
        request.admin_key = api_key
        return func(*args, **kwargs)
    return decorated

def require_feature(feature_name):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not db.has_feature_access(api_key, feature_name):
                return jsonify({
                    'error': f'Feature "{feature_name}" not available in your tier',
                    'upgrade_required': True
                }), 403
            return func(*args, **kwargs)
        return decorated
    return decorator

# ============= INITIAL ADMIN KEY SETUP =============

def setup_admin_key():
    """Check if admin key exists in DB, create if not"""
    # Check if admin key already exists in database
    admin_exists = False
    for key, data in db.keys.items():
        if key == ADMIN_API_KEY:
            admin_exists = True
            break
    
    # If not in DB, add it
    if not admin_exists:
        db.create_key(
            name="Master Admin",
            limits=TIERS['admin']['limits'],
            features=TIERS['admin']['features'],
            user_id="admin"
        )
        print(f"✅ Admin key initialized in database")
    else:
        print(f"✅ Admin key found in database")

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
    
    # Determine tier from rate limit
    rate_limit = request.key_data['limits'].get('rate_per_minute', 0)
    tier_names = {2: 'free', 50: 'pro', 500: 'admin'}
    tier = tier_names.get(rate_limit, 'custom')
    
    return jsonify({
        'reply': f"Jai (Joshua's AI) says: '{message}'",
        'tier': tier,
        'rate_limit': f"{rate_limit} req/min" if rate_limit else 'unlimited'
    })

@app.route('/api/document/upload', methods=['POST'])
@require_api_key
@require_feature('document_upload')
def upload_document():
    data = request.json
    return jsonify({
        'message': 'Document uploaded',
        'filename': data.get('filename'),
        'status': 'success'
    })

@app.route('/api/document/search', methods=['POST'])
@require_api_key
@require_feature('document_search')
def search_document():
    return jsonify({'message': 'Search results', 'results': []})

# ============= SECURE ADMIN ENDPOINTS =============

@app.route('/admin/keys/create', methods=['POST'])
@require_admin
def admin_create_key():
    """Create a new API key - ADMIN ONLY"""
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
        'tier': tier
    })

@app.route('/admin/keys/revoke', methods=['POST'])
@require_admin
def admin_revoke_key():
    """Revoke an API key - ADMIN ONLY"""
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({'error': 'api_key required'}), 400
    
    # Prevent revoking the master admin key
    if api_key == ADMIN_API_KEY:
        return jsonify({'error': 'Cannot revoke master admin key'}), 403
    
    if db.revoke_key(api_key):
        return jsonify({'success': True})
    return jsonify({'error': 'Key not found'}), 404

@app.route('/admin/keys/list', methods=['GET'])
@require_admin
def admin_list_keys():
    """List all keys (without showing the actual keys) - ADMIN ONLY"""
    keys = db.list_keys()
    # Remove sensitive data
    for key in keys:
        key.pop('api_key', None)
    return jsonify({'keys': keys, 'total': len(keys)})

@app.route('/admin/stats', methods=['GET'])
@require_admin
def admin_stats():
    """Get system stats - ADMIN ONLY"""
    keys = db.list_keys()
    total_requests = sum(k['usage']['total_requests'] for k in keys)
    active_keys = sum(1 for k in keys if k['active'])
    
    return jsonify({
        'total_keys': len(keys),
        'active_keys': active_keys,
        'total_requests': total_requests,
        'tiers': {
            'free': sum(1 for k in keys if k['limits'].get('rate_per_minute') == 2),
            'pro': sum(1 for k in keys if k['limits'].get('rate_per_minute') == 50),
            'admin': sum(1 for k in keys if k['limits'].get('is_admin'))
        }
    })

@app.route('/')
def index():
    return jsonify({
        'name': 'Jai - Joshua\'s Artificial Intelligence',
        'version': '2.0.0',
        'auth_required': True,
        'endpoints': {
            'public': ['/health'],
            'protected': ['/api/chat', '/api/document/upload', '/api/document/search'],
            'admin': ['/admin/keys/create', '/admin/keys/revoke', '/admin/keys/list', '/admin/stats']
        }
    })

if __name__ == '__main__':
    # Setup admin key from environment variable
    setup_admin_key()
    
    print("\n" + "="*60)
    print("🤖 JAI SERVER STARTING")
    print("="*60)
    print(f"Admin Key: {ADMIN_API_KEY[:20]}... (from env variable)")
    print(f"Database: {DB_FILE}")
    print("="*60 + "\n")
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)