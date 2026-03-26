"""JAI1 - Pure Intelligence Service
Simplified: Only /api/chat and /health endpoints.
Everything else is handled by the main endpoint.
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

# Import JAI's personality (it imports everything else)
from jai_responses import JAIPersonality
from jai_nlp import JAINLP

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

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'jai_intelligence.db')

# ========== DATABASE ==========

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS taught (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            trigger TEXT NOT NULL,
            response TEXT NOT NULL,
            times_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            trigger TEXT,
            suggested_response TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ JAI1 Database ready")

# ========== CORE INTELLIGENCE ==========

class JAI:
    
    @staticmethod
    def calculate(expr):
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            result = eval(expr)
            return f"🧮 {expr} = {result}"
        except:
            return None
    
    @staticmethod
    def currency_convert(amount, from_curr, to_curr):
        rates = {"USD": 1500, "EUR": 1600, "GBP": 1900, "NGN": 1}
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()
        
        if from_curr in rates and to_curr in rates:
            converted = amount * rates[from_curr] / rates[to_curr]
            return f"💰 {amount:,.2f} {from_curr} = {converted:,.2f} {to_curr}"
        return None
    
    @staticmethod
    def get_taught_response(client_id, trigger):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                SELECT response, times_used FROM taught 
                WHERE client_id = ? AND trigger LIKE ? 
                ORDER BY times_used ASC LIMIT 1
            ''', (client_id, f'%{trigger}%'))
            result = cur.fetchone()
            
            if result:
                cur.execute('''
                    UPDATE taught SET times_used = times_used + 1 
                    WHERE client_id = ? AND trigger LIKE ?
                ''', (client_id, f'%{trigger}%'))
                conn.commit()
                conn.close()
                return result['response']
            conn.close()
        except Exception as e:
            logger.error(f"DB error: {e}")
        return None
    
    @staticmethod
    def save_suggestion(client_id, trigger, response):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO suggestions (client_id, trigger, suggested_response, status)
                VALUES (?, ?, ?, 'pending')
            ''', (client_id, trigger, response))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"DB error: {e}")
            return False
    
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
        """Unified intelligence — returns everything"""
        options = options or {}
        include_speech = options.get('speech', False)
        
        # Step 1: Check taught response
        taught = JAI.get_taught_response(client_id, message)
        if taught:
            response = {
                "response": taught,
                "type": "taught",
                "source": "memory"
            }
            if include_speech:
                response["audio"] = JAI.text_to_speech(taught)
            return response
        
        # Step 2: Check for calculation
        numbers = re.findall(r'\d+', message)
        if len(numbers) >= 2:
            result = JAI.calculate(message)
            if result:
                response = {"response": result, "type": "calculation", "source": "core"}
                if include_speech:
                    response["audio"] = JAI.text_to_speech(result)
                return response
        
        # Step 3: Check for percentage
        percent_match = re.search(r'(\d+)\s*%?\s*(of)?\s*(\d+)', message, re.IGNORECASE)
        if percent_match:
            percent = float(percent_match.group(1))
            number = float(percent_match.group(3))
            result = f"🧮 {percent}% of {number} = {(percent / 100) * number}"
            response = {"response": result, "type": "calculation", "source": "core"}
            if include_speech:
                response["audio"] = JAI.text_to_speech(result)
            return response
        
        # Step 4: Check for currency conversion
        currency_match = re.search(r'(\d+)\s*(usd|dollar|eur|euro|gbp|pound)\s*(to|in)\s*(ngn|naira)', message, re.IGNORECASE)
        if currency_match:
            amount = float(currency_match.group(1))
            from_curr = currency_match.group(2).upper()
            if from_curr == "DOLLAR":
                from_curr = "USD"
            elif from_curr == "EURO":
                from_curr = "EUR"
            elif from_curr == "POUND":
                from_curr = "GBP"
            
            result = JAI.currency_convert(amount, from_curr, "NGN")
            if result:
                response = {"response": result, "type": "currency", "source": "core"}
                if include_speech:
                    response["audio"] = JAI.text_to_speech(result)
                return response
        
        # Step 5: Check for simple number recognition
        what_match = re.search(r'what is (\d+)', message, re.IGNORECASE)
        if what_match:
            number = float(what_match.group(1))
            result = f"🧮 {number} is {number}"
            response = {"response": result, "type": "calculation", "source": "core"}
            if include_speech:
                response["audio"] = JAI.text_to_speech(result)
            return response
        
        # Step 6: Check if it's a teaching suggestion
        teach_match = re.search(r'teach jai.*?:(.*?)answer:(.*?)$', message, re.IGNORECASE | re.DOTALL)
        if not teach_match:
            teach_match = re.search(r'teach.*?:(.*?)answer:(.*?)$', message, re.IGNORECASE | re.DOTALL)
        if teach_match:
            trigger = teach_match.group(1).strip()
            answer = teach_match.group(2).strip()
            success = JAI.save_suggestion(client_id, trigger, answer)
            if success:
                result = "✅ Thanks! I'll learn from this. A human will review and approve it."
            else:
                result = "❌ Sorry, couldn't save your suggestion. Try again."
            response = {"response": result, "type": "teaching", "source": "core"}
            if include_speech:
                response["audio"] = JAI.text_to_speech(result)
            return response
        
        # Step 7: Use JAIPersonality for all conversation
        try:
            personality_response = JAIPersonality.get_response(message, "", "No lesson")
            logger.info(f"JAIPersonality returned: {personality_response[:100] if personality_response else 'None'}")
        except Exception as e:
            logger.error(f"JAIPersonality error: {e}")
            personality_response = None
        
        if personality_response:
            response = {
                "response": personality_response,
                "type": "personality",
                "source": "jai_responses"
            }
            if include_speech:
                response["audio"] = JAI.text_to_speech(personality_response)
            return response
        
        # Step 8: Fallback if JAIPersonality fails
        logger.warning("JAIPersonality returned None, using fallback")
        fallback_responses = [
            "I'm here. What's on your mind?",
            "Tell me what's going on.",
            "What would you like to talk about?"
        ]
        result = random.choice(fallback_responses)
        response = {
            "response": result,
            "type": "fallback",
            "source": "default"
        }
        if include_speech:
            response["audio"] = JAI.text_to_speech(result)
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
    
    try:
        result = JAI.generate_response(message, client_id, options)
        return jsonify(result)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Error in api_chat: {e}")
        logger.error(f"Traceback: {error_detail}")
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI1 - Intelligence Service',
        'creator': 'Joshua Giwa',
        'version': '4.0',
        'features': ['chat', 'calculate', 'currency', 'teaching', 'tts', 'nlp']
    })

@app.route('/admin/db', methods=['GET'])
def admin_download_db():
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return send_file(DB_PATH, as_attachment=True, download_name=f'jai_intelligence_{datetime.now().strftime("%Y%m%d")}.db')

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

# ========== INITIALIZATION ==========

setup_database()

if __name__ == '__main__':
    logger.info("🧠 JAI1 - Intelligence Service starting...")
    logger.info(f"🚀 API server running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)