"""JAI - Gemini AI Integration
Uses Google's Gemini API for true language understanding.
"""

import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

class JAIGemini:
    """Gemini-powered intelligence for JAI"""
    
    _model = None
    _initialized = False
    
    @classmethod
    def initialize(cls, api_key=None):
        """Initialize Gemini with API key"""
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key:
            logger.warning("No Gemini API key provided")
            return False
        
        try:
            genai.configure(api_key=key)
            cls._model = genai.GenerativeModel('gemini-1.5-flash')
            cls._initialized = True
            return True
        except Exception as e:
            logger.error(f"Gemini init error: {e}")
            return False
    
    @classmethod
    def generate_response(cls, message, context=""):
        """Generate a response using Gemini"""
        if not cls._initialized or not cls._model:
            return None
        
        prompt = f"""You are JAI, a friendly AI companion created by Joshua Giwa from Yukuben, Nigeria.
You're warm, encouraging, and you talk like a real friend.
You understand Nigerian context, slang, and culture.
Keep responses concise but meaningful.

User: {message}

JAI (friendly and helpful):"""
        
        try:
            response = cls._model.generate_content(prompt)
            text = response.text.strip()
            # Clean up if needed
            if text.startswith('JAI:'):
                text = text[4:].strip()
            return text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return None