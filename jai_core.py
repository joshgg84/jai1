"""JAI - Core Personality Module
Main response generation with memory, services, and conversation logic.
"""

import random
import re
import logging
import base64
import tempfile
import os
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

# Try to import document processing
try:
    import PyPDF2
    import docx
    DOCUMENT_SUPPORT = True
except ImportError:
    DOCUMENT_SUPPORT = False
    logger.warning("Document processing libraries not installed")

# Store documents in memory (will be cleared on restart)
_documents = {}


class DocumentHandler:
    """Handle document upload and processing through chat"""
    
    @staticmethod
    def extract_text_from_base64(base64_content, filename):
        """Extract text from base64 encoded file"""
        try:
            # Decode base64
            file_content = base64.b64decode(base64_content)
            file_ext = filename.split('.')[-1].lower()
            
            if file_ext == 'txt':
                return file_content.decode('utf-8')
            
            elif file_ext == 'pdf' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                text = ""
                with open(tmp_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                
                os.unlink(tmp_path)
                return text
            
            elif file_ext == 'docx' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                doc = docx.Document(tmp_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                os.unlink(tmp_path)
                return text
            
            return None
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return None
    
    @staticmethod
    def simplify_document(text, filename):
        """Generate simplified version"""
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Detect document type
        text_lower = text.lower()
        if any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party', 'hereby']):
            doc_type = "legal"
            intro = "📄 **Legal Document Simplified**\n\n"
        elif any(word in text_lower for word in ['exam', 'test', 'question', 'student']):
            doc_type = "educational"
            intro = "📚 **Educational Content Simplified**\n\n"
        else:
            doc_type = "general"
            intro = "📄 **Document Simplified**\n\n"
        
        # Get key sentences
        sentences = re.split(r'[.!?]+', text)
        key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        
        simplified = intro
        simplified += f"**Original document:** {filename}\n\n"
        simplified += f"**Key points from this document:**\n\n"
        
        for point in key_points:
            simplified += f"• {point}\n\n"
        
        if doc_type == "legal":
            simplified += "\n**Important Notes:**\n• This document contains legal terms\n• Read carefully before signing\n• Ask questions about anything unclear"
        elif doc_type == "educational":
            simplified += "\n**Study Tips:**\n• Review these key points\n• Take notes on important concepts\n• Ask me questions about specific topics"
        
        return simplified, doc_type
    
    @staticmethod
    def answer_document_question(doc_id, question):
        """Answer questions about a document"""
        if doc_id not in _documents:
            return None
        
        doc = _documents[doc_id]
        content = doc['content']
        
        # Simple keyword matching
        question_lower = question.lower()
        keywords = re.findall(r'\b\w+\b', question_lower)
        keywords = [k for k in keywords if len(k) > 3 and k not in ['what', 'does', 'this', 'that', 'tell', 'about']]
        
        for keyword in keywords[:3]:
            if keyword in content.lower():
                sentences = re.split(r'[.!?]+', content)
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return f"📖 **About '{keyword}':**\n{sentence.strip()}\n\nAnything else you'd like to know about this document?"
        
        return f"📄 **From the document:**\n\n{content[:400]}...\n\nDoes that answer your question? I can explain further."


class JAIPersonality:
    """Main JAI personality with memory and services"""
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title="", client_id="unknown"):
        """Main response generator"""
        msg = message.lower().strip()
        
        # ========== DOCUMENT INTELLIGENCE COMMANDS ==========
        
        # Command to upload document via base64
        if msg.startswith('upload_doc:'):
            try:
                # Format: upload_doc:filename.json_base64_content
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    filename = parts[1].strip()
                    base64_content = parts[2].strip()
                    
                    # Extract text from document
                    text = DocumentHandler.extract_text_from_base64(base64_content, filename)
                    
                    if text:
                        # Simplify document
                        simplified, doc_type = DocumentHandler.simplify_document(text, filename)
                        
                        # Store document
                        doc_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        _documents[doc_id] = {
                            'filename': filename,
                            'content': text,
                            'simplified': simplified,
                            'type': doc_type,
                            'created_at': datetime.now()
                        }
                        
                        return f"✅ **Document uploaded successfully!**\n\n📄 **{filename}**\n\n{simplified}\n\n**Document ID:** `{doc_id}`\n\nYou can now ask questions about this document by saying: `ask_doc:{doc_id}:Your question here`"
                    else:
                        return "❌ Sorry, I couldn't read that document. Please make sure it's a valid TXT, PDF, or DOCX file."
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return "❌ Error processing document. Please check the format and try again."
        
        # Command to ask about a document
        if msg.startswith('ask_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    doc_id = parts[1].strip()
                    question = parts[2].strip()
                    
                    answer = DocumentHandler.answer_document_question(doc_id, question)
                    if answer:
                        return answer
                    else:
                        return "❌ Document not found. Please check the document ID or upload the document first."
            except Exception as e:
                logger.error(f"Document question error: {e}")
                return "❌ Error processing your question. Please try again."
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(message)
        if weather_response:
            JAIMemory.save_conversation(client_id, message, weather_response)
            return weather_response
        
        # ========== WEB SEARCH ==========
        has_question_mark = '?' in message
        has_question_word = any(msg.startswith(word) for word in ['who', 'what', 'where', 'when', 'why', 'how'])
        
        if has_question_mark or has_question_word:
            search_result = WebSearch.search_online(message)
            if search_result:
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, message, response)
                return response
        
        # ========== CHECK MEMORY ==========
        next_time_response = JAIMemory.get_next_time_say_response(client_id, message)
        if next_time_response:
            return next_time_response
        
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
        
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== LEARNING PATTERNS ==========
        next_time_pattern = re.search(r'next time .+? say[s]? ["\']?(.+?)["\']?\s+(?:say|respond with) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            JAIMemory.learn_next_time_say(client_id, trigger, response)
            return f"📚 Got it! Next time someone says '{trigger}', I'll respond with '{response}'"
        
        teach_pattern = re.search(r'teach ["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(1).strip()
            response = teach_pattern.group(2).strip()
            JAIMemory.teach_response(client_id, trigger, response)
            return f"✅ Learned! When you say '{trigger}', I'll respond with '{response}'"
        
        # ========== CALCULATIONS ==========
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(message)
            if calc_result:
                return calc_result
        
        has_numbers = len(re.findall(r'\d+', message)) >= 2
        has_math_op = any(op in msg for op in ['+', '-', '*', '/', '%'])
        if has_numbers and has_math_op:
            calc_result = Calculator.calculate(message)
            if calc_result:
                return calc_result
        
        # ========== CURRENCY ==========
        currency_result = JAICurrency.detect_and_convert(message)
        if currency_result:
            return currency_result
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            return TimeService.get_time()
        if "date" in msg:
            return TimeService.get_date()
        
        # ========== GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            return f"Good morning{', ' + user_name if user_name else ''}! 🌅 Hope you slept well!"
        
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            return f"Good afternoon{', ' + user_name if user_name else ''}! 🌞 How's your day?"
        
        if any(g in msg for g in ["good evening", "evening"]):
            return f"Good evening{', ' + user_name if user_name else ''}! 🌙"
        
        if any(g in msg for g in ["hi", "hello", "hey"]):
            if user_name:
                return f"Hello {user_name}! 😊 How can I help you today?"
            return "Hello! 😊 How can I help you today?"
        
        if any(h in msg for h in ["how are you", "how you doing"]):
            return "I'm doing great! Thanks for asking. How about you?"
        
        if any(t in msg for t in ["thank", "thanks"]):
            return "You're welcome! 😊"
        
        if any(g in msg for g in ["bye", "goodbye", "see you"]):
            return "Goodbye! Take care! 👋"
        
        if any(c in msg for c in ["who made you", "who created you"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬"
        
        if any(c in msg for c in ["what can you do", "your skills"]):
            return "I can: search online 🔍, check weather 🌤️, convert currency 💰, calculate math 🧮, process documents 📄, and remember what you teach me!\n\n📄 **Document features:**\n• Upload: `upload_doc:filename.docx:base64_content`\n• Ask: `ask_doc:doc_id:Your question`"
        
        # ========== JOKES ==========
        if any(j in msg for j in ["joke", "funny", "make me laugh"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾"
            ]
            return random.choice(jokes)
        
        # ========== INTENT & CASUAL ==========
        intent = JAINLP.extract_intent(message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        casual = JAICasual.get_casual_response(message)
        if casual:
            return casual
        
        natural = JAINatural.get_natural_response(message)
        if natural:
            return natural
        
        conv = JAIConversational.get_response(message)
        if conv:
            return conv
        
        # ========== DEFAULT ==========
        fallbacks = [
            "That's interesting. Tell me more!",
            "I hear you. What else is on your mind?",
            "Go on, I'm listening."
        ]
        
        if user_name:
            fallbacks = [
                f"What's on your mind, {user_name}?",
                f"Tell me more about that, {user_name}."
            ]
        
        return random.choice(fallbacks)