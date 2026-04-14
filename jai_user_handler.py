"""JAI - User Handler Module
Handles user name extraction, emotion detection, memory awareness, and user-related interactions.
"""

import re
import logging
from jai_memory import JAIMemory

logger = logging.getLogger(__name__)


class UserHandler:
    """Handle user-related interactions: names, emotions, memory, etc."""
    
    # Words that should NEVER be saved as names
    INVALID_NAMES = [
        'yes', 'no', 'ok', 'okay', 'good', 'bad', 'fine', 'great', 'awesome', 
        'hello', 'hi', 'hey', 'bye', 'thanks', 'thank', 'please', 'sorry',
        'confused', 'tired', 'happy', 'sad', 'angry', 'excited', 'bored',
        'what', 'where', 'when', 'why', 'how', 'who', 'which',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'this', 'that', 'these', 'those', 'there', 'their', 'theyre',
        'help', 'need', 'want', 'like', 'love', 'hate', 'feel', 'think',
        'tell', 'ask', 'answer', 'respond', 'reply', 'say', 'talk', 'speak',
        'write', 'read', 'see', 'look', 'watch', 'hear', 'listen',
        'go', 'come', 'leave', 'stay', 'wait', 'stop', 'start', 'begin', 'end',
        'explain', 'summarize', 'describe', 'tell', 'show', 'give', 'concept',
        'deployment', 'project', 'work', 'job', 'career', 'future', 'life'
    ]
    
    @classmethod
    def handle_user_message(cls, message, client_id):
        """Process user message for user-related content"""
        msg = message.lower().strip()
        
        # Get user facts
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== EMOTION / STATE DETECTION ==========
        emotion_response = cls._detect_emotion(msg)
        if emotion_response:
            return emotion_response
        
        # ========== NAME EXTRACTION (Only with explicit patterns) ==========
        name_patterns = [
            r'^my name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'^i am\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'^i\'m\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'^call me\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, msg, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip().title()
                if (extracted_name.isalpha() and 
                    len(extracted_name) >= 2 and 
                    extracted_name.lower() not in cls.INVALID_NAMES):
                    JAIMemory.save_user_fact(client_id, 'name', extracted_name)
                    return f"Nice to meet you, {extracted_name}! 😊 I'll remember your name."
        
        # ========== LOCATION EXTRACTION (Only with explicit patterns) ==========
        # Only trigger if the message is clearly about location
        location_patterns = [
            r'^i live in\s+([A-Za-z\s]{3,})',
            r'^i\'m from\s+([A-Za-z\s]{3,})',
            r'^my location is\s+([A-Za-z\s]{3,})',
            r'^from\s+([A-Za-z\s]{3,})$'
        ]
        
        for pattern in location_patterns:
            location_match = re.search(pattern, msg, re.IGNORECASE)
            if location_match:
                location = location_match.group(1).strip().title()
                if len(location) > 2 and location.lower() not in cls.INVALID_NAMES:
                    JAIMemory.save_user_fact(client_id, 'location', location)
                    return f"Cool! {location} is a great place! I've saved that."
        
        # ========== AGE EXTRACTION ==========
        age_match = re.search(r'(?:^i am|^i\'m|^my age is|^age is)\s+(\d+)\s*(?:years old|yrs old|year old)?', msg, re.IGNORECASE)
        if age_match:
            age = age_match.group(1)
            JAIMemory.save_user_fact(client_id, 'age', age)
            return f"Got it! You're {age} years old! I'll remember that."
        
        # ========== NAME QUESTION ==========
        if any(word in msg for word in ['what\'s my name', 'what is my name', 'do you know my name', 'remember my name']):
            if user_name:
                return f"Your name is {user_name}! 😊 I remember you."
            else:
                return "I don't know your name yet. Please tell me: 'My name is [your name]' and I'll remember it! 😊"
        
        # ========== MEMORY QUESTIONS ==========
        if any(word in msg for word in ['do you have memory', 'can you remember', 'what do you remember']):
            if user_name:
                facts = JAIMemory.get_user_facts(client_id)
                fact_list = "\n".join([f"• {k}: {v}" for k, v in facts.items()]) if facts else "Nothing yet"
                return f"🧠 **Yes, I have memory!**\n\nI remember:\n{fact_list}\n\nAsk me 'forget me' if you want me to clear my memory."
            else:
                return "🧠 **Yes, I have memory!**\n\nI can remember your name, preferences, and important facts. Just tell me your name and I'll remember it!"
        
        # ========== FORGET COMMAND ==========
        if msg in ['forget me', 'clear memory', 'delete my data', 'forget everything']:
            JAIMemory.clear_user_data(client_id)
            return "✅ I've cleared your memory. I won't remember our previous conversations. Starting fresh! 👋"
        
        return None
    
    @classmethod
    def _detect_emotion(cls, msg):
        """Detect user emotions and respond appropriately"""
        emotion_patterns = [
            r'i\'m\s+(confused|tired|happy|sad|angry|excited|bored|scared|worried|stressed)',
            r'i am\s+(confused|tired|happy|sad|angry|excited|bored|scared|worried|stressed)'
        ]
        
        for pattern in emotion_patterns:
            emotion_match = re.search(pattern, msg, re.IGNORECASE)
            if emotion_match:
                emotion = emotion_match.group(1).lower()
                
                if emotion == 'confused':
                    return "I understand confusion can be frustrating. What part is confusing you? Let me help clarify! 😊"
                elif emotion == 'tired':
                    return "Take a break if you need to. Rest is important! I'll be here when you come back. 😊"
                elif emotion == 'happy':
                    return "That's wonderful to hear! 😊 What's making you feel this way?"
                elif emotion == 'sad':
                    return "I'm sorry you're feeling this way. I'm here for you if you want to talk about it. 💙"
                elif emotion == 'angry':
                    return "I hear that you're frustrated. Take a deep breath. Want to talk about what's bothering you?"
                else:
                    return f"I hear you. It's okay to feel {emotion}. Want to talk about it?"
        
        return None