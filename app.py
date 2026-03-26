"""JAI1 - Intelligence Service
Handles all NLP, AI responses, learning, and lesson storage.
API endpoint for JAI2 to consume.
"""

import os
import sqlite3
import logging
import base64
import io
from flask import Flask, request, jsonify, send_file, session, redirect
from flask_cors import CORS
import PyPDF2
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
from gtts import gTTS

# Import JAI's personality and NLP
from jai_responses import JAIPersonality
from jai_nlp import JAINLP
from jai_advanced_nlp import JAIAdvancedNLP

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key_here')
CORS(app)  # Allow JAI2 to call this API

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
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
    
    # Lessons table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT,
            content TEXT NOT NULL,
            pages INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 0,
            uploaded_by TEXT
        )
    ''')
    
    # Bot taught responses (Q&A)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            response TEXT NOT NULL,
            approved INTEGER DEFAULT 1,
            times_used INTEGER DEFAULT 0,
            teaching_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP
        )
    ''')
    
    # Teaching suggestions
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teaching_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            message TEXT,
            suggested_response TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ JAI1 Database ready")

# ========== CURRENT LESSON ==========

current_lesson_id = None
current_lesson_content = ""
current_lesson_title = "No lesson uploaded"

def load_current_lesson():
    global current_lesson_id, current_lesson_content, current_lesson_title
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, title, content FROM lessons WHERE is_active = 1 ORDER BY uploaded_at DESC LIMIT 1')
    lesson = cur.fetchone()
    if lesson:
        current_lesson_id = lesson['id']
        current_lesson_content = lesson['content']
        current_lesson_title = lesson['title']
        logger.info(f"📚 Active lesson: {current_lesson_title}")
    else:
        current_lesson_id = None
        current_lesson_content = ""
        current_lesson_title = "No lesson uploaded"
    conn.close()

# ========== AUTH ==========

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login-page')
        return f(*args, **kwargs)
    return decorated

# ========== JAI INTELLIGENCE ==========

class JAI:
    @staticmethod
    def get_taught_response(message):
        """Check if this question has been taught before"""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                SELECT response, times_used FROM bot 
                WHERE text LIKE ? AND approved = 1 
                ORDER BY times_used ASC LIMIT 1
            ''', (f'%{message}%',))
            result = cur.fetchone()
            
            if result:
                # Update usage count
                cur.execute('''
                    UPDATE bot SET times_used = times_used + 1, last_used = CURRENT_TIMESTAMP 
                    WHERE text LIKE ?
                ''', (f'%{message}%',))
                conn.commit()
                conn.close()
                return result['response']
            conn.close()
        except Exception as e:
            logger.error(f"DB error in get_taught_response: {e}")
        return None
    
    @staticmethod
    def save_teaching_suggestion(user_id, message, response):
        """Save a teaching suggestion for admin review"""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO teaching_suggestions (user_id, message, suggested_response, created_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message[:500], response[:500], datetime.now()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"DB error saving suggestion: {e}")
            return False
    
    @staticmethod
    def generate_response(user_message, user_id="anonymous"):
        """Generate intelligent response"""
        # FIRST: Check if this question has been taught before
        taught_response = JAI.get_taught_response(user_message)
        if taught_response:
            logger.info(f"📚 Used taught response for: {user_message[:50]}")
            return {"response": taught_response, "type": "taught", "lesson": current_lesson_title}
        
        # SECOND: Use NLP to analyze message
        analysis = JAINLP.analyze_sentence(user_message)
        
        # THIRD: Get response from personality file
        response = JAIPersonality.get_response(user_message, current_lesson_content, current_lesson_title)
        
        return {"response": response, "type": "generated", "lesson": current_lesson_title, "analysis": analysis}

# ========== TEXT-TO-SPEECH ==========

@app.route('/speak', methods=['POST'])
def speak():
    """Convert text to speech and return audio"""
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        return jsonify({'success': True, 'audio': audio_base64, 'text': text[:500]})
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({'error': str(e)}), 500

# ========== API ENDPOINTS (For JAI2) ==========

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Main API endpoint for JAI2 to call"""
    data = request.json
    message = data.get('message', '').strip()
    user_id = data.get('userId', 'anonymous')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    result = JAI.generate_response(message, user_id)
    return jsonify({
        'response': result['response'],
        'type': result['type'],
        'lesson': result['lesson']
    })

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """Analyze text using NLP"""
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text required'}), 400
    
    analysis = JAINLP.analyze_sentence(text)
    advanced = JAIAdvancedNLP.full_analysis(text)
    
    return jsonify({
        'analysis': analysis,
        'advanced': advanced
    })

@app.route('/api/lesson', methods=['GET'])
def api_lesson():
    """Get current lesson"""
    return jsonify({
        'title': current_lesson_title,
        'loaded': current_lesson_id is not None,
        'content_preview': current_lesson_content[:500] if current_lesson_content else None
    })

# ========== ADMIN ROUTES ==========

@app.route('/admin/login-page')
def admin_login_page():
    return send_file('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return redirect('/admin')
    return '''
        <script>
            alert("Wrong password!");
            window.location.href = "/admin/login-page";
        </script>
    '''

@app.route('/admin')
@login_required
def admin_panel():
    return send_file('admin.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/')

@app.route('/admin/upload', methods=['POST'])
@login_required
def admin_upload():
    global current_lesson_id, current_lesson_content, current_lesson_title
    
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file'}), 400
    
    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
        
        title = pdf_file.filename.replace('.pdf', '')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE lessons SET is_active = 0")
        cur.execute('''
            INSERT INTO lessons (title, filename, content, pages, is_active, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
        ''', (title, pdf_file.filename, extracted_text, len(pdf_reader.pages), 'admin', datetime.now()))
        conn.commit()
        conn.close()
        
        load_current_lesson()
        
        return jsonify({'success': True, 'message': f'✅ Lesson "{title}" uploaded!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/lessons', methods=['GET'])
@login_required
def list_lessons():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, title, pages, uploaded_at, is_active FROM lessons ORDER BY uploaded_at DESC')
    lessons = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(lessons)

@app.route('/admin/switch/<int:lesson_id>', methods=['POST'])
@login_required
def switch_lesson(lesson_id):
    global current_lesson_id, current_lesson_content, current_lesson_title
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE lessons SET is_active = 0")
    cur.execute("UPDATE lessons SET is_active = 1 WHERE id = ?", (lesson_id,))
    conn.commit()
    conn.close()
    load_current_lesson()
    return jsonify({'success': True, 'lesson': current_lesson_title})

@app.route('/admin/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM lessons")
    total_lessons = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bot WHERE approved = 1")
    total_taught = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM teaching_suggestions WHERE status = 'pending'")
    pending_suggestions = cur.fetchone()[0]
    conn.close()
    return jsonify({
        'total_lessons': total_lessons,
        'total_taught': total_taught,
        'pending_suggestions': pending_suggestions,
        'current_lesson': current_lesson_title
    })

@app.route('/admin/learn', methods=['GET'])
@login_required
def learning_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, message, suggested_response, created_at 
        FROM teaching_suggestions 
        WHERE status = 'pending' 
        ORDER BY created_at DESC
    """)
    pending = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({'pending': pending})

@app.route('/admin/learn/approve/<int:suggestion_id>', methods=['POST'])
@login_required
def approve_learning(suggestion_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT message, suggested_response FROM teaching_suggestions WHERE id = ?", (suggestion_id,))
    suggestion = cur.fetchone()
    
    if suggestion:
        cur.execute("""
            INSERT INTO bot (text, response, approved, times_used, teaching_date)
            VALUES (?, ?, 1, 0, CURRENT_TIMESTAMP)
        """, (suggestion['message'], suggestion['suggested_response']))
        cur.execute("UPDATE teaching_suggestions SET status = 'approved' WHERE id = ?", (suggestion_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Learning approved!'})
    
    conn.close()
    return jsonify({'error': 'Suggestion not found'}), 404

@app.route('/admin/learn/reject/<int:suggestion_id>', methods=['POST'])
@login_required
def reject_learning(suggestion_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE teaching_suggestions SET status = 'rejected' WHERE id = ?", (suggestion_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Suggestion rejected'})

@app.route('/admin/learn/add', methods=['POST'])
@login_required
def add_qa():
    data = request.json
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip()
    
    if not question or not answer:
        return jsonify({'error': 'Question and answer required'}), 400
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bot (text, response, approved, times_used, teaching_date)
        VALUES (?, ?, 1, 0, CURRENT_TIMESTAMP)
    """, (question, answer))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Q&A added!'})

@app.route('/teach', methods=['POST'])
def teach():
    """Submit teaching suggestion from users"""
    data = request.json
    message = data.get('message', '').strip()
    suggested_response = data.get('response', '').strip()
    user_id = data.get('userId', 'anonymous')
    
    if not message or not suggested_response:
        return jsonify({'error': 'Message and response required'}), 400
    
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO teaching_suggestions (user_id, message, suggested_response, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message[:500], suggested_response[:500], datetime.now()))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Thank you! JAI will learn from your suggestion.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'name': 'JAI1 - Intelligence Service',
        'creator': 'Joshua Giwa',
        'village': 'Yukuben, Nigeria',
        'lesson_loaded': current_lesson_id is not None,
        'lesson': current_lesson_title,
        'taught_responses': True
    })

# ========== INITIALIZATION ==========

setup_database()
load_current_lesson()

if __name__ == '__main__':
    logger.info("🧠 JAI1 - Intelligence Service starting...")
    logger.info(f"📍 Creator: Joshua Giwa from Yukuben, Nigeria")
    logger.info(f"📚 Current lesson: {current_lesson_title}")
    logger.info(f"🚀 API server running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)