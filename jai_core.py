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
        
        # Command to upload document via base64
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
                        doc_id = DocumentHandler.store_document(filename, text, simplified)
                        
                        return f"✅ **Document uploaded!**\n\n" \
                               f"📄 **{filename}**\n" \
                               f"📊 {len(text)} characters\n" \
                               f"📝 Preview: \"{preview}\"\n\n" \
                               f"{simplified}\n\n" \
                               f"**ID:** `{doc_id}`\n\n" \
                               f"💡 **Now ask me anything about this document!** Just type your question naturally."
                    else:
                        return "❌ File appears empty or unreadable. Please check the file and try again."
                else:
                    return "❌ Invalid upload format. Please use the upload button."
            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return f"❌ Error: {str(e)}"
        
        # Command to ask about a document
        if msg.startswith('ask_doc:'):
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    doc_id = parts[1].strip()
                    question = parts[2].strip()
                    
                    if len(question) < 3:
                        return "💡 **Please ask a specific question** about your document.\n\nExamples:\n• What is this document about?\n• Summarize the key points\n• Tell me about [specific topic]"
                    
                    answer = DocumentHandler.answer_question(doc_id, question)
                    if answer:
                        return answer
                    else:
                        return f"❌ Document not found. Please upload a document first using the upload button."
            except Exception as e:
                logger.error(f"Document question error: {e}")
                return "❌ Error processing your question. Please try again."
        
        # ========== WEATHER ==========
        weather_response = Weather.detect_weather_query(original_message)
        if weather_response:
            JAIMemory.save_conversation(client_id, original_message, weather_response)
            return weather_response
        
        # ========== WEB SEARCH ==========
        # Check for questions that should trigger web search
        is_question = '?' in original_message
        starts_with_question = original_message.lower().startswith(('who ', 'what ', 'where ', 'when ', 'why ', 'how '))
        
        if is_question or starts_with_question:
            search_result = WebSearch.search_online(original_message)
            if search_result:
                response = f"🔍 {search_result}"
                JAIMemory.save_conversation(client_id, original_message, response)
                return response
        
        # ========== MEMORY ==========
        
        # Check for "next time say" patterns
        next_time_response = JAIMemory.get_next_time_say_response(client_id, original_message)
        if next_time_response:
            return next_time_response
        
        # Check taught responses
        taught_response = JAIMemory.get_taught_response(client_id, original_message)
        if taught_response:
            return taught_response
        
        # Extract and save user facts
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, original_message)
        if learned_facts:
            for fact_key, fact_value in learned_facts:
                if fact_key == "name":
                    return f"Nice to meet you, {fact_value}! I'll remember that. 😊"
                elif fact_key == "age":
                    return f"Got it! You're {fact_value} years old!"
                elif fact_key == "location":
                    return f"Cool! {fact_value} is a great place!"
        
        # Get user facts for personalization
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== LEARNING PATTERNS ==========
        
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
        
        # ========== CALCULATIONS ==========
        
        # Percent calculations
        percent_match = re.search(r'(\d+)\s*percent\s*of\s*(\d+)', msg)
        if percent_match:
            calc_result = Calculator.calculate(original_message)
            if calc_result:
                return calc_result
        
        # Math with numbers
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
        
        # ========== GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            return f"Good morning{', ' + user_name if user_name else ''}! 🌅 Hope you have a great day!"
        
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            return f"Good afternoon{', ' + user_name if user_name else ''}! 🌞 How's your day going?"
        
        if any(g in msg for g in ["good evening", "evening"]):
            return f"Good evening{', ' + user_name if user_name else ''}! 🌙 Hope you had a productive day!"
        
        if any(g in msg for g in ["good night", "night"]):
            return "Good night! 🌙 Rest well. Tomorrow is another chance!"
        
        if any(g in msg for g in ["hi", "hello", "hey", "howdy"]):
            if user_name:
                return f"Hello {user_name}! 😊 How can I help you today?\n\n📄 Upload a document\n🔍 Ask a question\n💬 Just chat"
            return "Hello! 😊 I can help you with:\n\n📄 **Documents** - Upload PDF/DOCX/TXT\n🔍 **Search** - Ask me anything\n🌤️ **Weather** - Check conditions\n💰 **Currency** - Live rates\n\nWhat would you like?"
        
        # ========== HOW ARE YOU ==========
        if any(h in msg for h in ["how are you", "how you doing", "how's it going"]):
            return "I'm doing great! Thanks for asking. How about you?"
        
        # ========== THANKS ==========
        if any(t in msg for t in ["thank", "thanks", "thx"]):
            return "You're welcome! 😊 Happy to help!"
        
        # ========== GOODBYE ==========
        if any(g in msg for g in ["bye", "goodbye", "see you", "later"]):
            return "Goodbye! Take care and come back anytime! 👋"
        
        # ========== CREATOR ==========
        if any(c in msg for c in ["who made you", "who created you", "your creator"]):
            return "I was created by **Joshua Giwa** from Yukuben Village, Nigeria! 🇳🇬 He built me to help people understand documents and answer questions."
        
        # ========== CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "capabilities", "help", "features"]):
            return "📚 **JAI's Capabilities**\n\n" \
                   "📄 **Document Intelligence**\n• Upload PDF, DOCX, or TXT files\n• I'll simplify and explain them\n• Ask questions about your documents\n\n" \
                   "🔍 **Web Search**\n• Answer factual questions\n• Find information online\n\n" \
                   "🌤️ **Weather**\n• Current conditions anywhere\n• Temperature and forecasts\n\n" \
                   "💰 **Currency**\n• Live exchange rates\n• Convert between currencies\n\n" \
                   "🧮 **Calculator**\n• Math calculations\n• Percentages and more\n\n" \
                   "💾 **Memory**\n• I remember what you teach me\n• Learn your preferences\n\n" \
                   "**Try uploading a document to get started!**"
        
        # ========== JOKES ==========
        if any(j in msg for j in ["joke", "funny", "make me laugh"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "What do you call a Nigerian who knows cyber security? A Nai-ja breaker! 😂"
            ]
            return random.choice(jokes)
        
        # ========== MOTIVATION ==========
        if any(m in msg for m in ["motivate me", "inspire me", "give me motivation", "encourage me"]):
            return JAIGrammarLong.build_long_motivation()
        
        # ========== INTENT DETECTION ==========
        intent = JAINLP.extract_intent(original_message)
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        # ========== CASUAL RESPONSES ==========
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
            "How does that make you feel?",
            "That's a good point. What do you think?",
            "I'm here for you. What would you like to talk about?"
        ]
        
        # Personalize fallback if we know user's name
        if user_name:
            personalized_fallbacks = [
                f"What's on your mind, {user_name}?",
                f"Tell me more about that, {user_name}.",
                f"How are you feeling about that, {user_name}?",
                f"That's interesting, {user_name}. What else?"
            ]
            fallbacks.extend(personalized_fallbacks)
        
        return random.choice(fallbacks)