"""JAI - Core Personality Module
Main response generation orchestrating all services.
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
from jai_document import DocumentHandler

logger = logging.getLogger(__name__)


class JAIPersonality:
    """Main JAI personality orchestrating all features"""
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title="", client_id="unknown"):
        """Main response generator"""
        msg = message.lower().strip()
        original_message = message
        
        # ========== DOCUMENT UPLOAD COMMAND ==========
        if msg.startswith('upload_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    filename = parts[1].strip()
                    base64_content = parts[2].strip()
                    
                    text = DocumentHandler.extract_text_from_base64(base64_content, filename)
                    
                    if text and len(text.strip()) > 10:
                        simplified = DocumentHandler.simplify_document(text, filename)
                        DocumentHandler.store_document(client_id, filename, text, simplified)
                        long_summary = DocumentHandler.generate_long_summary(text, filename)
                        JAIMemory.save_conversation(client_id, original_message, f"Document uploaded: {filename}")
                        return f"✅ **Document uploaded successfully!**\n\n{long_summary}"
                    else:
                        return "❌ File appears empty or unreadable. Please check the file and try again."
                else:
                    return "❌ Invalid upload format. Please use the upload button."
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return f"❌ Error: {str(e)}"
        
        # ========== DOCUMENT INTELLIGENCE ==========
        if DocumentHandler.has_document(client_id):
            doc = DocumentHandler.get_user_document(client_id)
            if doc:
                doc_answer = DocumentHandler.answer_question(client_id, original_message)
                if doc_answer:
                    JAIMemory.save_conversation(client_id, original_message, doc_answer)
                    return doc_answer
        
        # ========== GET USER MEMORY FACTS ==========
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== NAME EXTRACTION (BEFORE ANYTHING ELSE) ==========
        # Check if user is telling us their name
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
                # Validate name (only letters, not too short, not common words)
                common_words = ['yes', 'no', 'ok', 'okay', 'good', 'bad', 'fine', 'great', 'awesome', 'hello', 'hi']
                if extracted_name.isalpha() and len(extracted_name) >= 2 and extracted_name.lower() not in common_words:
                    JAIMemory.save_user_fact(client_id, 'name', extracted_name)
                    user_name = extracted_name
                    response = f"Nice to meet you, {extracted_name}! 😊 I'll remember your name."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
        
        # ========== NAME QUESTION DETECTION (HIGHEST PRIORITY) ==========
        # This MUST come before general knowledge search
        name_question_patterns = [
            r'what(\'s| is)? my name',
            r'do you know my name',
            r'remember my name',
            r'who am i',
            r'what do you call me',
            r'my name'
        ]
        
        for pattern in name_question_patterns:
            if re.search(pattern, msg):
                if user_name:
                    response = f"Your name is {user_name}! 😊 I remember you."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
                else:
                    response = "I don't know your name yet. Please tell me: 'My name is [your name]' and I'll remember it! 😊"
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
        
        # ========== MEMORY AWARENESS QUESTIONS ==========
        if any(word in msg for word in ['remember', 'forget', 'memory', 'recall', 'do you have memory']):
            if user_name:
                if 'remember' in msg or 'recall' in msg:
                    response = f"Yes, I remember you, {user_name}! 😊 I store your name and facts in my memory. Even if you leave and come back, I'll still know who you are."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
                elif 'forget' in msg:
                    response = f"I would never forget you, {user_name}! 😊 But if you want me to forget, you can ask me to 'forget me'."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
                else:
                    response = f"Yes, {user_name}! I have memory. I remember your name and what you tell me. 🧠"
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
            else:
                response = "I have memory capabilities! I can remember your name, preferences, and important facts. Just tell me your name and I'll remember it! 🧠"
                JAIMemory.save_conversation(client_id, original_message, response)
                return response
        
        # ========== EXPLICIT FORGET COMMAND ==========
        if msg == 'forget me' or msg == 'clear memory' or msg == 'delete my data':
            JAIMemory.clear_user_data(client_id)
            response = "✅ I've cleared your memory. I won't remember our previous conversations. Starting fresh! 👋"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== EXTRACT OTHER USER FACTS (age, location, etc.) ==========
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, original_message)
        if learned_facts:
            for fact_key, fact_value in learned_facts:
                if fact_key == "age":
                    response = f"Got it! You're {fact_value} years old! I'll remember that."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
                elif fact_key == "location":
                    response = f"Cool! {fact_value} is a great place! I've saved that."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return response
        
        # ========== CURRENCY CONVERSION ==========
        currency_result = JAICurrency.detect_and_convert(original_message)
        if currency_result:
            JAIMemory.save_conversation(client_id, original_message, currency_result)
            return currency_result
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(original_message)
        if weather_response:
            JAIMemory.save_conversation(client_id, original_message, weather_response)
            return weather_response
        
        # ========== CALCULATIONS ==========
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                JAIMemory.save_conversation(client_id, original_message, calc_result)
                return calc_result
        
        has_numbers = len(re.findall(r'\d+', original_message)) >= 2
        has_math_op = any(op in msg for op in ['+', '-', '*', '/', '%'])
        if has_numbers and has_math_op:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                JAIMemory.save_conversation(client_id, original_message, calc_result)
                return calc_result
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            time_response = TimeService.get_time()
            JAIMemory.save_conversation(client_id, original_message, time_response)
            return time_response
        if "date" in msg:
            date_response = TimeService.get_date()
            JAIMemory.save_conversation(client_id, original_message, date_response)
            return date_response
        
        # ========== LEARNED RESPONSES (TEACH FUNCTIONALITY) ==========
        taught_response = JAIMemory.get_taught_response(client_id, original_message)
        if taught_response:
            JAIMemory.save_conversation(client_id, original_message, taught_response)
            return taught_response
        
        next_time_response = JAIMemory.get_next_time_say_response(client_id, original_message)
        if next_time_response:
            JAIMemory.save_conversation(client_id, original_message, next_time_response)
            return next_time_response
        
        # ========== CHECK FOR GENERAL KNOWLEDGE QUESTIONS ==========
        clean_msg = msg.strip()
        clean_msg = re.sub(r'\?{3,}', '?', clean_msg)
        
        general_knowledge_patterns = [
            r'who created', r'who founded', r'who invented', r'who discovered',
            r'who is', r'who was', r'who are',
            r'what is', r'what was', r'what are', r'what does',
            r'where is', r'where was', r'where are',
            r'when is', r'when was', r'when did',
            r'why is', r'why was', r'why did',
            r'how to', r'how do', r'how does',
            r'tell me about', r'explain', r'define', r'meaning of',
            r'what does .+ mean', r'what is .+ called',
            r'can you tell me', r'do you know', r'i want to know',
            r'please explain', r'help me understand'
        ]
        
        is_general_knowledge = False
        for pattern in general_knowledge_patterns:
            if re.search(pattern, clean_msg):
                is_general_knowledge = True
                logger.info(f"General knowledge detected: {pattern}")
                break
        
        has_question_mark = '?' in original_message or '？' in original_message
        question_start_words = ['what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose', 'whom']
        starts_with_question = any(clean_msg.startswith(word) for word in question_start_words)
        
        if has_question_mark or starts_with_question:
            is_general_knowledge = True
        
        if len(clean_msg) < 30 and has_question_mark:
            is_general_knowledge = True
        
        if is_general_knowledge:
            logger.info(f"Searching online for: {original_message}")
            search_result = WebSearch.search_online(original_message)
            if search_result:
                JAIMemory.save_conversation(client_id, original_message, search_result)
                return search_result
        
        # ========== LEARNING PATTERNS ==========
        next_time_pattern = re.search(r'next time .+? say[s]? ["\']?(.+?)["\']?\s+(?:say|respond with) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            JAIMemory.learn_next_time_say(client_id, trigger, response)
            result = f"📚 Got it! When someone says '{trigger}', I'll respond with '{response}'"
            JAIMemory.save_conversation(client_id, original_message, result)
            return result
        
        teach_pattern = re.search(r'teach ["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(1).strip()
            response = teach_pattern.group(2).strip()
            JAIMemory.teach_response(client_id, trigger, response)
            result = f"✅ Learned! '{trigger}' -> '{response}'"
            JAIMemory.save_conversation(client_id, original_message, result)
            return result
        
        # ========== GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            response = f"Good morning{', ' + user_name if user_name else ''}! 🌅"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            response = f"Good afternoon{', ' + user_name if user_name else ''}! 🌞"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        if any(g in msg for g in ["good evening", "evening"]):
            response = f"Good evening{', ' + user_name if user_name else ''}! 🌙"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        if any(g in msg for g in ["good night", "night"]):
            response = "Good night! 🌙"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        if any(g in msg for g in ["hi", "hello", "hey", "howdy"]):
            if user_name:
                response = f"Hello {user_name}! 😊 How can I help you today?"
            else:
                response = "Hello! 😊 I'm K-LYNX AI++. What's your name? (Tell me 'My name is...')"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== HOW ARE YOU ==========
        if any(h in msg for h in ["how are you", "how you doing"]):
            response = "I'm doing great! Thanks for asking! How can I help you today?"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== THANKS ==========
        if any(t in msg for t in ["thank", "thanks"]):
            response = "You're welcome! 😊 Is there anything else I can help with?"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== GOODBYE ==========
        if any(g in msg for g in ["bye", "goodbye", "see you"]):
            response = f"Goodbye{', ' + user_name if user_name else ''}! Take care! 👋 I'll be here when you return."
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== CREATOR ==========
        if any(c in msg for c in ["who made you", "who created you"]):
            response = "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "help", "capabilities"]):
            doc_status = ""
            if DocumentHandler.has_document(client_id):
                doc = DocumentHandler.get_user_document(client_id)
                doc_status = f"\n\n📄 **Document loaded:** '{doc['filename']}'"
            response = f"📚 **I can help with:**\n\n🔍 **Search online** - Ask any question\n📄 **Read documents** - Upload PDF/DOCX/TXT\n🌤️ **Weather** - Current conditions\n💰 **Currency** - Live exchange rates\n🧮 **Calculate** - Math problems\n💾 **Memory** - I remember your name and facts!\n\n💡 Try asking: 'What is Python?' or '100 USD to KES'{doc_status}"
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== JOKES ==========
        if any(j in msg for j in ["joke", "funny"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "What do you call a bear with no teeth? A gummy bear! 🐻",
                "Why don't eggs tell jokes? They'd crack each other up! 🥚"
            ]
            response = random.choice(jokes)
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== MOTIVATION ==========
        if any(m in msg for m in ["motivate me", "inspire me"]):
            response = JAIGrammarLong.build_long_motivation()
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== INTENT & CASUAL ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            JAIMemory.save_conversation(client_id, original_message, intent_response)
            return intent_response
        
        casual = JAICasual.get_casual_response(original_message)
        if casual:
            JAIMemory.save_conversation(client_id, original_message, casual)
            return casual
        
        natural = JAINatural.get_natural_response(original_message)
        if natural:
            JAIMemory.save_conversation(client_id, original_message, natural)
            return natural
        
        conv = JAIConversational.get_response(original_message)
        if conv:
            JAIMemory.save_conversation(client_id, original_message, conv)
            return conv
        
        # ========== DEFAULT FALLBACK ==========
        fallbacks = [
            "That's interesting. Tell me more!",
            "I hear you. What else is on your mind?",
            "Go on, I'm listening.",
            "Tell me more about that."
        ]
        
        if user_name:
            fallbacks = [f"What's on your mind, {user_name}?", f"Tell me more, {user_name}."]
        
        response = random.choice(fallbacks)
        JAIMemory.save_conversation(client_id, original_message, response)
        return response