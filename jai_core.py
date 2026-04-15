"""JAI - Core Personality Module
Main response generation orchestrating all services.
Routes to Document Server, Casual Server, and Data Analyzer.
"""

import random
import re
import logging
import os
import requests
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
from jai_professional_writer import ProfessionalWriterHandler
from jai_creative_writer import CreativeWriterHandler
from jai_user_handler import UserHandler
from jai_formatter import TextFormatter

logger = logging.getLogger(__name__)

# Microservice URLs (set these as environment variables on Render)
DOCUMENT_SERVER_URL = os.environ.get('DOCUMENT_SERVER_URL', 'https://jai-document.onrender.com')
CASUAL_SERVER_URL = os.environ.get('CASUAL_SERVER_URL', 'https://jai-casual.onrender.com')
DATA_ANALYZER_URL = os.environ.get('DATA_ANALYZER_URL', 'https://jai-data-analyzer.onrender.com')


class MicroserviceClient:
    """Handle communication with microservices"""
    
    @staticmethod
    def call_document_server(endpoint, data, timeout=60):
        """Call document intelligence server"""
        try:
            response = requests.post(
                f"{DOCUMENT_SERVER_URL}{endpoint}",
                json=data,
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Document server error: {e}")
            return None
    
    @staticmethod
    def call_casual_server(message, client_id, user_name=None):
        """Call casual chat server"""
        try:
            response = requests.post(
                f"{CASUAL_SERVER_URL}/api/casual",
                json={
                    'message': message,
                    'clientId': client_id,
                    'userName': user_name
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('response')
            return None
        except Exception as e:
            logger.error(f"Casual server error: {e}")
            return None
    
    @staticmethod
    def call_data_analyzer(endpoint, data, timeout=60):
        """Call data analyzer server"""
        try:
            response = requests.post(
                f"{DATA_ANALYZER_URL}{endpoint}",
                json=data,
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Data analyzer error: {e}")
            return None


class JAIPersonality:
    """Main JAI personality orchestrating all features"""
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title="", client_id="unknown"):
        """Main response generator"""
        msg = message.lower().strip()
        original_message = message
        
        # ========== HANDLE FEATURE ENTRY (Page navigation) ==========
        if msg.startswith('entering '):
            feature_name = message[9:].strip()
            JAIMemory.set_current_feature(client_id, feature_name)
            response = f"📱 Welcome to {feature_name}! How can I help you?"
            JAIMemory.save_conversation(client_id, original_message, response)
            return TextFormatter.format_all(response)
        
        # ========== DOCUMENT UPLOAD COMMAND - Route to Document Server ==========
        if msg.startswith('upload_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    filename = parts[1].strip()
                    base64_content = parts[2].strip()
                    
                    # Call Document Server
                    result = MicroserviceClient.call_document_server(
                        '/api/upload',
                        {
                            'filename': filename,
                            'content': base64_content,
                            'clientId': client_id
                        },
                        timeout=60
                    )
                    
                    if result and result.get('success'):
                        JAIMemory.save_conversation(client_id, original_message, f"Document uploaded: {filename}")
                        response = f"✅ **Document uploaded successfully!**\n\n{result.get('summary', '')}"
                        return TextFormatter.format_all(response)
                    else:
                        error = result.get('error', 'Upload failed') if result else 'Document server unavailable'
                        return f"❌ {error}"
                else:
                    return "❌ Invalid upload format. Please use the upload button."
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return f"❌ Error: {str(e)}"
        
        # ========== DOCUMENT INTELLIGENCE - Route to Document Server ==========
        current_feature = JAIMemory.get_current_feature(client_id)
        if current_feature and 'Document Intelligence' in current_feature:
            # Check if document is loaded on server
            result = MicroserviceClient.call_document_server(
                '/api/ask',
                {
                    'clientId': client_id,
                    'question': original_message
                },
                timeout=30
            )
            if result and result.get('answer'):
                JAIMemory.save_conversation(client_id, original_message, result['answer'])
                return TextFormatter.format_all(result['answer'])
        
        # ========== DATA ANALYSIS - Route to Data Analyzer ==========
        if current_feature and 'Data Analyzer' in current_feature or msg.startswith('analyze data:'):
            result = MicroserviceClient.call_data_analyzer(
                '/api/analyze',
                {
                    'clientId': client_id,
                    'question': original_message
                },
                timeout=30
            )
            if result and result.get('answer'):
                JAIMemory.save_conversation(client_id, original_message, result['answer'])
                return TextFormatter.format_all(result['answer'])
        
        # ========== GET USER MEMORY FACTS ==========
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== CASUAL RESPONSES - Route to Casual Server ==========
        # Check if this is a casual message (not a command or question)
        is_casual = not any([
            msg.startswith('upload_'),
            '?' in msg,
            any(word in msg for word in ['what', 'who', 'where', 'when', 'why', 'how', 'explain', 'summarize', 'convert', 'weather', 'time', 'date']),
            any(word in msg for word in ['write', 'create', 'generate', 'make', 'draft']),
            any(word in msg for word in ['my name is', 'i am', 'i\'m'])
        ])
        
        if is_casual and len(msg) < 50:
            casual_response = MicroserviceClient.call_casual_server(original_message, client_id, user_name)
            if casual_response:
                JAIMemory.save_conversation(client_id, original_message, casual_response)
                return TextFormatter.format_all(casual_response)
        
        # ========== NAME EXTRACTION ==========
        name_extraction_patterns = [
            r'my name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'i am\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'i\'m\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'call me\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)',
            r'name is\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)'
        ]
        
        invalid_names = [
            'yes', 'no', 'ok', 'okay', 'good', 'bad', 'fine', 'great', 'awesome',
            'hello', 'hi', 'hey', 'bye', 'thanks', 'thank', 'please', 'sorry',
            'confused', 'tired', 'happy', 'sad', 'angry', 'excited', 'bored',
            'explain', 'summarize', 'describe', 'tell', 'show', 'give'
        ]
        
        for pattern in name_extraction_patterns:
            name_match = re.search(pattern, msg, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip().title()
                if (extracted_name.isalpha() and 
                    len(extracted_name) >= 2 and 
                    extracted_name.lower() not in invalid_names):
                    JAIMemory.save_user_fact(client_id, 'name', extracted_name)
                    user_name = extracted_name
                    response = f"Nice to meet you, {extracted_name}! 😊 I'll remember your name."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return TextFormatter.format_all(response)
        
        # ========== NAME QUESTION DETECTION ==========
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
                    response = f"Your name is {user_name}! 😊 I remember you."
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return TextFormatter.format_all(response)
                else:
                    response = "I don't know your name yet. Please tell me: 'My name is [your name]' and I'll remember it! 😊"
                    JAIMemory.save_conversation(client_id, original_message, response)
                    return TextFormatter.format_all(response)
        
        # ========== CREATIVE WRITER ==========
        if CreativeWriterHandler.is_creative_request(original_message):
            creative_response = CreativeWriterHandler.handle_creative_request(original_message)
            if creative_response:
                JAIMemory.save_conversation(client_id, original_message, creative_response)
                return TextFormatter.format_all(creative_response)
        
        # ========== PROFESSIONAL WRITER ==========
        if ProfessionalWriterHandler.is_writing_request(original_message):
            writing_response = ProfessionalWriterHandler.handle_writing_request(original_message)
            if writing_response:
                JAIMemory.save_conversation(client_id, original_message, writing_response)
                return TextFormatter.format_all(writing_response)
        
        # ========== CURRENCY CONVERSION ==========
        currency_result = JAICurrency.detect_and_convert(original_message)
        if currency_result:
            JAIMemory.save_conversation(client_id, original_message, currency_result)
            return TextFormatter.format_all(currency_result)
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(original_message)
        if weather_response:
            JAIMemory.save_conversation(client_id, original_message, weather_response)
            return TextFormatter.format_all(weather_response)
        
        # ========== CALCULATIONS ==========
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                JAIMemory.save_conversation(client_id, original_message, calc_result)
                return TextFormatter.format_all(calc_result)
        
        has_numbers = len(re.findall(r'\d+', original_message)) >= 2
        has_math_op = any(op in msg for op in ['+', '-', '*', '/', '%'])
        if has_numbers and has_math_op:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                JAIMemory.save_conversation(client_id, original_message, calc_result)
                return TextFormatter.format_all(calc_result)
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            time_response = TimeService.get_time()
            JAIMemory.save_conversation(client_id, original_message, time_response)
            return TextFormatter.format_all(time_response)
        if "date" in msg:
            date_response = TimeService.get_date()
            JAIMemory.save_conversation(client_id, original_message, date_response)
            return TextFormatter.format_all(date_response)
        
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
            r'please explain', r'help me understand',
            r'capital of', r'population of', r'currency of'
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
        
        if len(clean_msg) < 50 and has_question_mark:
            is_general_knowledge = True
        
        if is_general_knowledge:
            logger.info(f"Searching online for: {original_message}")
            search_result = WebSearch.search_online(original_message)
            if search_result:
                JAIMemory.save_conversation(client_id, original_message, search_result)
                return TextFormatter.format_all(search_result)
        
        # ========== LOCAL CASUAL FALLBACK (if microservice fails) ==========
        casual_response = JAICasual.get_casual_response(original_message, user_name)
        if casual_response:
            JAIMemory.save_conversation(client_id, original_message, casual_response)
            return TextFormatter.format_all(casual_response)
        
        # ========== INTENT & NATURAL ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            JAIMemory.save_conversation(client_id, original_message, intent_response)
            return TextFormatter.format_all(intent_response)
        
        natural = JAINatural.get_natural_response(original_message)
        if natural:
            JAIMemory.save_conversation(client_id, original_message, natural)
            return TextFormatter.format_all(natural)
        
        conv = JAIConversational.get_response(original_message)
        if conv:
            JAIMemory.save_conversation(client_id, original_message, conv)
            return TextFormatter.format_all(conv)
        
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
        return TextFormatter.format_all(response)