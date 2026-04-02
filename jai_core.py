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
                        preview = text[:200] + "..." if len(text) > 200 else text
                        simplified = DocumentHandler.simplify_document(text, filename)
                        DocumentHandler.store_document(client_id, filename, text, simplified)
                        
                        return f"✅ **Document uploaded!**\n\n" \
                               f"📄 **{filename}**\n" \
                               f"📊 {len(text)} characters\n" \
                               f"📝 Preview: \"{preview}\"\n\n" \
                               f"{simplified}\n\n" \
                               f"💡 **Now ask me anything!** I'll answer from your document or search online."
                    else:
                        return "❌ File appears empty or unreadable. Please check the file and try again."
                else:
                    return "❌ Invalid upload format. Please use the upload button."
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return f"❌ Error: {str(e)}"
        
        # ========== CHECK FOR GENERAL KNOWLEDGE QUESTIONS (ALWAYS SEARCH FIRST) ==========
        # These patterns should ALWAYS trigger web search
        general_knowledge_patterns = [
            r'who created', r'who founded', r'who invented', r'who discovered',
            r'who is', r'who was', r'who are',
            r'what is', r'what was', r'what are', r'what does',
            r'where is', r'where was', r'where are',
            r'when is', r'when was', r'when did',
            r'why is', r'why was', r'why did',
            r'how to', r'how do', r'how does',
            r'tell me about', r'explain', r'define', r'meaning of',
            r'what does .+ mean', r'what is .+ called'
        ]
        
        is_general_knowledge = False
        for pattern in general_knowledge_patterns:
            if re.search(pattern, msg):
                is_general_knowledge = True
                logger.info(f"General knowledge detected: {pattern}")
                break
        
        # Also check if message ends with question mark
        if original_message.strip().endswith('?'):
            is_general_knowledge = True
            logger.info("General knowledge detected: question mark")
        
        # GENERAL KNOWLEDGE - SEARCH ONLINE FIRST
        if is_general_knowledge:
            logger.info(f"Searching online for: {original_message}")
            search_result = WebSearch.search_online(original_message)
            if search_result:
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, original_message, response)
                return response
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(original_message)
        if weather_response:
            JAIMemory.save_conversation(client_id, original_message, weather_response)
            return weather_response
        
        # ========== DOCUMENT INTELLIGENCE (if document loaded) ==========
        if DocumentHandler.has_document(client_id):
            doc = DocumentHandler.get_user_document(client_id)
            if doc:
                # Answer from document
                doc_answer = DocumentHandler.answer_question(client_id, original_message)
                if doc_answer and not doc_answer.startswith("🔍"):
                    JAIMemory.save_conversation(client_id, original_message, doc_answer)
                    return doc_answer
        
        # ========== CALCULATIONS ==========
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                return calc_result
        
        has_numbers = len(re.findall(r'\d+', original_message)) >= 2
        has_math_op = any(op in msg for op in ['+', '-', '*', '/', '%'])
        if has_numbers and has_math_op:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                return calc_result
        
        # ========== CURRENCY CONVERSION ==========
        currency_result = JAICurrency.detect_and_convert(original_message)
        if currency_result:
            return currency_result
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            return TimeService.get_time()
        if "date" in msg:
            return TimeService.get_date()
        
        # ========== MEMORY ==========
        next_time_response = JAIMemory.get_next_time_say_response(client_id, original_message)
        if next_time_response:
            return next_time_response
        
        taught_response = JAIMemory.get_taught_response(client_id, original_message)
        if taught_response:
            return taught_response
        
        # Extract user facts
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, original_message)
        if learned_facts:
            for fact_key, fact_value in learned_facts:
                if fact_key == "name":
                    return f"Nice to meet you, {fact_value}! 😊"
                elif fact_key == "age":
                    return f"Got it! You're {fact_value} years old!"
                elif fact_key == "location":
                    return f"Cool! {fact_value} is a great place!"
        
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== LEARNING PATTERNS ==========
        next_time_pattern = re.search(r'next time .+? say[s]? ["\']?(.+?)["\']?\s+(?:say|respond with) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            JAIMemory.learn_next_time_say(client_id, trigger, response)
            return f"📚 Got it! When someone says '{trigger}', I'll respond with '{response}'"
        
        teach_pattern = re.search(r'teach ["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(1).strip()
            response = teach_pattern.group(2).strip()
            JAIMemory.teach_response(client_id, trigger, response)
            return f"✅ Learned! '{trigger}' -> '{response}'"
        
        # ========== GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            return f"Good morning{', ' + user_name if user_name else ''}! 🌅"
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            return f"Good afternoon{', ' + user_name if user_name else ''}! 🌞"
        if any(g in msg for g in ["good evening", "evening"]):
            return f"Good evening{', ' + user_name if user_name else ''}! 🌙"
        if any(g in msg for g in ["good night", "night"]):
            return "Good night! 🌙"
        
        if any(g in msg for g in ["hi", "hello", "hey", "howdy"]):
            if user_name:
                return f"Hello {user_name}! 😊 How can I help?"
            return "Hello! 😊 Ask me anything! I can search online, read documents, check weather, or convert currency."
        
        # ========== HOW ARE YOU ==========
        if any(h in msg for h in ["how are you", "how you doing"]):
            return "I'm doing great! Thanks for asking!"
        
        # ========== THANKS ==========
        if any(t in msg for t in ["thank", "thanks"]):
            return "You're welcome! 😊"
        
        # ========== GOODBYE ==========
        if any(g in msg for g in ["bye", "goodbye", "see you"]):
            return "Goodbye! Take care! 👋"
        
        # ========== CREATOR ==========
        if any(c in msg for c in ["who made you", "who created you"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬"
        
        # ========== CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "help"]):
            doc_status = ""
            if DocumentHandler.has_document(client_id):
                doc = DocumentHandler.get_user_document(client_id)
                doc_status = f"\n\n📄 **Document loaded:** '{doc['filename']}'"
            return f"📚 **I can help with:**\n\n🔍 **Search online** - Ask any question\n📄 **Read documents** - Upload PDF/DOCX/TXT\n🌤️ **Weather** - Current conditions\n💰 **Currency** - Live exchange rates\n🧮 **Calculate** - Math problems\n💾 **Memory** - I learn from you!{doc_status}"
        
        # ========== JOKES ==========
        if any(j in msg for j in ["joke", "funny"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾"
            ]
            return random.choice(jokes)
        
        # ========== MOTIVATION ==========
        if any(m in msg for m in ["motivate me", "inspire me"]):
            return JAIGrammarLong.build_long_motivation()
        
        # ========== INTENT & CASUAL ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        casual = JAICasual.get_casual_response(original_message)
        if casual:
            return casual
        
        natural = JAINatural.get_natural_response(original_message)
        if natural:
            return natural
        
        conv = JAIConversational.get_response(original_message)
        if conv:
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
        
        return random.choice(fallbacks)