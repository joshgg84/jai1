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
        'go', 'come', 'leave', 'stay', 'wait', 'stop', 'start', 'begin', 'end'
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
        
        # ========== NAME EXTRACTION ==========
        name_response = cls._extract_name(msg, client_id)
        if name_response:
            return name_response
        
        # ========== NAME QUESTION DETECTION ==========
        name_question_response = cls._answer_name_question(msg, user_name)
        if name_question_response:
            return name_question_response
        
        # ========== MEMORY AWARENESS QUESTIONS ==========
        memory_response = cls._handle_memory_questions(msg, user_name, client_id)
        if memory_response:
            return memory_response
        
        # ========== EXPLICIT FORGET COMMAND ==========
        if msg in ['forget me', 'clear memory', 'delete my data', 'forget everything']:
            JAIMemory.clear_user_data(client_id)
            return "✅ I've cleared your memory. I won't remember our previous conversations. Starting fresh! 👋"
        
        # ========== EXTRACT OTHER USER FACTS (age, location) ==========
        fact_response = cls._extract_facts(message, client_id)
        if fact_response:
            return fact_response
        
        return None
    
    @classmethod
    def _detect_emotion(cls, msg):
        """Detect user emotions and respond appropriately"""
        emotion_patterns = [
            r'i\'m\s+(confused|tired|happy|sad|angry|excited|bored|scared|worried|stressed|calm|relaxed|frustrated|annoyed|pleased|grateful|thankful|sorry|glad|sick|healthy|fine|okay|good|great|awesome|amazing|wonderful|terrible|horrible|awful|lost|stuck|overwhelmed)',
            r'i am\s+(confused|tired|happy|sad|angry|excited|bored|scared|worried|stressed|calm|relaxed|frustrated|annoyed|pleased|grateful|thankful|sorry|glad|sick|healthy|fine|okay|good|great|awesome|amazing|wonderful|terrible|horrible|awful|lost|stuck|overwhelmed)'
        ]
        
        for pattern in emotion_patterns:
            emotion_match = re.search(pattern, msg, re.IGNORECASE)
            if emotion_match:
                emotion = emotion_match.group(1).lower()
                
                if emotion == 'confused':
                    return "I understand confusion can be frustrating. What part is confusing you? Let me help clarify! 😊"
                elif emotion in ['tired', 'exhausted']:
                    return "Take a break if you need to. Rest is important! I'll be here when you come back. 😊"
                elif emotion in ['happy', 'great', 'awesome', 'amazing', 'wonderful', 'excited']:
                    return "That's wonderful to hear! 😊 What's making you feel this way?"
                elif emotion in ['sad', 'down', 'unhappy']:
                    return "I'm sorry you're feeling this way. I'm here for you if you want to talk about it. 💙"
                elif emotion in ['angry', 'frustrated', 'annoyed']:
                    return "I hear that you're frustrated. Take a deep breath. Want to talk about what's bothering you?"
                elif emotion in ['grateful', 'thankful']:
                    return "That's beautiful. Gratitude changes everything. What are you grateful for today? 😊"
                elif emotion in ['sorry', 'apologize']:
                    return "No need to apologize! 😊 We're just chatting. What's on your mind?"
                else:
                    return f"I hear you. It's okay to feel {emotion}. Want to talk about it?"
        
        return None
    
    @classmethod
    def _extract_name(cls, msg, client_id):
        """Extract user name from message"""
        name_extraction_patterns = [
            r'my name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'i am\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'i\'m\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'call me\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
        ]
        
        for pattern in name_extraction_patterns:
            name_match = re.search(pattern, msg, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip().title()
                # Validate name
                if (extracted_name.isalpha() and 
                    len(extracted_name) >= 2 and 
                    extracted_name.lower() not in cls.INVALID_NAMES):
                    JAIMemory.save_user_fact(client_id, 'name', extracted_name)
                    return f"Nice to meet you, {extracted_name}! 😊 I'll remember your name."
        
        return None
    
    @classmethod
    def _answer_name_question(cls, msg, user_name):
        """Answer questions about user's name"""
        name_question_patterns = [
            r'what(\'s| is)? my name',
            r'do you know my name',
            r'remember my name',
            r'who am i',
            r'what do you call me'
        ]
        
        for pattern in name_question_patterns:
            if re.search(pattern, msg):
                if user_name:
                    return f"Your name is {user_name}! 😊 I remember you."
                else:
                    return "I don't know your name yet. Please tell me: 'My name is [your name]' and I'll remember it! 😊"
        
        return None
    
    @classmethod
    def _handle_memory_questions(cls, msg, user_name, client_id):
        """Handle questions about memory capabilities"""
        if any(word in msg for word in ['remember', 'forget', 'memory', 'recall', 'do you have memory']):
            if user_name:
                if 'remember' in msg or 'recall' in msg:
                    return f"Yes, I remember you, {user_name}! 😊 I store your name and facts in my memory. Even if you leave and come back, I'll still know who you are."
                elif 'forget' in msg:
                    return f"I would never forget you, {user_name}! 😊 But if you want me to forget, you can ask me to 'forget me'."
                else:
                    return f"Yes, {user_name}! I have memory. I remember your name and what you tell me. 🧠"
            else:
                return "I have memory capabilities! I can remember your name, preferences, and important facts. Just tell me your name and I'll remember it! 🧠"
        
        return None
    
    @classmethod
    def _extract_facts(cls, message, client_id):
        """Extract and save user facts (age, location)"""
        msg_lower = message.lower()
        
        # Age extraction
        age_match = re.search(r'(?:i am|i\'m|my age is|age is)\s+(\d+)\s*(?:years old|yrs old|year old)?', msg_lower, re.IGNORECASE)
        if age_match:
            age = age_match.group(1)
            JAIMemory.save_user_fact(client_id, 'age', age)
            return f"Got it! You're {age} years old! I'll remember that."
        
        # Location extraction
        location_match = re.search(r'(?:i live in|i\'m from|my location is|from)\s+([A-Za-z\s]{3,})', msg_lower, re.IGNORECASE)
        if location_match:
            location = location_match.group(1).strip().title()
            if len(location) > 2:
                JAIMemory.save_user_fact(client_id, 'location', location)
                return f"Cool! {location} is a great place! I've saved that."
        
        return None