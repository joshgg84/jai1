"""JAI1 - Intelligence Service
Main API Gateway for all JAI microservices
"""

import os
import logging
import base64
import io
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from gtts import gTTS

from jai_core import JAIPersonality
from jai_nlp import JAINLP
from jai_currency import JAICurrency
from jai_memory import JAIMemory, setup_database

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-Admin-Key')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_KEY = os.getenv('ADMIN_KEY', 'jai_admin_key_2025')
PORT = int(os.getenv('PORT', 5001))


class JAI:
    @staticmethod
    def text_to_speech(text):
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return base64.b64encode(audio_buffer.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    @staticmethod
    def generate_response(message, client_id="unknown", options=None):
        options = options or {}
        include_speech = options.get('speech', False)
        
        personality_response = JAIPersonality.get_response(
            message, 
            lesson_content="", 
            lesson_title="No lesson",
            client_id=client_id
        )
        
        JAIMemory.save_conversation(client_id, message, personality_response)
        
        response = {"response": personality_response, "type": "personality", "source": "jai_core"}
        if include_speech:
            response["audio"] = JAI.text_to_speech(personality_response)
        return response


@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def api_chat():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.json
    message = data.get('message', '').strip()
    client_id = data.get('clientId', 'unknown')
    options = data.get('options', {})
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    result = JAI.generate_response(message, client_id, options)
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI',
        'creator': 'Joshua Giwa',
        'village': 'Yukuben, Nigeria',
        'services': {
            'document': os.environ.get('DOCUMENT_SERVER_URL', 'not configured'),
            'casual': os.environ.get('CASUAL_SERVER_URL', 'not configured'),
            'data': os.environ.get('DATA_ANALYZER_URL', 'not configured')
        }
    })


if __name__ == '__main__':
    setup_database()
    logger.info("🗣️ JAI starting with microservices architecture...")
    app.run(host='0.0.0.0', port=PORT, debug=False)