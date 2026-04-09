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
            # Clean the query - extract the main subject
            clean_query = cls._extract_subject(query)
            if not clean_query or len(clean_query) < 3:
                return None
            
            logger.info(f"Original query: {query}")
            logger.info(f"Extracted subject: {clean_query}")
            
            # Try Wikipedia directly
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
        
        # List of question patterns to remove (expanded)
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
            'i want to know about', 'what\'s', 'who\'s'
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
                # Get the last word (likely the subject)
                query_without_q = words[-1]
        
        # Capitalize first letter for Wikipedia
        if query_without_q and not query_without_q[0].isdigit():
            query_without_q = query_without_q[0].upper() + query_without_q[1:]
        
        return query_without_q
    
    @classmethod
    def _search_wikipedia(cls, term):
        """Search Wikipedia for a term"""
        try:
            # Format the term for URL
            formatted_term = term.replace(' ', '_')
            
            # Try direct page first
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_term}'
            logger.info(f"Wikipedia URL: {url}")
            
            response = requests.get(url, timeout=8, headers={'User-Agent': 'JAI/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    # Remove parentheticals
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    # Clean up whitespace
                    extract = ' '.join(extract.split())
                    # Limit length
                    if len(extract) > 600:
                        extract = extract[:600] + "..."
                    logger.info(f"Found Wikipedia page for: {term}")
                    return extract
            
            # Try search API if direct page fails
            search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={term}&format=json'
            search_response = requests.get(search_url, timeout=8)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('query', {}).get('search'):
                    # Get the first search result
                    first_result = search_data['query']['search'][0]['title']
                    logger.info(f"Search found: {first_result}")
                    
                    # Fetch that page
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
        """Quick check if message needs web search - more flexible"""
        if not message:
            return False
            
        msg = message.lower().strip()
        # Remove excessive question marks
        msg = re.sub(r'\?{2,}', '?', msg)
        
        # Check for question patterns
        question_patterns = [
            'who created', 'who made', 'who invented', 'who discovered',
            'who founded', 'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define',
            'can you', 'could you', 'do you know'
        ]
        
        for pattern in question_patterns:
            if pattern in msg:
                logger.info(f"Search triggered by: {pattern}")
                return True
        
        # Check for question mark (anywhere, not just end)
        if '?' in msg:
            logger.info("Search triggered by question mark")
            return True
        
        # Check if message starts with question words
        question_starts = ['what', 'who', 'where', 'when', 'why', 'how', 'which']
        if any(msg.startswith(word) for word in question_starts):
            logger.info(f"Search triggered by question start word")
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
    """Fast math calculations"""
    
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
        if not message:
            return False
        msg_lower = message.lower()
        return "time" in msg_lower or "date" in msg_lower


# ========== GENERAL KNOWLEDGE DETECTION ==========
class GeneralKnowledge:
    """Detect if question needs web search"""
    
    @staticmethod
    def is_general_question(question):
        """Quick check if this is a general knowledge question"""
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
            r'tell me about', r'explain', r'define'
        ]
        
        for pattern in patterns:
            if re.search(pattern, q_lower):
                return True
        
        if question.strip().endswith('?'):
            return True
        
        return False