"""JAI1 - Intelligence Service
Uses JAI's rule-based personality files.
No lessons — pure conversation with memory, web search, and weather.
"""

import os
import sqlite3
import logging
import base64
import io
import re
import random
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from gtts import gTTS

# Import JAI's personality
from jai_core import JAIPersonality
from jai_nlp import JAINLP
from jai_currency import JAICurrency
from jai_memory import JAIMemory, setup_database
# from jai_image import ImageHandler, ImageCommandHandler  # COMMENTED OUT - pytesseract issue

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

# ========== CONFIGURATION ==========
ADMIN_KEY = os.getenv('ADMIN_KEY', 'jai_admin_key_2025')
PORT = int(os.getenv('PORT', 5001))

# ========== JAI HANDLER ==========
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
        
        # Generate response with memory
        personality_response = JAIPersonality.get_response(
            message, 
            lesson_content="", 
            lesson_title="No lesson",
            client_id=client_id
        )
        
        # Save conversation to memory
        JAIMemory.save_conversation(client_id, message, personality_response)
        
        response = {"response": personality_response, "type": "personality", "source": "jai_core"}
        if include_speech:
            response["audio"] = JAI.text_to_speech(personality_response)
        return response

# ========== API ENDPOINTS ==========

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

@app.route('/api/memory/<client_id>', methods=['GET'])
def get_user_memory(client_id):
    """Get user-specific memory and facts"""
    facts = JAIMemory.get_user_facts(client_id)
    return jsonify({
        'client_id': client_id,
        'facts': facts,
        'message': 'JAI remembers what you teach!'
    })

@app.route('/api/teach', methods=['POST'])
def api_teach():
    """Explicitly teach JAI"""
    data = request.json
    trigger = data.get('trigger', '').strip()
    response = data.get('response', '').strip()
    client_id = data.get('clientId', 'unknown')
    
    if not trigger or not response:
        return jsonify({'error': 'Trigger and response required'}), 400
    
    success, message = JAIMemory.teach_response(client_id, trigger, response)
    return jsonify({'success': success, 'message': message})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI',
        'creator': 'Joshua Giwa',
        'village': 'Yukuben, Nigeria'
    })

@app.route('/admin/db', methods=['GET'])
def admin_download_db():
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    from jai_memory import DB_PATH
    return send_file(DB_PATH, as_attachment=True, download_name=f'jai_intelligence_{datetime.now().strftime("%Y%m%d")}.db')

# Initialize database
setup_database()

if __name__ == '__main__':
    logger.info("🗣️ JAI starting with memory, web search, and weather...")
    app.run(host='0.0.0.0', port=PORT, debug=False)