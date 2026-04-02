"""JAI - Core Personality Module
Main response generation with memory, services, and conversation logic.
"""

import random
import re
import logging
from datetime import datetime
from jai_nlp import JAINLP
from jai_casual import JAICasual
from jai_natural import JAINatural
from jai_conversation import JAIConversational
from jai_intent import JAIIntent
from jai_currency import JAICurrency
from jai_grammar import JAIGrammar
from jai_grammar_long import JAIGrammarLong
from jai_memory import JAIMemory
from jai_services import WebSearch, Weather, Calculator, TimeService

logger = logging.getLogger(__name__)


class JAIPersonality:
    """Main JAI personality with memory and services"""
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title="", client_id="unknown"):
        """Main response generator"""
        msg = message.lower().strip()
        
        # ========== STEP 1: WEATHER ==========
        weather_response = Weather.detect_weather_query(message)
        if weather_response:
            JAIMemory.save_conversation(client_id, message, weather_response)
            return weather_response
        
        # ========== STEP 2: WEB SEARCH (BEFORE ANYTHING ELSE) ==========
        if WebSearch.should_search(message):
            search_result = WebSearch.search_online(message)
            if search_result:
                # Truncate if too long
                if len(search_result) > 600:
                    search_result = search_result[:600] + "..."
                
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, message, response)
                return response
        
        # ========== STEP 3: MEMORY ==========
        
        # Check next time say patterns
        next_time_response = JAIMemory.get_next_time_say_response(client_id, message)
        if next_time_response:
            return next_time_response
        
        # Check taught responses
        taught_response = JAIMemory.get_taught_response(client_id, message)
        if taught_response:
            return taught_response
        
        # Extract user facts
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, message)
        if learned_facts:
            for fact_key, fact_value in learned_facts:
                if fact_key == "name":
                    return f"Nice to meet you, {fact_value}! I'll remember that. 😊"
                elif fact_key == "age":
                    return f"Got it! You're {fact_value} years old!"
                elif fact_key == "location":
                    return f"Cool! {fact_value} is a great place!"
        
        # Get user facts
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== STEP 4: LEARNING PATTERNS ==========
        
        # Next time say teaching
        next_time_pattern = re.search(r'next time .+? say[s]? ["\']?(.+?)["\']?\s+(?:say|respond with) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            JAIMemory.learn_next_time_say(client_id, trigger, response)
            return f"📚 Got it! Next time someone says '{trigger}', I'll respond with '{response}'"
        
        # Direct teaching
        teach_pattern = re.search(r'teach ["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(1).strip()
            response = teach_pattern.group(2).strip()
            JAIMemory.teach_response(client_id, trigger, response)
            return f"✅ Learned! When you say '{trigger}', I'll respond with '{response}'"
        
        # ========== STEP 5: GREETINGS & BASIC CONVERSATION ==========
        
        # Time greetings
        if "good morning" in msg or "morning" in msg:
            return f"Good morning{', ' + user_name if user_name else ''}! 🌅 Hope you slept well!"
        
        if "good afternoon" in msg or "afternoon" in msg:
            return f"Good afternoon{', ' + user_name if user_name else ''}! 🌞 How's your day?"
        
        if "good evening" in msg or "evening" in msg:
            return f"Good evening{', ' + user_name if user_name else ''}! 🌙 Hope you had a productive day!"
        
        # Basic greetings
        if any(g in msg for g in ["hi", "hello", "hey"]):
            if user_name:
                return f"Hello {user_name}! 😊 How can I help you today?"
            return "Hello! 😊 How can I help you today?"
        
        # How are you
        if any(h in msg for h in ["how are you", "how you doing"]):
            return "I'm doing great! Thanks for asking. How about you?"
        
        # Thanks
        if any(t in msg for t in ["thank", "thanks"]):
            return "You're welcome! 😊 Happy to help!"
        
        # Goodbye
        if any(g in msg for g in ["bye", "goodbye", "see you"]):
            return "Goodbye! Take care! 👋"
        
        # Creator
        if any(c in msg for c in ["who made you", "who created you"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬"
        
        # Capabilities
        if any(c in msg for c in ["what can you do", "your skills"]):
            return "I can: search online 🔍, check weather 🌤️, convert currency 💰, calculate math 🧮, and remember what you teach me!"
        
        # ========== STEP 6: CURRENCY ==========
        currency_result = JAICurrency.detect_and_convert(message)
        if currency_result:
            return currency_result
        
        # ========== STEP 7: CALCULATIONS ==========
        if Calculator.should_calculate(message):
            calc_result = Calculator.calculate(message)
            if calc_result:
                return calc_result
        
        # ========== STEP 8: TIME & DATE ==========
        if "time" in msg:
            return TimeService.get_time()
        if "date" in msg:
            return TimeService.get_date()
        
        # ========== STEP 9: JOKES ==========
        if any(j in msg for j in ["joke", "funny"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾"
            ]
            return random.choice(jokes)
        
        # ========== STEP 10: INTENT RESPONSES ==========
        intent = JAINLP.extract_intent(message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        # ========== STEP 11: CASUAL RESPONSES ==========
        casual = JAICasual.get_casual_response(message)
        if casual:
            return casual
        
        natural = JAINatural.get_natural_response(message)
        if natural:
            return natural
        
        conv = JAIConversational.get_response(message)
        if conv:
            return conv
        
        # ========== STEP 12: DEFAULT (NO SLANG FALLBACK) ==========
        fallbacks = [
            "That's interesting. Tell me more!",
            "I hear you. What else is on your mind?",
            "Go on, I'm listening.",
            "How does that make you feel?"
        ]
        
        if user_name:
            fallbacks = [
                f"What's on your mind, {user_name}?",
                f"Tell me more about that, {user_name}."
            ]
        
        return random.choice(fallbacks)