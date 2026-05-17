import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class APIKeyDatabase:
    def __init__(self, db_file='api_keys.json'):
        self.db_file = db_file
        self.keys = {}
        self.load()
    
    def load(self):
        """Load keys from file"""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                self.keys = json.load(f)
    
    def save(self):
        """Save keys to file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.keys, f, indent=2)
    
    def generate_api_key(self) -> str:
        """Generate a unique API key"""
        return f"jai_{secrets.token_urlsafe(32)}"
    
    def create_key(self, name: str, limits: Dict, user_id: str = None) -> Dict:
        """Create a new API key with limitations"""
        api_key = self.generate_api_key()
        key_id = hashlib.md5(api_key.encode()).hexdigest()[:8]
        
        self.keys[api_key] = {
            'key_id': key_id,
            'name': name,
            'user_id': user_id or f"user_{key_id}",
            'created_at': datetime.now().isoformat(),
            'limits': limits,
            'usage': {
                'total_requests': 0,
                'daily_requests': 0,
                'monthly_requests': 0,
                'last_reset': datetime.now().isoformat()
            },
            'active': True
        }
        self.save()
        
        return {
            'api_key': api_key,
            'key_id': key_id,
            'limits': limits
        }
    
    def validate_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and check limits"""
        if api_key not in self.keys:
            return None
        
        key_data = self.keys[api_key]
        
        if not key_data['active']:
            return {'error': 'API key is deactivated'}
        
        # Check and reset daily counters
        last_reset = datetime.fromisoformat(key_data['usage']['last_reset'])
        now = datetime.now()
        
        if now.date() > last_reset.date():
            key_data['usage']['daily_requests'] = 0
            key_data['usage']['last_reset'] = now.isoformat()
        
        # Check limits
        limits = key_data['limits']
        
        # Daily limit check
        if 'daily' in limits and key_data['usage']['daily_requests'] >= limits['daily']:
            return {'error': f"Daily limit of {limits['daily']} requests exceeded"}
        
        # Monthly limit check
        if 'monthly' in limits and key_data['usage']['monthly_requests'] >= limits['monthly']:
            return {'error': f"Monthly limit of {limits['monthly']} requests exceeded"}
        
        # Total limit check
        if 'total' in limits and key_data['usage']['total_requests'] >= limits['total']:
            return {'error': f"Total limit of {limits['total']} requests exceeded"}
        
        # Rate limit check (requests per minute)
        if 'rate_per_minute' in limits:
            # Simple rate limiting - track last requests
            if 'last_requests' not in key_data['usage']:
                key_data['usage']['last_requests'] = []
            
            # Clean old requests
            minute_ago = now - timedelta(minutes=1)
            key_data['usage']['last_requests'] = [
                ts for ts in key_data['usage']['last_requests'] 
                if datetime.fromisoformat(ts) > minute_ago
            ]
            
            if len(key_data['usage']['last_requests']) >= limits['rate_per_minute']:
                return {'error': f"Rate limit of {limits['rate_per_minute']} requests per minute exceeded"}
        
        return {'valid': True, 'key_data': key_data}
    
    def increment_usage(self, api_key: str):
        """Increment usage counters"""
        if api_key in self.keys:
            self.keys[api_key]['usage']['total_requests'] += 1
            self.keys[api_key]['usage']['daily_requests'] += 1
            self.keys[api_key]['usage']['monthly_requests'] += 1
            
            # Track for rate limiting
            if 'last_requests' not in self.keys[api_key]['usage']:
                self.keys[api_key]['usage']['last_requests'] = []
            self.keys[api_key]['usage']['last_requests'].append(datetime.now().isoformat())
            
            self.save()
    
    def revoke_key(self, api_key: str) -> bool:
        """Revoke/deactivate an API key"""
        if api_key in self.keys:
            self.keys[api_key]['active'] = False
            self.save()
            return True
        return False
    
    def delete_key(self, api_key: str) -> bool:
        """Permanently delete an API key"""
        if api_key in self.keys:
            del self.keys[api_key]
            self.save()
            return True
        return False
    
    def get_key_info(self, api_key: str) -> Optional[Dict]:
        """Get information about an API key"""
        if api_key in self.keys:
            info = self.keys[api_key].copy()
            info.pop('api_key', None)  # Don't return the key itself
            return info
        return None
    
    def list_keys(self) -> List[Dict]:
        """List all API keys (without showing the actual keys)"""
        return [
            {
                'key_id': data['key_id'],
                'name': data['name'],
                'user_id': data['user_id'],
                'created_at': data['created_at'],
                'limits': data['limits'],
                'usage': data['usage'],
                'active': data['active']
            }
            for key, data in self.keys.items()
        ]

# Initialize database
db = APIKeyDatabase()