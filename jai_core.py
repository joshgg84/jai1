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
from jai_professional_writer import ProfessionalWriterHandler
from jai_creative_writer import CreativeWriterHandler
from jai_user_handler import UserHandler

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
        
        # ========== USER HANDLER (Name, Emotions, Memory) ==========
        user_response = UserHandler.handle_user_message(original_message, client_id)
        if user_response:
            JAIMemory.save_conversation(client_id, original_message, user_response)
            return user_response
        
        # ========== CREATIVE WRITER (Love letters, poems, stories) ==========
        if CreativeWriterHandler.is_creative_request(original_message):
            creative_response = CreativeWriterHandler.handle_creative_request(original_message)
            if creative_response:
                JAIMemory.save_conversation(client_id, original_message, creative_response)
                return creative_response
        
        # ========== PROFESSIONAL WRITER (Emails, proposals, reports) ==========
        if ProfessionalWriterHandler.is_writing_request(original_message):
            writing_response = ProfessionalWriterHandler.handle_writing_request(original_message)
            if writing_response:
                JAIMemory.save_conversation(client_id, original_message, writing_response)
                return writing_response
        
        # ========== CURRENCY CONVERSION (HIGH PRIORITY) ==========
        # Moved to HIGH priority - BEFORE casual responses
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
        
        # ========== CASUAL RESPONSES ==========
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        casual_response = JAICasual.get_casual_response(original_message, user_name)
        if casual_response:
            JAIMemory.save_conversation(client_id, original_message, casual_response)
            return casual_response
        
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
        
        # ========== INTENT & NATURAL ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            JAIMemory.save_conversation(client_id, original_message, intent_response)
            return intent_response
        
        natural = JAINatural.get_natural_response(original_message)
        if natural:
            JAIMemory.save_conversation(client_id, original_message, natural)
            return natural
        
        conv = JAIConversational.get_response(original_message)
        if conv:
            JAIMemory.save_conversation(client_id, original_message, conv)
            return conv
        
        # ========== PROFESSIONAL WRITER FALLBACK ==========
        if any(w in msg for w in ['write', 'draft', 'compose', 'email', 'letter', 'proposal']):
            response = ProfessionalWriterHandler.get_writing_help()
            JAIMemory.save_conversation(client_id, original_message, response)
            return response
        
        # ========== DEFAULT FALLBACK ==========
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
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