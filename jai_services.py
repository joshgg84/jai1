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
    """Fast and efficient web search"""
    
    @classmethod
    def search_online(cls, query):
        """Quick search using Wikipedia API"""
        try:
            # Clean the query
            clean_query = cls._clean_query(query)
            if not clean_query or len(clean_query) < 3:
                return None
            
            logger.info(f"Searching: {clean_query}")
            
            # Try Wikipedia directly
            result = cls._search_wikipedia(clean_query)
            if result:
                return result
            
            return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    @classmethod
    def _clean_query(cls, query):
        """Extract the main search term from a question"""
        query_lower = query.lower().strip()
        
        # Remove common question prefixes
        prefixes = [
            'who is', 'who was', 'who are',
            'what is', 'what was', 'what are',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define'
        ]
        
        for prefix in prefixes:
            if query_lower.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        # Remove question mark and extra spaces
        query = query.replace('?', '').strip()
        
        # Capitalize first letter for Wikipedia
        if query:
            query = query[0].upper() + query[1:]
        
        return query
    
    @classmethod
    def _search_wikipedia(cls, term):
        """Search Wikipedia for a term"""
        try:
            # Format the term for URL
            formatted_term = term.replace(' ', '_')
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_term}'
            
            response = requests.get(url, timeout=5, headers={'User-Agent': 'JAI/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    # Get the first paragraph or two
                    extract = data['extract']
                    # Remove parentheticals
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    # Clean up whitespace
                    extract = ' '.join(extract.split())
                    # Limit length
                    if len(extract) > 500:
                        extract = extract[:500] + "..."
                    return extract
            
            return None
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    @classmethod
    def should_search(cls, message):
        """Quick check if message needs web search"""
        msg = message.lower().strip()
        
        # Check for question words at start
        question_starts = ['who', 'what', 'where', 'when', 'why', 'how']
        first_word = msg.split()[0] if msg.split() else ''
        
        if first_word in question_starts:
            return True
        
        # Check for question mark
        if '?' in msg:
            return True
        
        # Check for common question patterns
        question_patterns = ['what is', 'who is', 'where is', 'when is', 'why is', 'how to']
        for pattern in question_patterns:
            if pattern in msg:
                return True
        
        return False


# ========== FAST CACHE ==========
_search_cache = {}
_cache_duration = 3600  # 1 hour

def get_cached_search(query):
    """Get cached search result"""
    key = query.lower().strip()
    if key in _search_cache:
        cache_time = _search_cache[key]['time']
        if (datetime.now() - cache_time).seconds < _cache_duration:
            return _search_cache[key]['result']
    return None

def cache_search_result(query, result):
    """Cache search result"""
    key = query.lower().strip()
    _search_cache[key] = {
        'result': result,
        'time': datetime.now()
    }


# ========== WEATHER MODULE ==========
class Weather:
    """Get weather information quickly"""
    
    @classmethod
    def get_weather(cls, city=None):
        """Get current weather for a city"""
        if not city:
            city = "Lagos"
        
        try:
            # Using wttr.in with simple format
            url = f"https://wttr.in/{city}?format=%C:+%t,+%w,+%h&m"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                weather_data = response.text.strip()
                if weather_data and not weather_data.startswith('Unknown'):
                    return f"🌤️ {city.title()}: {weather_data}"
        except Exception as e:
            logger.warning(f"Weather failed: {e}")
        
        return None
    
    @classmethod
    def detect_weather_query(cls, message):
        """Quick weather detection"""
        msg_lower = message.lower()
        
        if 'weather' in msg_lower or 'temperature' in msg_lower:
            # Extract city
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
    """Fast math calculations"""
    
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
    """Fast time and date"""
    
    @staticmethod
    def get_time():
        now = datetime.now()
        return f"🕐 {now.strftime('%I:%M %p')}"
    
    @staticmethod
    def get_date():
        now = datetime.now()
        return f"📅 {now.strftime('%A, %B %d, %Y')}"
    
    @staticmethod
    def should_respond(message):
        msg_lower = message.lower()
        return "time" in msg_lower or "date" in msg_lower


# ========== GENERAL KNOWLEDGE DETECTION ==========
class GeneralKnowledge:
    """Detect if question needs web search"""
    
    @staticmethod
    def is_general_question(question):
        """Quick check if this is a general knowledge question"""
        q_lower = question.lower()
        
        # Patterns that indicate general knowledge
        patterns = [
            r'who (is|was|created|founded|invented)',
            r'what (is|was|are)',
            r'where (is|was|are)',
            r'when (is|was|did)',
            r'why (is|was|did)',
            r'how (to|do|does|is)',
            r'what does .+ mean',
            r'explain .+',
            r'define .+',
            r'tell me about .+'
        ]
        
        for pattern in patterns:
            if re.search(pattern, q_lower):
                return True
        
        return False