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
            # Keep only last 50 messages
            if len(_conversations[client_id]) > 50:
                _conversations[client_id] = _conversations[client_id][-50:]
            logger.info(f"Saved conversation for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return False
    
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
        
        # IMPORTANT: Check for name patterns FIRST
        # Pattern: "My name is Joshua"
        name_match = re.search(r'(?:my name is|my name\'s|name is|i am|i\'m|call me|you can call me)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', msg_lower, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip().title()
            # Validate name (only letters, not too short, not a common word)
            common_words = ['yes', 'no', 'ok', 'okay', 'good', 'bad', 'fine', 'great', 'awesome']
            if name.isalpha() and len(name) >= 2 and name.lower() not in common_words:
                JAIMemory.save_user_fact(client_id, 'name', name)
                saved_facts.append(('name', name))
                logger.info(f"Extracted and saved name: {name} for {client_id}")
                return saved_facts  # Return immediately after saving name
        
        # Also check for exact patterns with the word "is"
        if 'my name is' in msg_lower:
            parts = msg_lower.split('my name is')
            if len(parts) > 1:
                name_part = parts[1].strip().split()[0] if parts[1].strip() else ''
                if name_part and name_part.isalpha() and len(name_part) >= 2:
                    name = name_part.title()
                    JAIMemory.save_user_fact(client_id, 'name', name)
                    saved_facts.append(('name', name))
                    logger.info(f"Extracted name via simple split: {name}")
                    return saved_facts
        
        # Age pattern
        age_match = re.search(r'(?:i am|i\'m|my age is|age is)\s+(\d+)\s*(?:years old|yrs old|year old)?', msg_lower, re.IGNORECASE)
        if age_match:
            age = age_match.group(1)
            JAIMemory.save_user_fact(client_id, 'age', age)
            saved_facts.append(('age', age))
            logger.info(f"Extracted age: {age}")
            return saved_facts
        
        # Location pattern
        location_match = re.search(r'(?:i live in|i\'m from|my location is|from)\s+([A-Za-z\s]{3,})', msg_lower, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip().title()
            if len(location) > 2:
                JAIMemory.save_user_fact(client_id, 'location', location)
                saved_facts.append(('location', location))
                logger.info(f"Extracted location: {location}")
        
        return saved_facts
    
    @staticmethod
    def teach_response(client_id, trigger, response):
        """Teach the AI a custom response"""
        try:
            if client_id not in _learned_responses:
                _learned_responses[client_id] = {}
            _learned_responses[client_id][trigger.lower()] = response
            logger.info(f"Taught response for {client_id}: {trigger} -> {response}")
            return True, "Response learned!"
        except Exception as e:
            logger.error(f"Error teaching response: {e}")
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
            logger.error(f"Error getting taught response: {e}")
            return None
    
    @staticmethod
    def learn_next_time_say(client_id, trigger, response):
        """Learn a 'next time say' response"""
        try:
            if client_id not in _next_time_say:
                _next_time_say[client_id] = {}
            _next_time_say[client_id][trigger.lower()] = response
            logger.info(f"Learned next_time_say for {client_id}: {trigger} -> {response}")
            return True
        except Exception as e:
            logger.error(f"Error learning next_time_say: {e}")
            return False
    
    @staticmethod
    def get_next_time_say_response(client_id, message):
        """Get a 'next time say' response if trigger matches"""
        try:
            msg_lower = message.lower()
            responses = _next_time_say.get(client_id, {})
            for trigger, response in responses.items():
                if trigger in msg_lower:
                    # Delete after use (one-time)
                    del _next_time_say[client_id][trigger]
                    return response
            return None
        except Exception as e:
            logger.error(f"Error getting next_time_say response: {e}")
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
            logger.info(f"Cleared all data for {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing user data: {e}")
            return False
    
    @staticmethod
    def get_conversation_history(client_id, limit=10):
        """Get recent conversation history"""
        try:
            convs = _conversations.get(client_id, [])
            return [(c['user'], c['ai'], c['time']) for c in convs[-limit:]]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []


# Setup function for compatibility
def setup_database():
    """Compatibility function - no database needed"""
    logger.info("Memory system ready (in-memory storage)")
    pass