"""JAI - Gemini AI Integration
Uses Google's Gemini API for true language understanding.
"""

import google.generativeai as genai
import os

class JAIGemini:
    """Gemini-powered intelligence for JAI"""
    
    _model = None
    
    @classmethod
    def initialize(cls, api_key=None):
        """Initialize Gemini with API key"""
        key = api_key or os.getenv('GEMINI_API_KEY')
        if not key:
            return False
        
        genai.configure(api_key=key)
        cls._model = genai.GenerativeModel('gemini-1.5-flash')
        return True
    
    @classmethod
    def generate_response(cls, message, context=""):
        """Generate a response using Gemini"""
        if not cls._model:
            return None
        
        prompt = f"""You are JAI, a friendly AI companion created by Joshua Giwa from Yukuben, Nigeria.
You're warm, encouraging, and you talk like a real friend.
You understand Nigerian context, slang, and culture.

Current context: {context[:500] if context else "No specific context"}

User: {message}

JAI (friendly and helpful):"""
        
        try:
            response = cls._model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini error: {e}")
            return None