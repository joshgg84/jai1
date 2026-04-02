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
        
        # ========== DOCUMENT INTELLIGENCE ==========
        if msg.startswith('upload_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    filename = parts[1].strip()
                    base64_content = parts[2].strip()
                    
                    text = DocumentHandler.extract_text_from_base64(base64_content, filename)
                    
                    if text and len(text.strip()) > 10:
                        preview = text[:200] + "..." if len(text) > 200 else text
                        simplified, doc_type = DocumentHandler.simplify_document(text, filename)
                        doc_id = DocumentHandler.store_document(filename, text, simplified, doc_type)
                        
                        return f"✅ **Document uploaded!**\n\n" \
                               f"📄 {filename}\n" \
                               f"📊 {len(text)} characters\n" \
                               f"📝 Preview: \"{preview}\"\n\n" \
                               f"{simplified}\n\n" \
                               f"**ID:** `{doc_id}`\n\n" \
                               f"💡 Ask me anything about this document!"
                    else:
                        return "❌ File appears empty or unreadable. Try a TXT file with content."
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        if msg.startswith('ask_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    doc_id = parts[1].strip()
                    question = parts[2].strip()
                    answer = DocumentHandler.answer_question(doc_id, question)
                    return answer if answer else "❌ Document not found."
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(original_message)
        if weather_response:
            JAIMemory.save_conversation(client_id, original_message, weather_response)
            return weather_response
        
        # ========== WEB SEARCH ==========
        if '?' in original_message or original_message.lower().startswith(('who ', 'what ', 'where ', 'when ', 'why ', 'how ')):
            search_result = WebSearch.search_online(original_message)
            if search_result:
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, original_message, response)
                return response
        
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
            trigger, response = next_time_pattern.group(1).strip(), next_time_pattern.group(2).strip()
            JAIMemory.learn_next_time_say(client_id, trigger, response)
            return f"📚 Got it! When someone says '{trigger}', I'll respond with '{response}'"
        
        teach_pattern = re.search(r'teach ["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger, response = teach_pattern.group(1).strip(), teach_pattern.group(2).strip()
            JAIMemory.teach_response(client_id, trigger, response)
            return f"✅ Learned! '{trigger}' -> '{response}'"
        
        # ========== CALCULATIONS ==========
        if re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg):
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                return calc_result
        
        if len(re.findall(r'\d+', original_message)) >= 2 and any(op in msg for op in ['+', '-', '*', '/', '%']):
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                return calc_result
        
        # ========== CURRENCY ==========
        currency_result = JAICurrency.detect_and_convert(original_message)
        if currency_result:
            return currency_result
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            return TimeService.get_time()
        if "date" in msg:
            return TimeService.get_date()
        
        # ========== GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            return f"Good morning{', ' + user_name if user_name else ''}! 🌅"
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            return f"Good afternoon{', ' + user_name if user_name else ''}! 🌞"
        if any(g in msg for g in ["good evening", "evening"]):
            return f"Good evening{', ' + user_name if user_name else ''}! 🌙"
        if any(g in msg for g in ["hi", "hello", "hey"]):
            if user_name:
                return f"Hello {user_name}! 😊 How can I help?"
            return "Hello! 😊 Upload a document, ask a question, or just chat!"
        
        # ========== SIMPLE RESPONSES ==========
        if any(h in msg for h in ["how are you", "how you doing"]):
            return "I'm doing great! Thanks for asking!"
        if any(t in msg for t in ["thank", "thanks"]):
            return "You're welcome! 😊"
        if any(g in msg for g in ["bye", "goodbye", "see you"]):
            return "Goodbye! Take care! 👋"
        if any(c in msg for c in ["who made you", "who created you"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬"
        
        # ========== CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "help"]):
            return "📄 **Read documents** - Upload PDF/DOCX/TXT\n🔍 **Search online** - Ask questions\n🌤️ **Weather** - Check anywhere\n💰 **Currency** - Live rates\n🧮 **Calculate** - Math & percentages\n💾 **Memory** - I learn from you!\n\nTry uploading a document!"
        
        # ========== JOKES & MOTIVATION ==========
        if any(j in msg for j in ["joke", "funny"]):
            jokes = ["Why don't scientists trust atoms? Because they make up everything! 😄", "What do you call a fake noodle? An impasta! 🍝", "Why did the scarecrow win an award? He was outstanding in his field! 🌾"]
            return random.choice(jokes)
        
        if any(m in msg for m in ["motivate me", "inspire me"]):
            return JAIGrammarLong.build_long_motivation()
        
        # ========== INTENT & CASUAL ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        for handler in [JAICasual.get_casual_response, JAINatural.get_natural_response, JAIConversational.get_response]:
            response = handler(original_message)
            if response:
                return response
        
        # ========== DEFAULT ==========
        fallbacks = ["That's interesting. Tell me more!", "I hear you. What else is on your mind?", "Go on, I'm listening."]
        if user_name:
            fallbacks = [f"What's on your mind, {user_name}?", f"Tell me more, {user_name}."]
        
        return random.choice(fallbacks)