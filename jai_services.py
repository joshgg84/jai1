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
    """Fast and efficient web search with disambiguation"""
    
    # Track ambiguous queries that need clarification
    _pending_clarifications = {}
    
    @classmethod
    def search_online(cls, query):
        """Quick search using Wikipedia API with disambiguation support"""
        if not query:
            return None
            
        try:
            # FIRST: Check if this is a clarification response
            clarification_result = cls._check_clarification_response(query)
            if clarification_result:
                return clarification_result
            
            # Clean the query - extract the main subject
            clean_query = cls._extract_subject(query)
            if not clean_query or len(clean_query) < 3:
                return None
            
            logger.info(f"Original query: {query}")
            logger.info(f"Extracted subject: {clean_query}")
            
            # Check for ambiguous terms
            ambiguous_result = cls._check_ambiguity(clean_query, query)
            if ambiguous_result:
                return ambiguous_result
            
            # Try Wikipedia directly
            result = cls._search_wikipedia(clean_query)
            if result:
                return result
            
            return None
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return None
    
    @classmethod
    def _check_clarification_response(cls, message):
        """Check if user is responding to a pending clarification"""
        if not message:
            return None
            
        message_lower = message.lower().strip()
        
        # Clean up old pending clarifications (older than 2 minutes)
        current_time = datetime.now()
        to_delete = []
        for key, data in cls._pending_clarifications.items():
            if (current_time - data.get('timestamp', current_time)).seconds > 120:
                to_delete.append(key)
        for key in to_delete:
            del cls._pending_clarifications[key]
        
        # Check each pending clarification
        for query_hash, pending in list(cls._pending_clarifications.items()):
            options = pending.get('options', [])
            
            # Check if user replied with a number
            if message_lower.isdigit():
                num = int(message_lower)
                if 1 <= num <= len(options):
                    selected = options[num - 1]
                    del cls._pending_clarifications[query_hash]
                    result = cls._search_wikipedia(selected['search'])
                    if result:
                        return result
                    return f"Here's what I found about {selected['name']}: {cls._search_wikipedia(selected['search'])}"
            
            # Check if user replied with text matching any option
            for option in options:
                option_name_lower = option['name'].lower()
                
                # Direct match or partial match
                if (message_lower in option_name_lower or 
                    option_name_lower in message_lower):
                    del cls._pending_clarifications[query_hash]
                    result = cls._search_wikipedia(option['search'])
                    if result:
                        return result
                    return f"Here's what I found about {option['name']}: {cls._search_wikipedia(option['search'])}"
                
                # Extract keywords from parentheses like (programming language)
                paren_match = re.search(r'\(([^)]+)\)', option['name'])
                if paren_match:
                    keyword = paren_match.group(1).lower()
                    if keyword in message_lower or message_lower in keyword:
                        del cls._pending_clarifications[query_hash]
                        result = cls._search_wikipedia(option['search'])
                        if result:
                            return result
                        return f"Here's what I found about {option['name']}: {cls._search_wikipedia(option['search'])}"
        
        return None
    
    @classmethod
    def _check_ambiguity(cls, term, original_query):
        """Check if term is ambiguous and ask for clarification"""
        if not term:
            return None
            
        # Convert to lowercase for matching
        term_lower = term.lower()
        
        # Known ambiguous terms
        ambiguous_terms = {
            'python': [
                {'name': 'Python (programming language)', 'search': 'Python programming language'},
                {'name': 'Python (snake)', 'search': 'Python snake'}
            ],
            'java': [
                {'name': 'Java (programming language)', 'search': 'Java programming language'},
                {'name': 'Java (island)', 'search': 'Java island'},
                {'name': 'Java (coffee)', 'search': 'Java coffee'}
            ],
            'spring': [
                {'name': 'Spring (season)', 'search': 'Spring season'},
                {'name': 'Spring (framework)', 'search': 'Spring Framework'}
            ],
            'apple': [
                {'name': 'Apple (company)', 'search': 'Apple Inc'},
                {'name': 'Apple (fruit)', 'search': 'Apple fruit'}
            ],
            'amazon': [
                {'name': 'Amazon (company)', 'search': 'Amazon.com'},
                {'name': 'Amazon (rainforest)', 'search': 'Amazon rainforest'}
            ],
            'windows': [
                {'name': 'Windows (operating system)', 'search': 'Microsoft Windows'},
                {'name': 'Windows (glass)', 'search': 'Window glass'}
            ],
            'table': [
                {'name': 'Table (furniture)', 'search': 'Table furniture'},
                {'name': 'Table (database)', 'search': 'Database table'}
            ],
            'bank': [
                {'name': 'Bank (financial)', 'search': 'Bank'},
                {'name': 'Bank (river)', 'search': 'Bank river'}
            ],
            'cricket': [
                {'name': 'Cricket (sport)', 'search': 'Cricket sport'},
                {'name': 'Cricket (insect)', 'search': 'Cricket insect'}
            ]
        }
        
        # Check if this term is ambiguous
        if term_lower in ambiguous_terms:
            # Create a hash key from the original query
            query_hash = original_query.lower().strip()
            
            # Check if we already asked
            if query_hash in cls._pending_clarifications:
                return None
            
            # Store pending clarification
            cls._pending_clarifications[query_hash] = {
                'options': ambiguous_terms[term_lower],
                'timestamp': datetime.now()
            }
            
            # Build options text
            options_text = "\n".join([f"• {i+1}. {opt['name']}" for i, opt in enumerate(ambiguous_terms[term_lower])])
            return f"🔍 **Which {term} do you mean?**\n\n{options_text}\n\nReply with the number (e.g., '1') or name."
        
        return None
    
    @classmethod
    def _extract_subject(cls, query):
        """Extract the main subject from a question"""
        if not query:
            return ""
            
        original_query = query
        query_lower = query.lower().strip()
        
        # Remove question mark
        query = query.replace('?', '').strip()
        
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
            'can you tell me about', 'do you know'
        ]
        
        # Remove the question prefix
        for pattern in question_patterns:
            if query_lower.startswith(pattern):
                query = query[len(pattern):].strip()
                break
        
        # If query is too short, get last word
        if len(query) < 3:
            words = query_lower.split()
            if words:
                query = words[-1]
        
        # For short ambiguous terms, keep as lowercase for matching
        if query.lower() in ['python', 'java', 'spring', 'apple', 'amazon', 'windows']:
            return query.lower()
        
        # Capitalize first letter
        if query and not query[0].isdigit():
            query = query[0].upper() + query[1:]
        
        return query
    
    @classmethod
    def _search_wikipedia(cls, term):
        """Search Wikipedia for a term"""
        if not term:
            return None
            
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
                    extract = cls._clean_extract(data['extract'])
                    return extract
            
            # Try search API
            search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={term}&format=json'
            search_response = requests.get(search_url, timeout=8)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get('query', {}).get('search'):
                    first_result = search_data['query']['search'][0]['title']
                    logger.info(f"Search found: {first_result}")
                    
                    page_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{first_result.replace(" ", "_")}'
                    page_response = requests.get(page_url, timeout=8)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if page_data.get('extract'):
                            extract = cls._clean_extract(page_data['extract'])
                            return extract
            
            return None
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    @classmethod
    def _clean_extract(cls, extract):
        """Clean and truncate Wikipedia extract"""
        if not extract:
            return ""
        # Remove parentheticals
        extract = re.sub(r'\([^)]*\)', '', extract)
        # Clean up whitespace
        extract = ' '.join(extract.split())
        # Limit length
        if len(extract) > 800:
            extract = extract[:800] + "..."
        return extract
    
    @classmethod
    def should_search(cls, message):
        """Quick check if message needs web search"""
        if not message:
            return False
            
        msg = message.lower().strip()
        
        # Check for question patterns
        question_patterns = [
            'who created', 'who made', 'who invented', 'who discovered',
            'who founded', 'who is', 'who was', 'who are',
            'what is', 'what was', 'what are', 'what does',
            'where is', 'where was', 'where are',
            'when is', 'when was', 'when did',
            'why is', 'why was', 'why did',
            'how to', 'how do', 'how does',
            'tell me about', 'explain', 'define'
        ]
        
        for pattern in question_patterns:
            if pattern in msg:
                logger.info(f"Search triggered by: {pattern}")
                return True
        
        # Check for question mark
        if '?' in msg:
            logger.info("Search triggered by question mark")
            return True
        
        return False


# ========== FAST CACHE ==========
_search_cache = {}
_cache_duration = 3600

def get_cached_search(query):
    """Get cached search result"""
    if not query:
        return None
    key = query.lower().strip()
    if key in _search_cache:
        cache_time = _search_cache[key]['time']
        if (datetime.now() - cache_time).seconds < _cache_duration:
            return _search_cache[key]['result']
    return None

def cache_search_result(query, result):
    """Cache search result"""
    if not query:
        return
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