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
        """Search online using Wikipedia API"""
        try:
            # Clean the query - remove question words
            clean_query = query.lower()
            for word in ['who is', 'what is', 'where is', 'when is', 'why is', 'how to', 
                        'tell me about', 'explain', 'define', 'what are', 'who was']:
                if clean_query.startswith(word):
                    clean_query = clean_query[len(word):].strip()
            
            # Remove question mark
            clean_query = clean_query.replace('?', '').strip()
            
            # Format for Wikipedia - replace spaces with underscore
            page_title = clean_query.replace(' ', '_')
            
            # Try Wikipedia API
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}'
            logger.info(f"Searching Wikipedia: {url}")
            
            response = requests.get(url, timeout=10, headers={'User-Agent': 'JAI-Bot/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    # Clean up the extract
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    extract = ' '.join(extract.split())
                    if len(extract) > 50:
                        logger.info(f"Found Wikipedia page for: {clean_query}")
                        return extract
            
            # If exact page not found, try search
            search_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(" ", "_")}'
            search_response = requests.get(search_url, timeout=10)
            
            if search_response.status_code == 200:
                data = search_response.json()
                if data.get('extract'):
                    return data['extract']
            
            return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    @classmethod
    def should_search(cls, message):
        """Determine if message should trigger web search"""
        msg_lower = message.lower().strip()
        
        # Question words that trigger search
        question_triggers = [
            'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define'
        ]
        
        for trigger in question_triggers:
            if msg_lower.startswith(trigger):
                logger.info(f"Search triggered by: {trigger}")
                return True
        
        # If message ends with question mark
        if message.strip().endswith('?'):
            logger.info("Search triggered by question mark")
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
                    city = re.sub(r'[^\w\s]', '', city)
            return cls.get_weather(city)
        return None


# ========== CALCULATION MODULE ==========
class Calculator:
    """Handle mathematical calculations"""
    
    @staticmethod
    def calculate(expr):
        try:
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