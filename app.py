"""JAI1 - Pure Intelligence Service
Unified API: One endpoint for all intelligence.
Clients just send messages, JAI1 returns intelligent responses.
"""

import os
import sqlite3
import logging
import base64
import io
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
from gtts import gTTS

# Import NLP modules
from jai_nlp import JAINLP
#from jai_advanced_nlp import JAIAdvancedNLP

app = Flask(__name__)
CORS(app)

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
    
    # Taught responses (Q&A)
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
    
    # Teaching suggestions
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
        """Safe calculator"""
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            result = eval(expr)
            return f"🧮 {expr} = {result}"
        except:
            return None
    
    @staticmethod
    def currency_convert(amount, from_curr, to_curr):
        """Currency conversion"""
        rates = {"USD": 1500, "EUR": 1600, "GBP": 1900, "NGN": 1}
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()
        
        if from_curr in rates and to_curr in rates:
            converted = amount * rates[from_curr] / rates[to_curr]
            return f"💰 {amount:,.2f} {from_curr} = {converted:,.2f} {to_curr}"
        return None
    
    @staticmethod
    def get_taught_response(client_id, trigger):
        """Check if this trigger has been taught"""
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
        """Save a teaching suggestion"""
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
        """Convert text to speech audio"""
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
        calc_match = re.search(r'[\d+\-*/%]', message)
        numbers = re.findall(r'\d+', message)
        if calc_match and len(numbers) >= 2:
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
        
        # Step 7: Default — NLP analysis
        analysis = {
            "sentiment": JAINLP.analyze_sentence(message),
            #"advanced": JAIAdvancedNLP.full_analysis(message),
            "keywords": JAINLP.extract_keywords(message),
            "intent": JAINLP.extract_intent(message)
        }
        
        response = {
            "response": None,
            "type": "needs_processing",
            "source": "nlp",
            "analysis": analysis,
            "message": message
        }
        
        # If client requested speech, generate for the analysis summary
        if include_speech:
            summary = f"I understand you're {analysis['sentiment']['sentiment']['emotion']} about something. What would you like to talk about?"
            response["audio"] = JAI.text_to_speech(summary)
        
        return response

# ========== UNIFIED API ENDPOINT ==========

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """One endpoint for everything"""
    data = request.json
    message = data.get('message', '').strip()
    client_id = data.get('clientId', 'unknown')
    options = data.get('options', {})
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    result = JAI.generate_response(message, client_id, options)
    return jsonify(result)

# ========== ADMIN ENDPOINTS ==========

@app.route('/admin/db', methods=['GET'])
def admin_download_db():
    """Download database backup"""
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return send_file(DB_PATH, as_attachment=True, download_name=f'jai_intelligence_{datetime.now().strftime("%Y%m%d")}.db')

@app.route('/admin/taught', methods=['POST'])
def admin_add_taught():
    """Admin adds taught response"""
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    client_id = data.get('clientId', 'global')
    trigger = data.get('trigger', '').strip()
    response = data.get('response', '').strip()
    
    if not trigger or not response:
        return jsonify({'error': 'Trigger and response required'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO taught (client_id, trigger, response) VALUES (?, ?, ?)', (client_id, trigger, response))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/suggestions', methods=['GET'])
def admin_get_suggestions():
    """Get pending suggestions"""
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM suggestions WHERE status = "pending" ORDER BY created_at DESC')
    suggestions = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(suggestions)

@app.route('/admin/suggestions/<int:suggestion_id>', methods=['POST'])
def admin_approve_suggestion(suggestion_id):
    """Approve a suggestion"""
    auth = request.headers.get('X-Admin-Key')
    if auth != ADMIN_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT client_id, trigger, suggested_response FROM suggestions WHERE id = ?', (suggestion_id,))
    suggestion = cur.fetchone()
    
    if suggestion:
        cur.execute('INSERT INTO taught (client_id, trigger, response) VALUES (?, ?, ?)',
                   (suggestion['client_id'], suggestion['trigger'], suggestion['suggested_response']))
        cur.execute('UPDATE suggestions SET status = "approved" WHERE id = ?', (suggestion_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    conn.close()
    return jsonify({'error': 'Suggestion not found'}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI1 - Intelligence Service',
        'creator': 'Joshua Giwa',
        'version': '3.0',
        'features': ['chat', 'calculate', 'currency', 'teaching', 'tts', 'nlp']
    })

# ========== INITIALIZATION ==========

setup_database()

if __name__ == '__main__':
    logger.info("🧠 JAI1 - Unified Intelligence Service starting...")
    logger.info(f"🚀 API server running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)