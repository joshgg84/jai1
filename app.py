from flask import Flask, request, jsonify
import requests
import hashlib
import hmac
import secrets
import pyotp
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional
import os
import json

app = Flask(__name__)

# ============= CONFIGURATION =============

# Service URLs (Render will assign these)
SERVICES = {
    'chat': os.getenv('JAI_CHAT_URL', 'http://localhost:8001'),
    'document': os.getenv('JAI_DOCUMENT_URL', 'http://localhost:8002'),
    'memory': os.getenv('JAI_MEMORY_URL', 'http://localhost:8003')
}

# Database file for API keys
DB_FILE = 'api_keys.json'

# ============= DATABASE =============

class APIKeyDatabase:
    def __init__(self, db_file='api_keys.json'):
        self.db_file = db_file
        self.keys = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    self.keys = json.load(f)
            except:
                self.keys = {}
    
    def save(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_api_key(self) -> str:
        return f"jai_{secrets.token_urlsafe(32)}"
    
    def create_key(self, name: str, limits: Dict, features: Dict, user_id: str = None) -> Dict:
        api_key = self.generate_api_key()
        key_id = hashlib.md5(api_key.encode()).hexdigest()[:8]
        
        self.keys[api_key] = {
            'key_id': key_id,
            'name': name,
            'user_id': user_id or f"user_{key_id}",
            'created_at': datetime.now().isoformat(),
            'limits': limits,
            'features': features,
            'usage': {
                'total_requests': 0,
                'daily_requests': 0,
                'monthly_requests': 0,
                'last_reset': datetime.now().isoformat(),
                'feature_usage': {},
                'last_requests': []
            },
            'active': True
        }
        self.save()
        
        return {
            'api_key': api_key,
            'key_id': key_id,
            'limits': limits,
            'features': features
        }
    
    def has_feature_access(self, api_key: str, feature: str) -> bool:
        if api_key not in self.keys:
            return False
        features = self.keys[api_key].get('features', {})
        if feature in features:
            return features[feature].get('enabled', False)
        return False
    
    def get_feature_limits(self, api_key: str, feature: str) -> Dict:
        if api_key not in self.keys:
            return {}
        features = self.keys[api_key].get('features', {})
        if feature in features:
            return features[feature].get('limits', {})
        return {}
    
    def track_feature_usage(self, api_key: str, feature: str):
        if api_key in self.keys:
            if 'feature_usage' not in self.keys[api_key]['usage']:
                self.keys[api_key]['usage']['feature_usage'] = {}
            if feature not in self.keys[api_key]['usage']['feature_usage']:
                self.keys[api_key]['usage']['feature_usage'][feature] = 0
            self.keys[api_key]['usage']['feature_usage'][feature] += 1
            self.save()
    
    def validate_key(self, api_key: str) -> Optional[Dict]:
        if api_key not in self.keys:
            return None
        
        key_data = self.keys[api_key]
        
        if not key_data['active']:
            return {'error': 'API key is deactivated'}
        
        # Reset daily counters
        last_reset = datetime.fromisoformat(key_data['usage']['last_reset'])
        now = datetime.now()
        
        if now.date() > last_reset.date():
            key_data['usage']['daily_requests'] = 0
            key_data['usage']['last_reset'] = now.isoformat()
        
        # Check limits
        limits = key_data['limits']
        
        if 'daily' in limits and key_data['usage']['daily_requests'] >= limits['daily']:
            return {'error': f"Daily limit of {limits['daily']} requests exceeded"}
        
        if 'monthly' in limits and key_data['usage']['monthly_requests'] >= limits['monthly']:
            return {'error': f"Monthly limit of {limits['monthly']} requests exceeded"}
        
        if 'total' in limits and key_data['usage']['total_requests'] >= limits['total']:
            return {'error': f"Total limit of {limits['total']} requests exceeded"}
        
        # Rate limiting
        if 'rate_per_minute' in limits:
            minute_ago = now - timedelta(minutes=1)
            key_data['usage']['last_requests'] = [
                ts for ts in key_data['usage']['last_requests']
                if datetime.fromisoformat(ts) > minute_ago
            ]
            
            if len(key_data['usage']['last_requests']) >= limits['rate_per_minute']:
                return {'error': f"Rate limit of {limits['rate_per_minute']} requests per minute exceeded"}
        
        return {'valid': True, 'key_data': key_data}
    
    def increment_usage(self, api_key: str, feature: str = None):
        if api_key in self.keys:
            self.keys[api_key]['usage']['total_requests'] += 1
            self.keys[api_key]['usage']['daily_requests'] += 1
            self.keys[api_key]['usage']['monthly_requests'] += 1
            
            self.keys[api_key]['usage']['last_requests'].append(datetime.now().isoformat())
            
            if feature:
                self.track_feature_usage(api_key, feature)
            
            self.save()
    
    def revoke_key(self, api_key: str) -> bool:
        if api_key in self.keys:
            self.keys[api_key]['active'] = False
            self.save()
            return True
        return False
    
    def get_key_info(self, api_key: str) -> Optional[Dict]:
        if api_key in self.keys:
            info = self.keys[api_key].copy()
            info.pop('api_key', None)
            return info
        return None
    
    def list_keys(self) -> List[Dict]:
        return [
            {
                'key_id': data['key_id'],
                'name': data['name'],
                'user_id': data['user_id'],
                'created_at': data['created_at'],
                'limits': data['limits'],
                'features': data.get('features', {}),
                'usage': data['usage'],
                'active': data['active']
            }
            for key, data in self.keys.items()
        ]

db = APIKeyDatabase(DB_FILE)

# ============= OTP AND SESSION MANAGEMENT =============

# Store active admin sessions
active_sessions = {}  # session_token -> {admin_key, expiry, created_at}

# Store OTP secrets for admins
admin_otp_secrets = {}  # admin_key -> {secret, recovery_codes, created_at}

# Audit log
audit_log = []

def add_audit_log(action: str, admin_key: str, details: str, status: str):
    """Add entry to audit log"""
    audit_log.append({
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'admin_key': admin_key[:20] + '...',  # Partial key only
        'details': details,
        'status': status,
        'ip': request.remote_addr if request else 'unknown'
    })
    # Keep last 1000 logs
    while len(audit_log) > 1000:
        audit_log.pop(0)

def setup_admin_otp(admin_key: str) -> Dict:
    """Setup OTP for an admin - returns OTP secret and recovery codes"""
    otp_secret = pyotp.random_base32()
    recovery_codes = [secrets.token_hex(4) for _ in range(10)]  # 10 recovery codes
    
    admin_otp_secrets[admin_key] = {
        'secret': otp_secret,
        'recovery_codes': recovery_codes.copy(),
        'created_at': datetime.now().isoformat(),
        'hotp_counter': 0,
        'last_used': None
    }
    
    totp = pyotp.TOTP(otp_secret)
    provisioning_uri = totp.provisioning_uri(name=admin_key[:10], issuer_name="JaiAI")
    
    return {
        'secret': otp_secret,
        'recovery_codes': recovery_codes,
        'provisioning_uri': provisioning_uri,
        'qr_code_data': f"otpauth://totp/JaiAI:{admin_key[:10]}?secret={otp_secret}&issuer=JaiAI"
    }

def verify_otp(admin_key: str, otp_code: str) -> bool:
    """
    Verify OTP code for admin
    Supports TOTP, HOTP, and recovery codes
    """
    # Check if admin exists
    if admin_key not in admin_otp_secrets:
        # Auto-setup for new admins
        setup = setup_admin_otp(admin_key)
        print(f"\n⚠️ NEW ADMIN OTP SETUP REQUIRED for key: {admin_key[:20]}...")
        print(f"   Secret: {setup['secret']}")
        print(f"   Recovery codes: {', '.join(setup['recovery_codes'])}")
        print(f"   Add to authenticator app: {setup['provisioning_uri']}\n")
        return False
    
    otp_data = admin_otp_secrets[admin_key]
    secret = otp_data['secret']
    
    # Method 1: TOTP (30-second window)
    totp = pyotp.TOTP(secret, interval=30)
    if totp.verify(otp_code, valid_window=1):
        otp_data['last_used'] = datetime.now().isoformat()
        add_audit_log('OTP_VERIFY', admin_key, 'TOTP verification successful', 'success')
        return True
    
    # Method 2: HOTP (counter-based backup)
    hotp = pyotp.HOTP(secret)
    for offset in range(10):
        if hotp.verify(otp_code, otp_data.get('hotp_counter', 0) + offset):
            otp_data['hotp_counter'] = otp_data.get('hotp_counter', 0) + offset + 1
            otp_data['last_used'] = datetime.now().isoformat()
            add_audit_log('OTP_VERIFY', admin_key, 'HOTP verification successful', 'success')
            return True
    
    # Method 3: Recovery codes (one-time use)
    recovery_codes = otp_data.get('recovery_codes', [])
    if otp_code in recovery_codes:
        recovery_codes.remove(otp_code)
        otp_data['recovery_codes'] = recovery_codes
        otp_data['last_used'] = datetime.now().isoformat()
        add_audit_log('OTP_VERIFY', admin_key, 'Recovery code used', 'warning')
        return True
    
    add_audit_log('OTP_VERIFY', admin_key, f'Failed OTP attempt: {otp_code}', 'failure')
    return False

def verify_admin_session():
    """Verify admin session from request headers"""
    session_token = request.headers.get('X-Session-Token')
    request_signature = request.headers.get('X-Request-Signature')
    timestamp = request.headers.get('X-Request-Timestamp')
    nonce = request.headers.get('X-Request-Nonce')
    
    if not session_token or session_token not in active_sessions:
        return None
    
    session = active_sessions[session_token]
    if datetime.now() > session['expiry']:
        del active_sessions[session_token]
        return None
    
    # Verify timestamp (prevent replay attacks)
    try:
        req_time = datetime.fromtimestamp(int(timestamp) / 1000)
        if abs(datetime.now() - req_time) > timedelta(seconds=30):
            return None
    except:
        return None
    
    # Verify request signature
    if request_signature:
        data_to_sign = f"{request.method}|{request.path}|{timestamp}|{nonce}|{json.dumps(request.json or {})}|{session_token}"
        expected = hashlib.sha256(data_to_sign.encode()).hexdigest()
        
        if not hmac.compare_digest(request_signature, expected):
            return None
    
    return session['admin_key']

def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_key = verify_admin_session()
        
        if not admin_key:
            return jsonify({'error': 'Unauthorized. Invalid or expired session.'}), 401
        
        # Check if admin key has admin privileges
        key_info = db.get_key_info(admin_key)
        if not key_info or not key_info.get('limits', {}).get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        request.admin_key = admin_key
        return f(*args, **kwargs)
    return decorated_function

def require_api_key(f):
    """Decorator to require API key for public endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Missing API key. Please provide X-API-Key header'}), 401
        
        validation = db.validate_key(api_key)
        
        if 'error' in validation:
            return jsonify({'error': validation['error']}), 429 if 'limit' in validation['error'] else 401
        
        request.key_data = validation['key_data']
        request.api_key = api_key
        
        db.increment_usage(api_key)
        
        return f(*args, **kwargs)
    return decorated_function

def require_feature(feature_name):
    """Decorator to require specific feature access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not db.has_feature_access(api_key, feature_name):
            return jsonify({
                'error': f'Feature "{feature_name}" is not available for your tier',
                'upgrade_message': 'Please upgrade to access this feature',
                'feature': feature_name
            }), 403
        
        db.track_feature_usage(api_key, feature_name)
        
        return f(*args, **kwargs)
    return decorated_function

# ============= TIER DEFINITIONS =============

TIERS = {
    'free': {
        'name': 'Free Tier',
        'limits': {
            'daily': 100,
            'monthly': 2000,
            'rate_per_minute': 2,
            'total': None,
            'is_admin': False
        },
        'features': {
            'chat': {'enabled': True, 'limits': {'max_message_length': 500, 'context_messages': 5}},
            'memory_short_term': {'enabled': True, 'limits': {'retention_days': 7, 'max_memories': 50}},
            'context_persistence': {'enabled': True, 'limits': {'max_contexts': 3, 'expiry_hours': 24}},
            'document_upload': {'enabled': False, 'limits': None},
            'document_search': {'enabled': False, 'limits': None},
            'memory_long_term': {'enabled': False, 'limits': None},
            'conversation_export': {'enabled': False, 'limits': None}
        },
        'description': 'Basic chat only. 2 requests per minute.'
    },
    'pro': {
        'name': 'Pro Tier',
        'limits': {
            'daily': 5000,
            'monthly': 100000,
            'rate_per_minute': 50,
            'total': None,
            'is_admin': False
        },
        'features': {
            'chat': {'enabled': True, 'limits': {'max_message_length': 5000, 'context_messages': 50}},
            'memory_short_term': {'enabled': True, 'limits': {'retention_days': 30, 'max_memories': 1000}},
            'context_persistence': {'enabled': True, 'limits': {'max_contexts': 50, 'expiry_hours': 720}},
            'document_upload': {'enabled': True, 'limits': {'max_file_size_mb': 10, 'max_files': 100}},
            'document_search': {'enabled': True, 'limits': {'searches_per_day': 500}},
            'memory_long_term': {'enabled': True, 'limits': {'retention_years': 1, 'max_memories': 10000}},
            'conversation_export': {'enabled': True, 'limits': {'exports_per_day': 10}}
        },
        'description': 'Full features including documents and long-term memory.'
    },
    'enterprise': {
        'name': 'Enterprise Tier',
        'limits': {
            'daily': None,
            'monthly': None,
            'rate_per_minute': 200,
            'total': 1000000,
            'is_admin': False
        },
        'features': {
            'chat': {'enabled': True, 'limits': {'max_message_length': 50000, 'context_messages': 500}},
            'memory_short_term': {'enabled': True, 'limits': {'retention_days': 90, 'max_memories': 50000}},
            'context_persistence': {'enabled': True, 'limits': {'max_contexts': 1000, 'expiry_hours': 8760}},
            'document_upload': {'enabled': True, 'limits': {'max_file_size_mb': 100, 'max_files': 10000}},
            'document_search': {'enabled': True, 'limits': {'searches_per_day': 50000}},
            'memory_long_term': {'enabled': True, 'limits': {'retention_years': 10, 'max_memories': 1000000}},
            'conversation_export': {'enabled': True, 'limits': {'exports_per_day': 1000}}
        },
        'description': 'Unlimited everything with enterprise SLA.'
    }
}

# ============= SERVICE ROUTER =============

class ServiceRouter:
    def route_to_chat(self, message: str, context_id: str, user_id: str, feature_limits: dict):
        max_length = feature_limits.get('chat', {}).get('limits', {}).get('max_message_length', 500)
        if len(message) > max_length:
            raise ValueError(f"Message exceeds {max_length} characters limit")
        
        try:
            response = requests.post(
                f"{SERVICES['chat']}/generate",
                json={'message': message, 'context_id': context_id, 'user_id': user_id},
                timeout=10
            )
            return response.json()
        except:
            return {'reply': f"Jai heard: '{message}'. Chat service connecting..."}
    
    def route_to_document(self, action: str, **kwargs):
        try:
            response = requests.post(
                f"{SERVICES['document']}/{action}",
                json=kwargs,
                timeout=30
            )
            return response.json()
        except:
            return {'error': 'Document service unavailable'}

router = ServiceRouter()

# ============= ADMIN ENDPOINTS =============

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Secure admin login with OTP"""
    data = request.json
    admin_key = request.headers.get('X-API-Key')
    otp = data.get('otp')
    session_token = data.get('session_token')
    timestamp = data.get('timestamp')
    signature = data.get('signature')
    
    # Verify admin key exists
    key_info = db.get_key_info(admin_key)
    if not key_info or not key_info.get('limits', {}).get('is_admin', False):
        add_audit_log('LOGIN_ATTEMPT', admin_key or 'unknown', 'Invalid admin key', 'failure')
        return jsonify({'error': 'Invalid admin credentials'}), 401
    
    # Verify timestamp
    if abs(datetime.now().timestamp() - (timestamp / 1000)) > 30:
        return jsonify({'error': 'Request expired'}), 401
    
    # Verify signature
    expected = hashlib.sha256(
        f"{json.dumps({'otp':otp, 'session_token':session_token, 'timestamp':timestamp})}{admin_key}".encode()
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        add_audit_log('LOGIN_ATTEMPT', admin_key, 'Invalid signature', 'failure')
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Verify OTP
    if not verify_otp(admin_key, otp):
        add_audit_log('LOGIN_ATTEMPT', admin_key, 'Invalid OTP', 'failure')
        return jsonify({'error': 'Invalid OTP code'}), 401
    
    # Create session
    active_sessions[session_token] = {
        'admin_key': admin_key,
        'expiry': datetime.now() + timedelta(hours=1),
        'created_at': datetime.now()
    }
    
    add_audit_log('LOGIN', admin_key, 'Successful admin login', 'success')
    return jsonify({'success': True, 'session_token': session_token, 'expires_in': 3600})

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session_token = request.headers.get('X-Session-Token')
    if session_token in active_sessions:
        admin_key = active_sessions[session_token]['admin_key']
        del active_sessions[session_token]
        add_audit_log('LOGOUT', admin_key, 'Admin logout', 'success')
    return jsonify({'success': True})

@app.route('/admin/keys/create', methods=['POST'])
@require_admin
def admin_create_key():
    data = request.json
    tier = data.get('tier', 'free')
    name = data.get('name')
    user_id = data.get('user_id')
    custom_features = data.get('features')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    if tier not in TIERS and tier != 'custom':
        return jsonify({'error': f'Invalid tier. Available: {list(TIERS.keys())}'}), 400
    
    if tier == 'custom':
        limits = {
            'daily': data.get('daily_limit'),
            'monthly': data.get('monthly_limit'),
            'rate_per_minute': data.get('rate_limit', 10),
            'is_admin': data.get('is_admin', False)
        }
        features = custom_features or TIERS['pro']['features']
    else:
        limits = TIERS[tier]['limits'].copy()
        features = TIERS[tier]['features'].copy()
    
    new_key = db.create_key(name, limits, features, user_id)
    
    add_audit_log('CREATE_KEY', request.admin_key, f'Created key for {name} ({tier} tier)', 'success')
    
    return jsonify({
        'success': True,
        'api_key': new_key['api_key'],
        'key_id': new_key['key_id'],
        'tier': tier,
        'limits': limits,
        'features': features,
        'warning': '⚠️ Save this API key now! It will not be shown again.'
    })

@app.route('/admin/keys/revoke', methods=['POST'])
@require_admin
def admin_revoke_key():
    data = request.json
    key_id = data.get('key_id')
    api_key = data.get('api_key')
    
    # Find key by key_id or api_key
    found = None
    for key, info in db.keys.items():
        if info['key_id'] == key_id or key == api_key:
            found = key
            break
    
    if not found:
        return jsonify({'error': 'Key not found'}), 404
    
    db.revoke_key(found)
    add_audit_log('REVOKE_KEY', request.admin_key, f'Revoked key: {key_id}', 'success')
    
    return jsonify({'success': True})

@app.route('/admin/keys/list', methods=['GET'])
@require_admin
def admin_list_keys():
    keys = db.list_keys()
    return jsonify({'keys': keys, 'total': len(keys)})

@app.route('/admin/otp/setup', methods=['GET'])
@require_admin
def admin_otp_setup():
    """Get OTP setup information for admin"""
    admin_key = request.admin_key
    otp_data = admin_otp_secrets.get(admin_key)
    
    if not otp_data:
        setup = setup_admin_otp(admin_key)
        otp_data = admin_otp_secrets[admin_key]
    
    return jsonify({
        'secret': otp_data['secret'],
        'recovery_codes': otp_data['recovery_codes'],
        'provisioning_uri': f"otpauth://totp/JaiAI:{admin_key[:10]}?secret={otp_data['secret']}&issuer=JaiAI"
    })

@app.route('/admin/audit/log', methods=['GET'])
@require_admin
def admin_audit_log():
    return jsonify({'logs': audit_log[-100:]})  # Last 100 logs

# ============= PUBLIC ENDPOINTS =============

@app.route('/api/chat', methods=['POST'])
@require_api_key
@require_feature('chat')
def chat():
    data = request.json
    user_id = data.get('user_id') or request.key_data['user_id']
    context_id = data.get('context_id', 'default')
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        result = router.route_to_chat(message, context_id, user_id, request.key_data.get('features', {}))
        
        # Add tier info
        result['tier_info'] = {
            'name': 'free' if request.key_data['limits'].get('rate_per_minute') == 2 else 'pro',
            'features_available': [k for k, v in request.key_data.get('features', {}).items() if v.get('enabled')],
            'rate_limit': f"{request.key_data['limits'].get('rate_per_minute', 'unlimited')} req/min"
        }
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/upload', methods=['POST'])
@require_api_key
@require_feature('document_upload')
def upload_document():
    try:
        result = router.route_to_document('upload', **request.json)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/search', methods=['POST'])
@require_api_key
@require_feature('document_search')
def search_document():
    try:
        result = router.route_to_document('search', **request.json)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'services': SERVICES,
        'auth_required': True,
        'version': '2.0.0'
    })

@app.route('/', methods=['GET'])
def info():
    return jsonify({
        'name': 'Jai - Joshua\'s Artificial Intelligence',
        'version': '2.0.0',
        'auth_required': True,
        'tiers': ['free', 'pro', 'enterprise'],
        'endpoints': {
            'chat': '/api/chat (POST) - Requires API key',
            'document_upload': '/api/document/upload (POST) - Pro/Enterprise only',
            'document_search': '/api/document/search (POST) - Pro/Enterprise only',
            'health': '/health (GET) - Public'
        }
    })

# ============= INITIALIZATION =============

if __name__ == '__main__':
    # Create initial admin key if none exists
    admin_keys = [k for k, v in db.keys.items() if v.get('limits', {}).get('is_admin')]
    
    if not admin_keys:
        admin_key = db.create_key(
            name="Master Admin",
            limits={'daily': None, 'monthly': None, 'rate_per_minute': 500, 'is_admin': True},
            features={k: {'enabled': True} for k in TIERS['enterprise']['features'].keys()},
            user_id="admin"
        )
        
        # Setup OTP for admin
        otp_setup = setup_admin_otp(admin_key['api_key'])
        
        print("\n" + "="*70)
        print("⚠️  JAI ADMIN SETUP - SAVE THESE CREDENTIALS!")
        print("="*70)
        print(f"\n🔑 ADMIN API KEY: {admin_key['api_key']}")
        print(f"\n🔐 OTP SECRET: {otp_setup['secret']}")
        print(f"\n📱 RECOVERY CODES (save these!):")
        for code in otp_setup['recovery_codes']:
            print(f"   - {code}")
        print(f"\n📲 Scan this QR code in Google Authenticator:")
        print(f"   {otp_setup['provisioning_uri']}")
        print("\n" + "="*70)
        print("⚠️  You will need BOTH the Admin API Key AND OTP to login!")
        print("="*70 + "\n")
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)