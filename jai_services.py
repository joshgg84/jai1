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
            # Extract search term from question
            search_term = query.lower()
            
            # Remove question words
            for word in ['what is', 'who is', 'where is', 'when is', 'why is', 'how to', 
                        'tell me about', 'explain', 'define']:
                if search_term.startswith(word):
                    search_term = search_term[len(word):].strip()
                    break
            
            # Remove question mark
            search_term = search_term.replace('?', '').strip()
            
            # Capitalize first letter for Wikipedia
            search_term = search_term[0].upper() + search_term[1:] if search_term else search_term
            
            logger.info(f"Searching Wikipedia for: {search_term}")
            
            # Try direct Wikipedia API
            encoded_term = search_term.replace(' ', '_')
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_term}'
            
            response = requests.get(url, timeout=10, headers={'User-Agent': 'JAI-Bot/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    # Clean up
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    extract = ' '.join(extract.split())
                    if len(extract) > 50:
                        logger.info(f"Found Wikipedia page for: {search_term}")
                        return extract
            
            # If direct fails, try with first word only
            first_word = search_term.split()[0] if ' ' in search_term else search_term
            if first_word != search_term:
                url2 = f'https://en.wikipedia.org/api/rest_v1/page/summary/{first_word}'
                response2 = requests.get(url2, timeout=10)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('extract'):
                        extract = data2['extract']
                        extract = re.sub(r'\([^)]*\)', '', extract)
                        extract = ' '.join(extract.split())
                        if len(extract) > 50:
                            logger.info(f"Found Wikipedia page for: {first_word}")
                            return extract
            
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
            'how to', 'how do', 'how does'
        ]
        
        for trigger in question_triggers:
            if msg_lower.startswith(trigger):
                return True
        
        # If message ends with question mark
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