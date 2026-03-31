"""JAI - Memory and Learning Module
Handles database operations, learning from users, and memory management.
"""

import os
import sqlite3
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Database setup
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'jai_intelligence.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Initialize all database tables"""
    conn = get_db()
    cur = conn.cursor()
    
    # Taught responses
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
    
    # Next time say patterns (learning from user suggestions)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS next_time_say (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            trigger_phrase TEXT NOT NULL,
            suggested_response TEXT NOT NULL,
            context TEXT,
            times_suggested INTEGER DEFAULT 1,
            times_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User facts (personal information)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            fact_key TEXT NOT NULL,
            fact_value TEXT NOT NULL,
            confidence REAL DEFAULT 1.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_id, fact_key)
        )
    ''')
    
    # Conversation history
    cur.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            user_message TEXT NOT NULL,
            jai_response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Memory database ready")

class JAIMemory:
    """Memory and learning manager for JAI"""
    
    @staticmethod
    def get_taught_response(client_id, trigger):
        """Get a taught response from memory"""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                SELECT response, times_used FROM taught 
                WHERE client_id = ? AND (trigger = ? OR ? LIKE '%' || trigger || '%')
                ORDER BY times_used ASC LIMIT 1
            ''', (client_id, trigger, trigger))
            result = cur.fetchone()
            if result:
                # Update usage count
                cur.execute('''
                    UPDATE taught SET times_used = times_used + 1 
                    WHERE client_id = ? AND trigger = ?
                ''', (client_id, trigger))
                conn.commit()
                conn.close()
                return result['response']
            conn.close()
        except Exception as e:
            logger.error(f"Error getting taught response: {e}")
        return None
    
    @staticmethod
    def teach_response(client_id, trigger, response):
        """Teach JAI a new response"""
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Check if exists
            cur.execute('''
                SELECT id FROM taught 
                WHERE client_id = ? AND trigger = ?
            ''', (client_id, trigger))
            
            existing = cur.fetchone()
            
            if existing:
                cur.execute('''
                    UPDATE taught SET response = ? 
                    WHERE client_id = ? AND trigger = ?
                ''', (response, client_id, trigger))
                message = "Updated"
            else:
                cur.execute('''
                    INSERT INTO taught (client_id, trigger, response)
                    VALUES (?, ?, ?)
                ''', (client_id, trigger, response))
                message = "Learned"
            
            conn.commit()
            conn.close()
            logger.info(f"🎓 {message}: '{trigger}' -> '{response}'")
            return True, message
        except Exception as e:
            logger.error(f"Error teaching: {e}")
            return False, str(e)
    
    @staticmethod
    def learn_next_time_say(client_id, trigger_phrase, suggested_response):
        """Learn from 'next time say' pattern"""
        try:
            conn = get_db()
            cur = conn.cursor()
            
            # Check if exists
            cur.execute('''
                SELECT id, times_suggested FROM next_time_say 
                WHERE client_id = ? AND trigger_phrase = ?
            ''', (client_id, trigger_phrase))
            
            existing = cur.fetchone()
            
            if existing:
                cur.execute('''
                    UPDATE next_time_say 
                    SET suggested_response = ?, times_suggested = times_suggested + 1
                    WHERE id = ?
                ''', (suggested_response, existing['id']))
            else:
                cur.execute('''
                    INSERT INTO next_time_say (client_id, trigger_phrase, suggested_response)
                    VALUES (?, ?, ?)
                ''', (client_id, trigger_phrase, suggested_response))
            
            conn.commit()
            conn.close()
            logger.info(f"📚 Learned 'next time say': '{trigger_phrase}' -> '{suggested_response}'")
            return True
        except Exception as e:
            logger.error(f"Error learning next time say: {e}")
            return False
    
    @staticmethod
    def get_next_time_say_response(client_id, message):
        """Check if there's a 'next time say' response for this message"""
        try:
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute('''
                SELECT trigger_phrase, suggested_response, times_used 
                FROM next_time_say 
                WHERE client_id = ?
                ORDER BY times_used ASC, times_suggested DESC
            ''', (client_id,))
            
            patterns = cur.fetchall()
            
            for pattern in patterns:
                if pattern['trigger_phrase'].lower() in message.lower():
                    # Update usage count
                    cur.execute('''
                        UPDATE next_time_say 
                        SET times_used = times_used + 1 
                        WHERE client_id = ? AND trigger_phrase = ?
                    ''', (client_id, pattern['trigger_phrase']))
                    conn.commit()
                    conn.close()
                    return pattern['suggested_response']
            
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting next time say: {e}")
            return None
    
    @staticmethod
    def extract_and_save_user_fact(client_id, message):
        """Extract user facts from conversation and save them"""
        msg_lower = message.lower()
        facts = []
        
        # Name extraction
        name_patterns = [
            r'my name is (\w+)',
            r'i am (\w+)',
            r'call me (\w+)',
            r'i\'m (\w+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                name = match.group(1).capitalize()
                JAIMemory.save_user_fact(client_id, "name", name)
                facts.append(("name", name))
                break
        
        # Age extraction
        age_match = re.search(r'i am (\d+) years? old', msg_lower)
        if age_match:
            age = age_match.group(1)
            JAIMemory.save_user_fact(client_id, "age", age)
            facts.append(("age", age))
        
        # Location extraction
        location_patterns = [
            r'i am from (\w+)',
            r'i live in (\w+)',
            r'i stay in (\w+)',
            r'from (\w+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, msg_lower)
            if match:
                location = match.group(1).capitalize()
                JAIMemory.save_user_fact(client_id, "location", location)
                facts.append(("location", location))
                break
        
        return facts
    
    @staticmethod
    def save_user_fact(client_id, fact_key, fact_value):
        """Save or update a user fact"""
        try:
            conn = get_db()
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO user_facts (client_id, fact_key, fact_value)
                VALUES (?, ?, ?)
                ON CONFLICT(client_id, fact_key) 
                DO UPDATE SET fact_value = excluded.fact_value, 
                             confidence = confidence + 0.1,
                             updated_at = CURRENT_TIMESTAMP
            ''', (client_id, fact_key, fact_value))
            
            conn.commit()
            conn.close()
            logger.info(f"📝 Saved user fact: {client_id} -> {fact_key} = {fact_value}")
            return True
        except Exception as e:
            logger.error(f"Error saving user fact: {e}")
            return False
    
    @staticmethod
    def get_user_facts(client_id):
        """Get all facts about a user"""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                SELECT fact_key, fact_value, confidence 
                FROM user_facts 
                WHERE client_id = ? AND confidence > 0.5
                ORDER BY confidence DESC
            ''', (client_id,))
            results = cur.fetchall()
            conn.close()
            return {row['fact_key']: row['fact_value'] for row in results}
        except Exception as e:
            logger.error(f"Error getting user facts: {e}")
            return {}
    
    @staticmethod
    def save_conversation(client_id, user_message, jai_response):
        """Save conversation for history"""
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO conversations (client_id, user_message, jai_response)
                VALUES (?, ?, ?)
            ''', (client_id, user_message, jai_response))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False