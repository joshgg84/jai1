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
            clean_query = cls._extract_subject(query)
            if not clean_query or len(clean_query) < 3:
                return None
            
            logger.info(f"Original query: {query}")
            logger.info(f"Extracted subject: {clean_query}")
            
            result = cls._search_wikipedia(clean_query)
            if result:
                return result
            
            return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    @classmethod
    def _extract_subject(cls, query):
        """Extract the main subject from a question - handles messy input"""
        if not query:
            return ""
        
        # Clean up the query first
        query = query.strip()
        # Remove multiple question marks
        query = re.sub(r'\?{2,}', '?', query)
        # Remove trailing question mark for processing
        query_without_q = query.rstrip('?').strip()
        
        query_lower = query_without_q.lower()
        
        # Handle "capital of X" patterns specially
        capital_match = re.search(r'capital of\s+([A-Za-z\s]+)', query_lower)
        if capital_match:
            country = capital_match.group(1).strip()
            return f"Capital of {country.title()}"
        
        # Handle "population of X" patterns
        population_match = re.search(r'population of\s+([A-Za-z\s]+)', query_lower)
        if population_match:
            place = population_match.group(1).strip()
            return f"Population of {place.title()}"
        
        # Handle "currency of X" patterns
        currency_match = re.search(r'currency of\s+([A-Za-z\s]+)', query_lower)
        if currency_match:
            place = currency_match.group(1).strip()
            return f"Currency of {place.title()}"
        
        # List of question patterns to remove
        question_patterns = [
            'who created', 'who made', 'who invented', 'who discovered',
            'who founded', 'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define',
            'can you tell me about', 'do you know',
            'can you', 'could you', 'please tell me',
            'i want to know about', 'what\'s', 'who\'s',
            'capital of', 'population of', 'area of', 'currency of'
        ]
        
        # Remove the question prefix
        for pattern in question_patterns:
            if query_lower.startswith(pattern):
                query_without_q = query_without_q[len(pattern):].strip()
                break
        
        # If nothing left, try to get the last meaningful word
        if len(query_without_q) < 2:
            words = query_lower.split()
            if words:
                query_without_q = words[-1]
        
        # Capitalize first letter for Wikipedia
        if query_without_q and not query_without_q[0].isdigit():
            query_without_q = query_without_q[0].upper() + query_without_q[1:]
        
        return query_without_q
    
    @classmethod
    def _search_wikipedia(cls, term):
        """Search Wikipedia for a term"""
        try:
            formatted_term = term.replace(' ', '_')
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_term}'
            
            response = requests.get(url, timeout=8, headers={'User-Agent': 'JAI/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    extract = ' '.join(extract.split())
                    if len(extract) > 600:
                        extract = extract[:600] + "..."
                    return extract
            
            # Try search API if direct page fails
            search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={term}&format=json'
            search_response = requests.get(search_url, timeout=8)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('query', {}).get('search'):
                    first_result = search_data['query']['search'][0]['title']
                    page_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{first_result.replace(" ", "_")}'
                    page_response = requests.get(page_url, timeout=8)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if page_data.get('extract'):
                            extract = page_data['extract']
                            extract = re.sub(r'\([^)]*\)', '', extract)
                            extract = ' '.join(extract.split())
                            if len(extract) > 600:
                                extract = extract[:600] + "..."
                            return extract
            
            return None
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    @classmethod
    def should_search(cls, message):
        """Quick check if message needs web search"""
        if not message:
            return False
            
        msg = message.lower().strip()
        
        question_patterns = [
            'who created', 'who made', 'who invented', 'who discovered',
            'who founded', 'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define',
            'capital of', 'population of'
        ]
        
        for pattern in question_patterns:
            if pattern in msg:
                return True
        
        if '?' in msg:
            return True
        
        return False


# ========== FAST CACHE ==========
_search_cache = {}
_cache_duration = 3600

def get_cached_search(query):
    key = query.lower().strip()
    if key in _search_cache:
        cache_time = _search_cache[key]['time']
        if (datetime.now() - cache_time).seconds < _cache_duration:
            return _search_cache[key]['result']
    return None

def cache_search_result(query, result):
    key = query.lower().strip()
    _search_cache[key] = {
        'result': result,
        'time': datetime.now()
    }


# ========== WEATHER MODULE ==========
class Weather:
    @classmethod
    def get_weather(cls, city=None):
        if not city:
            city = "Lagos"
        
        try:
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
        if not message:
            return None
        msg_lower = message.lower()
        
        if 'weather' in msg_lower or 'temperature' in msg_lower:
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
    @staticmethod
    def calculate(expr):
        try:
            if not expr:
                return None
            expr = expr.replace('plus', '+').replace('minus', '-')
            expr = expr.replace('times', '*').replace('divided by', '/')
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            result = eval(expr)
            return f"🧮 {expr} = {result}"
        except:
            return None
    
    @staticmethod
    def should_calculate(message):
        if not message:
            return False
        msg_lower = message.lower()
        return any(op in msg_lower for op in ["+", "-", "*", "/", "%", "calculate"])


# ========== TIME MODULE ==========
class TimeService:
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
        if not message:
            return False
        msg_lower = message.lower()
        return "time" in msg_lower or "date" in msg_lower


# ========== GENERAL KNOWLEDGE DETECTION ==========
class GeneralKnowledge:
    @staticmethod
    def is_general_question(question):
        if not question:
            return False
            
        q_lower = question.lower()
        
        patterns = [
            r'who created', r'who made', r'who invented', r'who discovered',
            r'who founded', r'who is', r'who was', r'who are',
            r'what is', r'what was', r'what are', r'what does',
            r'where is', r'where was', r'where are',
            r'when is', r'when was', r'when did',
            r'why is', r'why was', r'why did',
            r'how to', r'how do', r'how does',
            r'tell me about', r'explain', r'define',
            r'capital of', r'population of'
        ]
        
        for pattern in patterns:
            if re.search(pattern, q_lower):
                return True
        
        if question.strip().endswith('?'):
            return True
        
        return False