import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import os

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
                'request_timestamps': []  # Track timestamps for rate limiting
            },
            'active': True
        }
        self.save()
        return {'api_key': api_key, 'key_id': key_id, 'limits': limits, 'features': features}
    
    def has_feature_access(self, api_key: str, feature: str) -> bool:
        if api_key not in self.keys:
            return False
        return self.keys[api_key].get('features', {}).get(feature, {}).get('enabled', False)
    
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
        
        # Check daily limit
        limits = key_data['limits']
        if limits.get('daily') and key_data['usage']['daily_requests'] >= limits['daily']:
            return {'error': f"Daily limit of {limits['daily']} exceeded"}
        
        # Check rate per minute limit
        if limits.get('rate_per_minute'):
            # Clean old timestamps (older than 1 minute)
            minute_ago = now - timedelta(minutes=1)
            key_data['usage']['request_timestamps'] = [
                ts for ts in key_data['usage']['request_timestamps']
                if datetime.fromisoformat(ts) > minute_ago
            ]
            
            # Check if rate limit exceeded
            if len(key_data['usage']['request_timestamps']) >= limits['rate_per_minute']:
                oldest = min(key_data['usage']['request_timestamps']) if key_data['usage']['request_timestamps'] else now.isoformat()
                wait_seconds = 60 - (now - datetime.fromisoformat(oldest)).seconds
                return {'error': f"Rate limit of {limits['rate_per_minute']} requests per minute exceeded. Wait {wait_seconds} seconds."}
        
        return {'valid': True, 'key_data': key_data}
    
    def increment_usage(self, api_key: str):
        if api_key in self.keys:
            now = datetime.now()
            self.keys[api_key]['usage']['total_requests'] += 1
            self.keys[api_key]['usage']['daily_requests'] += 1
            self.keys[api_key]['usage']['monthly_requests'] += 1
            
            # Add timestamp for rate limiting
            self.keys[api_key]['usage']['request_timestamps'].append(now.isoformat())
            
            # Keep only last 2 minutes of timestamps to save memory
            two_min_ago = now - timedelta(minutes=2)
            self.keys[api_key]['usage']['request_timestamps'] = [
                ts for ts in self.keys[api_key]['usage']['request_timestamps']
                if datetime.fromisoformat(ts) > two_min_ago
            ]
            
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
        return [{'key_id': data['key_id'], 'name': data['name'], 'user_id': data['user_id'], 
                 'created_at': data['created_at'], 'limits': data['limits'], 
                 'features': data.get('features', {}), 'usage': data['usage'], 'active': data['active']} 
                for key, data in self.keys.items()]