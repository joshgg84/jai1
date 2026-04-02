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
        
        # ========== STEP 2: WEB SEARCH (FOR QUESTIONS) ==========
        # Special check: "what is" without numbers should go to search
        if 'what is' in msg and not re.search(r'\d+', msg):
            logger.info(f"Question detected (what is without numbers): {message}")
            search_result = WebSearch.search_online(message)
            if search_result:
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, message, response)
                return response
        
        # Check if message is a question or contains question words
        is_question = message.strip().endswith('?')
        has_question_word = any(word in msg.split()[:3] for word in ['who', 'what', 'where', 'when', 'why', 'how'])
        
        if is_question or has_question_word:
            logger.info(f"Question detected: {message}")
            search_result = WebSearch.search_online(message)
            
            if search_result:
                logger.info(f"Search successful, returning result")
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, message, response)
                return response
        
        # ========== STEP 3: CHECK MEMORY ==========
        
        # Check for "next time say" patterns
        next_time_response = JAIMemory.get_next_time_say_response(client_id, message)
        if next_time_response:
            return next_time_response
        
        # Check taught responses
        taught_response = JAIMemory.get_taught_response(client_id, message)
        if taught_response:
            return taught_response
        
        # Extract and save user facts
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, message)
        if learned_facts:
            for fact_key, fact_value in learned_facts:
                if fact_key == "name":
                    return f"Nice to meet you, {fact_value}! I'll remember that. 😊"
                elif fact_key == "age":
                    return f"Got it! You're {fact_value} years old. That's awesome!"
                elif fact_key == "location":
                    return f"Cool! {fact_value} is a great place. What's it like there?"
        
        # Get user facts for personalization
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== STEP 4: CHECK FOR LEARNING PATTERNS ==========
        
        # Check for "next time say" teaching pattern
        next_time_pattern = re.search(r'next time (?:someone|they|you) (?:say|asks?) ["\']?(.+?)["\']?\s*(?:say|respond with|tell them) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if not next_time_pattern:
            next_time_pattern = re.search(r'when (?:someone|they|you) (?:says|asks?) ["\']?(.+?)["\']?,\s*(?:say|respond with|tell them) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            success = JAIMemory.learn_next_time_say(client_id, trigger, response)
            if success:
                return f"📚 Got it! Next time someone says '{trigger}', I'll respond with '{response}'. Thanks for teaching me!"
            else:
                return "📚 Thanks for the suggestion! I'll try to remember that."
        
        # Check for direct teaching pattern
        teach_pattern = re.search(r'(teach|learn)\s+["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(2).strip()
            response = teach_pattern.group(3).strip()
            success, message_result = JAIMemory.teach_response(client_id, trigger, response)
            if success:
                return f"✅ I learned that! When you say '{trigger}', I'll respond with '{response}'"
            else:
                return f"❌ Sorry, I couldn't learn that. Error: {message_result}"
        
        # ========== STEP 5: TIME GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            greeting = "Good morning! 🌅 Hope you slept well. What is on your agenda today?"
            if user_name:
                greeting = f"Good morning, {user_name}! 🌅 Hope you slept well. What's on your agenda today?"
            return greeting
        
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            greeting = "Good afternoon! 🌞 How is your day treating you?"
            if user_name:
                greeting = f"Good afternoon, {user_name}! 🌞 How's your day treating you?"
            return greeting
        
        if any(g in msg for g in ["good evening", "evening"]):
            greeting = "Good evening! 🌙 Hope you had a productive day."
            if user_name:
                greeting = f"Good evening, {user_name}! 🌙 Hope you had a productive day."
            return greeting
        
        if any(g in msg for g in ["good night", "night"]):
            return "Good night! 🌙 Rest well. Tomorrow is another chance."
        
        # ========== STEP 6: BASIC GREETINGS ==========
        if any(g in msg for g in ["hi", "hello", "hey", "howdy", "sup"]):
            if user_name:
                return random.choice([
                    f"Hello {user_name}! 😊 How can I help you today?",
                    f"Hey {user_name}! What's good?",
                    f"Hi {user_name}! Ready to chat?"
                ])
            return random.choice([
                "Hello! 😊 How can I help you today?",
                "Hey there! What's good?",
                "Hi! Ready to chat?"
            ])
        
        # ========== STEP 7: HOW ARE YOU? ==========
        if any(h in msg for h in ["how are you", "how you doing", "how is it going", "how are you doing"]):
            responses = [
                "I am doing great! Thanks for asking. How about you?",
                "I am good, just vibing. What about you?",
                "Doing well! What is new with you today?",
                "I am here! More importantly, how are YOU doing?"
            ]
            if user_name:
                responses = [
                    f"I'm doing great, {user_name}! Thanks for asking. How about you?",
                    f"Doing well, {user_name}! What's new with you today?"
                ]
            return random.choice(responses)
        
        # ========== STEP 8: FOLLOW-UP RESPONSES ==========
        if any(f in msg for f in ["i am fine", "i am good", "doing good", "doing well", "i am alright"]):
            if any(q in msg for q in ["what about you", "how about you", "and you", "u?", "you?"]):
                return random.choice([
                    "I am doing great, thanks for asking! 😊 What has been the highlight of your day so far?",
                    "I am good! Just been here, ready to chat. What is new with you?",
                    "I am doing well! Thanks for checking. What is on your mind today?",
                    "I am alright — better now that you asked. So what is happening in your world?"
                ])
            else:
                return random.choice([
                    "Glad to hear that! 😊 What has been going well?",
                    "That is good! Anything exciting happening today?",
                    "Happy to hear that. What are you up to?"
                ])
        
        # ========== STEP 9: THANKS ==========
        if any(t in msg for t in ["thank", "thanks", "thx"]):
            return random.choice([
                "You're welcome! 😊 Happy to help.",
                "Anytime! That's what I'm here for.",
                "My pleasure!"
            ])
        
        # ========== STEP 10: GOODBYE ==========
        if any(g in msg for g in ["bye", "goodbye", "see you", "later"]):
            return random.choice([
                "Goodbye! Take care! 👋",
                "See you later! Come back anytime.",
                "Peace! Have a great day!"
            ])
        
        # ========== STEP 11: CREATOR ==========
        if any(c in msg for c in ["who made you", "who created you", "your creator"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬 He built me to be a helpful companion that learns from every conversation."
        
        # ========== STEP 12: CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "help with"]):
            return "I can chat with you, do calculations 💰, convert currencies with live rates, check weather 🌤️, search online 🔍, and most importantly - I LEARN! \n\nYou can:\n• Teach me: 'teach hello -> Hi there!'\n• Next time say: 'next time someone says hello say Hey!'\n• Share your name, age, or location"
        
        # ========== STEP 13: CURRENCY CONVERSION ==========
        currency_result = JAICurrency.detect_and_convert(message)
        if currency_result:
            return currency_result
        
        # ========== STEP 14: CALCULATIONS (ONLY IF NUMBERS ARE PRESENT) ==========
        # Check if message contains math operators AND has numbers
        has_math_ops = any(op in msg for op in ["+", "-", "*", "/", "%"])
        has_numbers = len(re.findall(r'\d+', message)) >= 2
        
        # Only trigger calculation if there are actual numbers to calculate
        if has_math_ops and has_numbers:
            calc_result = Calculator.calculate(message)
            if calc_result:
                return calc_result
        
        # Handle "what is X percent of Y" pattern separately
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(message)
            if calc_result:
                return calc_result
        
        # ========== STEP 15: TIME & DATE ==========
        if "time" in msg:
            return TimeService.get_time()
        
        if "date" in msg:
            return TimeService.get_date()
        
        # ========== STEP 16: JOKES ==========
        if any(j in msg for j in ["joke", "funny", "make me laugh"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "What do you call a Nigerian who knows cyber security? A Nai-ja breaker! 😂"
            ]
            return random.choice(jokes)
        
        # ========== STEP 17: MOTIVATION ==========
        if any(m in msg for m in ["motivate me", "inspire me", "give me motivation"]):
            return JAIGrammarLong.build_long_motivation()
        
        # ========== STEP 18: USE JAIINTENT ==========
        intent = JAINLP.extract_intent(message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        # ========== STEP 19: SENTIMENT ANALYSIS ==========
        analysis = JAINLP.analyze_sentence(message)
        if analysis and analysis['sentiment']['emotion'] in ['positive', 'negative']:
            polarity = analysis['sentiment']['polarity']
            
            if polarity > 0.6:
                return "Wow! That energy is contagious! 🎉 Tell me everything — I want to celebrate with you!"
            
            if polarity < -0.6:
                return "That sounds really heavy. I am here with you. Want to talk it through? No pressure."
        
        # ========== STEP 20: CASUAL RESPONSES ==========
        casual = JAICasual.get_casual_response(message)
        if casual:
            return casual
        
        natural = JAINatural.get_natural_response(message)
        if natural:
            return natural
        
        conv = JAIConversational.get_response(message)
        if conv:
            return conv
        
        # ========== STEP 21: DEFAULT FALLBACK ==========
        fallbacks = [
            "That's interesting. Tell me more!",
            "I hear you. What else is on your mind?",
            "Go on, I'm listening.",
            "How does that make you feel?",
            "That's a good point. What do you think?",
            "I'm here for you. What would you like to talk about?"
        ]
        
        # Personalize fallback if we know user's name
        if user_name:
            personalized_fallbacks = [
                f"What's on your mind, {user_name}?",
                f"Tell me more about that, {user_name}.",
                f"How are you feeling about that, {user_name}?"
            ]
            fallbacks.extend(personalized_fallbacks)
        
        return random.choice(fallbacks)