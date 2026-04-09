import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "alive",
        "message": "JAI Server is running",
        "version": "minimal"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "jai1"
    })

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        message = data.get('message', '')
        client_id = data.get('clientId', 'unknown')
        
        # Simple response for testing
        return jsonify({
            "response": f"✅ Server is working! Your message: '{message}'",
            "type": "test",
            "client_id": client_id
        })
    except Exception as e:
        return jsonify({
            "response": f"Error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)