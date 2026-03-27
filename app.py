"""JAI1 - Intelligence Service
Powered by OpenAI GPT for true language understanding.
"""

import os
import sqlite3
import logging
import base64
import io
import re
import random
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from gtts import gTTS
import openai

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
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

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
    logger.info("✅ Database ready")

# ========== CORE INTELLIGENCE ==========

class JAI:
    
    @staticmethod
    def calculate(expr):
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            return f"🧮 {expr} = {eval(expr)}"
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
        
        # Step 1: Check taught response
        taught = JAI.get_taught_response(client_id, message)
        if taught:
            response = {"response": taught, "type": "taught", "source": "memory"}
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
        
        # Step 4: Check for currency
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
        
        # Step 5: Use OpenAI GPT
        if OPENAI_API_KEY:
            try:
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """You are JAI (Joshua's Artificial Intelligence), created by Joshua Giwa from Yukuben, Nigeria.

Your personality:
- Warm and encouraging like a big brother
- Use emojis occasionally 😊
- Relate everything to Nigerian context (banking scams, POS fraud, WhatsApp hijacking)
- Talk about life, work, dreams, struggles
- Keep responses concise but meaningful (1-3 sentences usually)
- Be honest and real — no toxic positivity

If asked about yourself: say you were created by Joshua Giwa from Yukuben, Nigeria, and your mission is to be a companion and friend."""},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                gpt_text = response.choices[0].message.content.strip()
                if gpt_text:
                    resp = {"response": gpt_text, "type": "ai", "source": "openai"}
                    if include_speech:
                        resp["audio"] = JAI.text_to_speech(gpt_text)
                    return resp
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
        
        # Step 6: Ultimate fallback
        fallbacks = [
            "I'm here. What's on your mind?",
            "Tell me what's going on.",
            "I'm listening. What would you like to talk about?",
            "What's on your heart today?"
        ]
        result = random.choice(fallbacks)
        response = {"response": result, "type": "fallback", "source": "default"}
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
        logger.error(f"Error in api_chat: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI',
        'creator': 'Joshua Giwa',
        'village': 'Yukuben, Nigeria',
        'openai_configured': bool(OPENAI_API_KEY)
    })

@app.route('/admin/db', methods=['GET'])
def admin_download_db():
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return send_file(DB_PATH, as_attachment=True, download_name=f'jai_intelligence_{datetime.now().strftime("%Y%m%d")}.db')

setup_database()

if __name__ == '__main__':
    logger.info("🧠 JAI - Intelligence Service starting...")
    logger.info(f"🔑 OpenAI: {'configured' if OPENAI_API_KEY else 'MISSING'}")
    logger.info(f"🚀 Server running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)