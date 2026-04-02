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
    """Search online for factual questions - no API key needed"""
    
    _search_cache = {}
    
    @classmethod
    def search_online(cls, query):
        """Search online using free APIs"""
        cache_key = query.lower().strip()
        
        # Check cache (5 minute cache)
        if cache_key in cls._search_cache:
            cache_time = cls._search_cache[cache_key]['time']
            if (datetime.now() - cache_time).seconds < 300:
                return cls._search_cache[cache_key]['result']
        
        try:
            # Try DuckDuckGo API first
            encoded_query = requests.utils.quote(query)
            url = f'https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1'
            response = requests.get(url, timeout=8, headers={'User-Agent': 'JAI-Bot/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                
                # Get the abstract or definition
                result = None
                if data.get('AbstractText'):
                    result = data['AbstractText']
                elif data.get('Definition'):
                    result = data['Definition']
                elif data.get('Answer'):
                    result = data['Answer']
                
                if result and len(result) > 10:
                    # Cache result
                    cls._search_cache[cache_key] = {
                        'result': result,
                        'time': datetime.now()
                    }
                    return result
            
            # Try Wikipedia as fallback
            wiki_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}'
            wiki_response = requests.get(wiki_url, timeout=8)
            
            if wiki_response.status_code == 200:
                wiki_data = wiki_response.json()
                if wiki_data.get('extract'):
                    result = wiki_data['extract']
                    cls._search_cache[cache_key] = {
                        'result': result,
                        'time': datetime.now()
                    }
                    return result
                    
        except Exception as e:
            logger.warning(f"Search failed: {e}")
        
        return None
    
    @classmethod
    def should_search(cls, message):
        """Determine if message should trigger web search"""
        msg_lower = message.lower()
        
        # Question words that indicate factual query
        question_triggers = [
            'what is', 'who is', 'where is', 'when is', 'why is', 'how to',
            'tell me about', 'explain', 'define', 'meaning of', 'what are',
            'who was', 'what does', 'how does', 'why do', 'when did'
        ]
        
        for trigger in question_triggers:
            if trigger in msg_lower:
                return True
        
        # Questions with question mark and more than 3 words
        if '?' in message and len(message.split()) > 3:
            # Don't search for personal/greeting questions
            personal_patterns = ['how are you', 'how you doing', 'what about you']
            if not any(p in msg_lower for p in personal_patterns):
                return True
        
        return False


# ========== WEATHER MODULE ==========
class Weather:
    """Get weather information for any city"""
    
    @classmethod
    def get_weather(cls, city=None):
        """Get current weather for a city"""
        if not city:
            city = "Lagos"
        
        try:
            # Using wttr.in - free weather service
            url = f"https://wttr.in/{city}?format=%C:+%t,+%w,+%h&m"
            response = requests.get(url, timeout=8)
            
            if response.status_code == 200:
                weather_data = response.text.strip()
                if weather_data and not weather_data.startswith('Unknown'):
                    return f"🌤️ **Weather in {city.title()}**\n{weather_data}"
        except Exception as e:
            logger.warning(f"Weather lookup failed: {e}")
        
        return None
    
    @classmethod
    def detect_weather_query(cls, message):
        """Detect if user is asking about weather"""
        msg_lower = message.lower()
        
        weather_keywords = ['weather', 'temperature', 'forecast', 'raining', 'sunny', 'cloudy', 'hot', 'cold']
        
        if any(keyword in msg_lower for keyword in weather_keywords):
            # Extract city name
            city = None
            
            # Pattern: "weather in Lagos"
            if 'in' in msg_lower:
                parts = msg_lower.split('in')
                if len(parts) > 1:
                    city = parts[1].strip().split()[0]
                    city = re.sub(r'[^\w\s]', '', city)
            
            # Pattern: "Lagos weather"
            if not city:
                words = message.split()
                for i, word in enumerate(words):
                    if word.lower() in weather_keywords and i > 0:
                        city = words[i-1]
                        break
                    elif word.lower() in weather_keywords and i < len(words)-1:
                        city = words[i+1]
                        break
            
            return cls.get_weather(city)
        
        return None


# ========== CALCULATION MODULE ==========
class Calculator:
    """Handle mathematical calculations"""
    
    @staticmethod
    def calculate(expr):
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            return f"🧮 {expr} = {eval(expr)}"
        except:
            return None
    
    @staticmethod
    def should_calculate(message):
        """Check if message contains calculation request"""
        msg_lower = message.lower()
        return any(op in msg_lower for op in ["+", "-", "*", "/", "%", "calculate", "what is"])


# ========== TIME MODULE ==========
class TimeService:
    """Handle time and date queries"""
    
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