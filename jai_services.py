"""JAI - Services Module
Contains web search, weather, and other external service integrations.
"""

import re
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


# ========== WEB SEARCH MODULE ==========
class WebSearch:
    """Search online for factual questions"""
    
    @classmethod
    def search_online(cls, query):
        """Search online using DuckDuckGo API"""
        try:
            encoded_query = requests.utils.quote(query)
            url = f'https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1'
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code == 200:
                data = response.json()
                
                # Try to get AbstractText first
                if data.get('AbstractText'):
                    return data['AbstractText']
                
                # Try Definition
                if data.get('Definition'):
                    return data['Definition']
                
                # Try Answer
                if data.get('Answer'):
                    return data['Answer']
                
                # Try RelatedTopics
                if data.get('RelatedTopics'):
                    for topic in data['RelatedTopics']:
                        if isinstance(topic, dict) and topic.get('Text'):
                            text = topic['Text']
                            if len(text) > 50:
                                return text
                
                return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    @classmethod
    def should_search(cls, message):
        """Determine if message should trigger web search"""
        msg_lower = message.lower().strip()
        
        # Question words that should ALWAYS trigger search
        question_triggers = [
            'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does', 'what do',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did', 'why do',
            'how to', 'how do', 'how does', 'how is',
            'tell me about', 'explain', 'define', 'meaning of',
            'capital of', 'population of', 'president of'
        ]
        
        for trigger in question_triggers:
            if msg_lower.startswith(trigger) or trigger in msg_lower:
                return True
        
        # If message ends with question mark and has content
        if message.strip().endswith('?'):
            return True
        
        return False


# ========== WEATHER MODULE ==========
class Weather:
    """Get weather information"""
    
    @classmethod
    def get_weather(cls, city=None):
        """Get current weather for a city"""
        if not city:
            city = "Lagos"
        
        try:
            url = f"https://wttr.in/{city}?format=%C:+%t,+%w,+%h&m"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                weather_data = response.text.strip()
                if weather_data and not weather_data.startswith('Unknown'):
                    return f"🌤️ Weather in {city.title()}: {weather_data}"
        except Exception as e:
            logger.warning(f"Weather failed: {e}")
        
        return None
    
    @classmethod
    def detect_weather_query(cls, message):
        """Detect weather question"""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['weather', 'temperature', 'forecast']):
            city = None
            if 'in' in msg_lower:
                parts = msg_lower.split('in')
                if len(parts) > 1:
                    city = parts[1].strip().split()[0]
            return cls.get_weather(city)
        return None


# ========== CALCULATION MODULE ==========
class Calculator:
    """Handle mathematical calculations"""
    
    @staticmethod
    def calculate(expr):
        try:
            # Clean the expression
            expr = expr.replace('plus', '+').replace('minus', '-')
            expr = expr.replace('times', '*').replace('divided by', '/')
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            result = eval(expr)
            return f"🧮 {expr} = {result}"
        except:
            return None
    
    @staticmethod
    def should_calculate(message):
        msg_lower = message.lower()
        return any(op in msg_lower for op in ["+", "-", "*", "/", "%", "calculate"])


# ========== TIME MODULE ==========
class TimeService:
    """Handle time and date"""
    
    @staticmethod
    def get_time():
        now = datetime.now()
        return f"🕐 The time is {now.strftime('%I:%M %p')}"
    
    @staticmethod
    def get_date():
        now = datetime.now()
        return f"📅 Today is {now.strftime('%A, %B %d, %Y')}"
    
    @staticmethod
    def should_respond(message):
        msg_lower = message.lower()
        return "time" in msg_lower or "date" in msg_lower