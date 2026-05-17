from flask import Flask, request, jsonify
import requests
from typing import Dict, Optional
import os
from database import db
from functools import wraps

app = Flask(__name__)

# Service URLs (Render will assign these)
SERVICES = {
    'chat': os.getenv('JAI_CHAT_URL', 'http://localhost:8001'),
    'document': os.getenv('JAI_DOCUMENT_URL', 'http://localhost:8002'),
    'memory': os.getenv('JAI_MEMORY_URL', 'http://localhost:8003')
}

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Missing API key. Please provide X-API-Key header'}), 401
        
        # Validate key
        validation = db.validate_key(api_key)
        
        if 'error' in validation:
            return jsonify({'error': validation['error']}), 429 if 'limit' in validation['error'] else 401
        
        # Add key data to request context
        request.key_data = validation['key_data']
        request.api_key = api_key
        
        # Increment usage
        db.increment_usage(api_key)
        
        return f(*args, **kwargs)
    return decorated_function

class ServiceRouter:
    def __init__(self):
        self.service_health = {name: True for name in SERVICES}
    
    def route_to_chat(self, message: str, context_id: str, user_id: str):
        """Route chat requests with memory context"""
        memory_context = self._get_memory(user_id, context_id)
        
        response = requests.post(
            f"{SERVICES['chat']}/generate",
            json={
                'message': message,
                'context_id': context_id,
                'user_id': user_id,
                'memory_context': memory_context
            },
            timeout=10
        )
        
        self._store_memory(user_id, context_id, message, response.json())
        return response.json()
    
    def route_to_document(self, action: str, **kwargs):
        """Route document operations"""
        response = requests.post(
            f"{SERVICES['document']}/{action}",
            json=kwargs,
            timeout=30
        )
        return response.json()
    
    def _get_memory(self, user_id: str, context_id: str) -> Dict:
        """Fetch relevant memories"""
        try:
            response = requests.get(
                f"{SERVICES['memory']}/recall",
                params={'user_id': user_id, 'context_id': context_id},
                timeout=5
            )
            return response.json()
        except:
            return {'memories': [], 'context': {}}
    
    def _store_memory(self, user_id: str, context_id: str, message: str, response: Dict):
        """Store conversation in memory service"""
        try:
            requests.post(
                f"{SERVICES['memory']}/store",
                json={
                    'user_id': user_id,
                    'context_id': context_id,
                    'interaction': {
                        'input': message,
                        'output': response.get('reply', ''),
                        'timestamp': __import__('time').time()
                    }
                },
                timeout=5
            )
        except:
            pass

router = ServiceRouter()

# ============= API KEY MANAGEMENT ENDPOINTS =============

@app.route('/admin/keys/create', methods=['POST'])
@require_api_key
def create_api_key():
    """Create a new API key (requires admin key)"""
    # Check if requester has admin privileges
    if not request.key_data.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    data = request.json
    name = data.get('name')
    limits = data.get('limits', {})
    user_id = data.get('user_id')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    # Create the key
    new_key = db.create_key(name, limits, user_id)
    
    return jsonify({
        'message': 'API key created successfully',
        'api_key': new_key['api_key'],  # Only shown once!
        'key_id': new_key['key_id'],
        'limits': new_key['limits']
    })

@app.route('/admin/keys/revoke', methods=['POST'])
@require_api_key
def revoke_api_key():
    """Revoke an API key"""
    if not request.key_data.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    api_key = request.json.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 400
    
    if db.revoke_key(api_key):
        return jsonify({'message': 'API key revoked successfully'})
    return jsonify({'error': 'API key not found'}), 404

@app.route('/admin/keys/list', methods=['GET'])
@require_api_key
def list_api_keys():
    """List all API keys"""
    if not request.key_data.get('limits', {}).get('is_admin', False):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    keys = db.list_keys()
    return jsonify({'keys': keys, 'total': len(keys)})

@app.route('/admin/keys/info', methods=['GET'])
@require_api_key
def get_key_info():
    """Get info about your own API key"""
    api_key = request.headers.get('X-API-Key')
    info = db.get_key_info(api_key)
    
    if info:
        return jsonify(info)
    return jsonify({'error': 'Key not found'}), 404

# ============= PUBLIC API ENDPOINTS (require API key) =============

@app.route('/api/chat', methods=['POST'])
@require_api_key
def chat():
    """Main chat endpoint - requires API key"""
    data = request.json
    
    # Use user_id from key if not provided
    user_id = data.get('user_id') or request.key_data['user_id']
    context_id = data.get('context_id', 'default')
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        result = router.route_to_chat(message, context_id, user_id)
        
        # Add rate limit info to response
        result['rate_limit'] = {
            'remaining_daily': request.key_data['limits'].get('daily', 'unlimited') - request.key_data['usage']['daily_requests'],
            'used_today': request.key_data['usage']['daily_requests'],
            'total_used': request.key_data['usage']['total_requests']
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/upload', methods=['POST'])
@require_api_key
def upload_document():
    """Upload document - requires API key"""
    try:
        result = router.route_to_document(
            'upload',
            filename=request.json.get('filename'),
            content=request.json.get('content')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/search', methods=['POST'])
@require_api_key
def search_document():
    """Search document - requires API key"""
    try:
        result = router.route_to_document(
            'search',
            query=request.json.get('query'),
            document_id=request.json.get('document_id')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory/context', methods=['GET'])
@require_api_key
def get_memory_context():
    """Get user's memory context"""
    user_id = request.args.get('user_id') or request.key_data['user_id']
    context_id = request.args.get('context_id', 'default')
    
    try:
        result = router._get_memory(user_id, context_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= PUBLIC ENDPOINTS (no key required) =============

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'services': SERVICES,
        'auth_required': True
    })

@app.route('/', methods=['GET'])
def info():
    return jsonify({
        'name': 'Jai - Joshua\'s Artificial Intelligence',
        'version': '2.0.0',
        'auth_required': True,
        'endpoints': {
            'public': ['/health', '/'],
            'protected': ['/api/chat', '/api/document/upload', '/api/document/search', '/api/memory/context'],
            'admin': ['/admin/keys/create', '/admin/keys/revoke', '/admin/keys/list']
        }
    })

if __name__ == '__main__':
    # Create initial admin key if none exists
    if len(db.list_keys()) == 0:
        admin_key = db.create_key(
            name="Admin Key",
            limits={
                'daily': 10000,
                'monthly': 100000,
                'total': None,
                'rate_per_minute': 100,
                'is_admin': True
            },
            user_id="admin"
        )
        print(f"\n⚠️  INITIAL ADMIN API KEY (save this!): {admin_key['api_key']}\n")
    
    app.run(host='0.0.0.0', port=8000)