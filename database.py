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
    
    def create_key(self, name: str, limits: Dict, features: Dict, user_id: str = None) -> Dict:
        """Create a new API key with limitations and features"""
        api_key = self.generate_api_key()
        key_id = hashlib.md5(api_key.encode()).hexdigest()[:8]
        
        self.keys[api_key] = {
            'key_id': key_id,
            'name': name,
            'user_id': user_id or f"user_{key_id}",
            'created_at': datetime.now().isoformat(),
            'limits': limits,
            'features': features,  # New: feature access control
            'usage': {
                'total_requests': 0,
                'daily_requests': 0,
                'monthly_requests': 0,
                'last_reset': datetime.now().isoformat(),
                'feature_usage': {}  # Track which features are used
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
        """Check if API key has access to a specific feature"""
        if api_key not in self.keys:
            return False
        
        key_data = self.keys[api_key]
        features = key_data.get('features', {})
        
        # Check if feature is enabled
        if feature in features:
            return features[feature].get('enabled', False)
        
        return False
    
    def get_feature_limits(self, api_key: str, feature: str) -> Dict:
        """Get specific limits for a feature"""
        if api_key not in self.keys:
            return {}
        
        key_data = self.keys[api_key]
        features = key_data.get('features', {})
        
        if feature in features:
            return features[feature].get('limits', {})
        
        return {}
    
    def track_feature_usage(self, api_key: str, feature: str):
        """Track usage of specific features"""
        if api_key in self.keys:
            if 'feature_usage' not in self.keys[api_key]['usage']:
                self.keys[api_key]['usage']['feature_usage'] = {}
            
            if feature not in self.keys[api_key]['usage']['feature_usage']:
                self.keys[api_key]['usage']['feature_usage'][feature] = 0
            
            self.keys[api_key]['usage']['feature_usage'][feature] += 1
            self.save()
    
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
            if 'last_requests' not in key_data['usage']:
                key_data['usage']['last_requests'] = []
            
            minute_ago = now - timedelta(minutes=1)
            key_data['usage']['last_requests'] = [
                ts for ts in key_data['usage']['last_requests'] 
                if datetime.fromisoformat(ts) > minute_ago
            ]
            
            if len(key_data['usage']['last_requests']) >= limits['rate_per_minute']:
                return {'error': f"Rate limit of {limits['rate_per_minute']} requests per minute exceeded"}
        
        return {'valid': True, 'key_data': key_data}
    
    def increment_usage(self, api_key: str, feature: str = None):
        """Increment usage counters"""
        if api_key in self.keys:
            self.keys[api_key]['usage']['total_requests'] += 1
            self.keys[api_key]['usage']['daily_requests'] += 1
            self.keys[api_key]['usage']['monthly_requests'] += 1
            
            if 'last_requests' not in self.keys[api_key]['usage']:
                self.keys[api_key]['usage']['last_requests'] = []
            self.keys[api_key]['usage']['last_requests'].append(datetime.now().isoformat())
            
            if feature:
                self.track_feature_usage(api_key, feature)
            
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
            info.pop('api_key', None)
            return info
        return None
    
    def list_keys(self) -> List[Dict]:
        """List all API keys"""
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
    
    def get_rate_limit_headers(self, api_key: str) -> Dict:
        """Get rate limit info for response headers"""
        if api_key not in self.keys:
            return {}
        
        key_data = self.keys[api_key]
        limits = key_data['limits']
        usage = key_data['usage']
        
        headers = {
            'X-RateLimit-Limit': str(limits.get('daily', 'unlimited')),
            'X-RateLimit-Remaining': str(limits.get('daily', 0) - usage['daily_requests']) if limits.get('daily') else 'unlimited',
            'X-RateLimit-Used': str(usage['daily_requests']),
            'X-RateLimit-Reset': 'midnight UTC'
        }
        
        if 'rate_per_minute' in limits:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            minute_requests = len([
                ts for ts in usage.get('last_requests', [])
                if datetime.fromisoformat(ts) > minute_ago
            ])
            
            headers['X-RateLimit-PerMinute-Limit'] = str(limits['rate_per_minute'])
            headers['X-RateLimit-PerMinute-Remaining'] = str(limits['rate_per_minute'] - minute_requests)
            headers['X-RateLimit-PerMinute-Used'] = str(minute_requests)
        
        return headers

db = APIKeyDatabase()