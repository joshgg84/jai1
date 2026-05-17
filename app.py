from flask import Flask, request, jsonify
import requests
from typing import Dict, Optional
import json
import os

app = Flask(__name__)

# Service URLs (Render will assign these)
SERVICES = {
    'chat': os.getenv('JAI_CHAT_URL', 'http://localhost:8001'),
    'document': os.getenv('JAI_DOCUMENT_URL', 'http://localhost:8002'),
    'memory': os.getenv('JAI_MEMORY_URL', 'http://localhost:8003')
}

class ServiceRouter:
    def __init__(self):
        self.service_health = {name: True for name in SERVICES}
    
    def route_to_chat(self, message: str, context_id: str, user_id: str):
        """Route chat requests with memory context"""
        # First get memory context
        memory_context = self._get_memory(user_id, context_id)
        
        # Send to chat service
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
        
        # Store the interaction in memory
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
    
    def _store_memory(self, user_id: str, context_id: str, 
                      message: str, response: Dict):
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
            pass  # Non-critical, log error

router = ServiceRouter()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint - orchestrates chat + memory"""
    data = request.json
    result = router.route_to_chat(
        message=data.get('message', ''),
        context_id=data.get('context_id', 'default'),
        user_id=data.get('user_id', 'anonymous')
    )
    return jsonify(result)

@app.route('/api/document/upload', methods=['POST'])
def upload_document():
    """Upload document - routes to document service"""
    result = router.route_to_document(
        'upload',
        filename=request.json.get('filename'),
        content=request.json.get('content')
    )
    return jsonify(result)

@app.route('/api/document/search', methods=['POST'])
def search_document():
    """Search document - routes to document service"""
    result = router.route_to_document(
        'search',
        query=request.json.get('query'),
        document_id=request.json.get('document_id')
    )
    return jsonify(result)

@app.route('/api/memory/context', methods=['GET'])
def get_memory_context():
    """Get user's memory context"""
    user_id = request.args.get('user_id')
    context_id = request.args.get('context_id', 'default')
    
    result = router._get_memory(user_id, context_id)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'services': SERVICES})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)