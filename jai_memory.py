"""JAI - Memory Module
Handles user memory, facts, and conversation history using in-memory storage.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory storage
_user_facts = {}
_conversations = {}
_learned_responses = {}
_next_time_say = {}
_current_feature = {}  # NEW: Store current feature/page per user


class JAIMemory:
    """Handle user memory and facts using in-memory storage"""
    
    @staticmethod
    def save_conversation(client_id, user_message, ai_response):
        """Save conversation to history"""
        try:
            if client_id not in _conversations:
                _conversations[client_id] = []
            _conversations[client_id].append({
                'user': user_message,
                'ai': ai_response,
                'time': datetime.now()
            })
            if len(_conversations[client_id]) > 50:
                _conversations[client_id] = _conversations[client_id][-50:]
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
    @staticmethod
    def set_current_feature(client_id, feature_name):
        """Set the current feature/page the user is on"""
        _current_feature[client_id] = feature_name
        logger.info(f"User {client_id} entered feature: {feature_name}")
        return True
    
    @staticmethod
    def get_current_feature(client_id):
        """Get the current feature/page the user is on"""
        return _current_feature.get(client_id, None)
    
    @staticmethod
    def save_user_fact(client_id, key, value):
        """Save a fact about the user"""
        try:
            if client_id not in _user_facts:
                _user_facts[client_id] = {}
            _user_facts[client_id][key.lower()] = value
            logger.info(f"Saved fact for {client_id}: {key}={value}")
            return True
        except Exception as e:
            logger.error(f"Error saving fact: {e}")
            return False
    
    @staticmethod
    def get_user_fact(client_id, key):
        """Get a specific fact about the user"""
        try:
            facts = _user_facts.get(client_id, {})
            return facts.get(key.lower())
        except Exception as e:
            logger.error(f"Error getting fact: {e}")
            return None
    
    @staticmethod
    def get_user_facts(client_id):
        """Get all facts about the user"""
        try:
            return _user_facts.get(client_id, {}).copy()
        except Exception as e:
            logger.error(f"Error getting facts: {e}")
            return {}
    
    @staticmethod
    def extract_and_save_user_fact(client_id, message):
        """Extract user facts from message and save them"""
        msg_lower = message.lower().strip()
        saved_facts = []
        
        # Name extraction (only with explicit patterns)
        name_match = re.search(r'(?:my name is|my name\'s|name is|i am|i\'m|call me)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', msg_lower, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip().title()
            common_words = ['yes', 'no', 'ok', 'okay', 'good', 'bad', 'fine', 'great', 'awesome', 'hello', 'hi', 'explain', 'summarize']
            if name.isalpha() and len(name) >= 2 and name.lower() not in common_words:
                JAIMemory.save_user_fact(client_id, 'name', name)
                saved_facts.append(('name', name))
                return saved_facts
        
        # Age extraction
        age_match = re.search(r'(?:i am|i\'m|my age is|age is)\s+(\d+)\s*(?:years old|yrs old|year old)?', msg_lower, re.IGNORECASE)
        if age_match:
            age = age_match.group(1)
            JAIMemory.save_user_fact(client_id, 'age', age)
            saved_facts.append(('age', age))
            return saved_facts
        
        # Location extraction (only with explicit patterns)
        location_match = re.search(r'(?:i live in|i\'m from|my location is|from)\s+([A-Za-z\s]{3,})', msg_lower, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip().title()
            if len(location) > 2:
                JAIMemory.save_user_fact(client_id, 'location', location)
                saved_facts.append(('location', location))
        
        return saved_facts
    
    @staticmethod
    def teach_response(client_id, trigger, response):
        """Teach the AI a custom response"""
        try:
            if client_id not in _learned_responses:
                _learned_responses[client_id] = {}
            _learned_responses[client_id][trigger.lower()] = response
            return True, "Response learned!"
        except Exception as e:
            return False, f"Error: {e}"
    
    @staticmethod
    def get_taught_response(client_id, message):
        """Get a taught response if trigger matches"""
        try:
            msg_lower = message.lower()
            responses = _learned_responses.get(client_id, {})
            for trigger, response in responses.items():
                if trigger in msg_lower:
                    return response
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def learn_next_time_say(client_id, trigger, response):
        """Learn a 'next time say' response"""
        try:
            if client_id not in _next_time_say:
                _next_time_say[client_id] = {}
            _next_time_say[client_id][trigger.lower()] = response
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def get_next_time_say_response(client_id, message):
        """Get a 'next time say' response if trigger matches"""
        try:
            msg_lower = message.lower()
            responses = _next_time_say.get(client_id, {})
            for trigger, response in responses.items():
                if trigger in msg_lower:
                    del _next_time_say[client_id][trigger]
                    return response
            return None
        except Exception as e:
            return None
    
    @staticmethod
    def clear_user_data(client_id):
        """Clear all data for a user"""
        try:
            if client_id in _user_facts:
                del _user_facts[client_id]
            if client_id in _conversations:
                del _conversations[client_id]
            if client_id in _learned_responses:
                del _learned_responses[client_id]
            if client_id in _next_time_say:
                del _next_time_say[client_id]
            if client_id in _current_feature:
                del _current_feature[client_id]
            return True
        except Exception as e:
            return False
    
    @staticmethod
    def get_conversation_history(client_id, limit=10):
        """Get recent conversation history"""
        try:
            convs = _conversations.get(client_id, [])
            return [(c['user'], c['ai'], c['time']) for c in convs[-limit:]]
        except Exception as e:
            return []


def setup_database():
    """Compatibility function - no database needed"""
    logger.info("Memory system ready (in-memory storage)")
    pass