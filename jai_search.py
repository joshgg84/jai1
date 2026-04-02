"""JAI - Web Search Module
Searches online for user queries and returns relevant information.
Falls back to JAI's personality responses when no results found.
"""

import requests
import json
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import quote
import random

logger = logging.getLogger(__name__)

class JAISearch:
    """Web search with multiple API fallbacks"""
    
    # Cache search results to reduce API calls
    _search_cache = {}
    _cache_duration = timedelta(hours=6)
    
    # Free search APIs (multiple fallbacks)
    SEARCH_APIS = [
        {
            'name': 'DuckDuckGo',
            'url': 'https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1',
            'parse': lambda data: JAISearch._parse_duckduckgo(data)
        },
        {
            'name': 'Wikipedia',
            'url': 'https://en.wikipedia.org/api/rest_v1/page/summary/{query}',
            'parse': lambda data: JAISearch._parse_wikipedia(data)
        }
    ]
    
    # Keywords that indicate a search is needed
    SEARCH_KEYWORDS = [
        'what is', 'who is', 'where is', 'when is', 'why is', 'how to',
        'tell me about', 'explain', 'define', 'meaning of', 'latest',
        'news about', 'update on', 'current', 'today', 'recent',
        'weather', 'forecast', 'temperature', 'population of',
        'capital of', 'president of', 'ceo of', 'founder of'
    ]
    
    @classmethod
    def should_search(cls, message):
        """Determine if the query should be searched online"""
        msg_lower = message.lower()
        
        # Don't search for very short messages
        if len(message.split()) < 3:
            return False
        
        # Check for search keywords
        for keyword in cls.SEARCH_KEYWORDS:
            if keyword in msg_lower:
                return True
        
        # Check if it's a question
        if '?' in message:
            # Check if it's a factual question (contains who, what, where, etc.)
            question_words = ['who', 'what', 'where', 'when', 'why', 'how']
            if any(word in msg_lower.split()[:3] for word in question_words):
                return True
        
        # Check if it's a specific query (name, place, thing)
        words = message.split()
        if len(words) <= 5 and not any(word in msg_lower for word in ['hello', 'hi', 'hey', 'how are you']):
            return True
        
        return False
    
    @classmethod
    def search_online(cls, query):
        """Search online for the query using available APIs"""
        # Check cache first
        cache_key = query.lower().strip()
        if cache_key in cls._search_cache:
            cache_time = cls._search_cache[cache_key]['time']
            if datetime.now() - cache_time < cls._cache_duration:
                logger.info(f"Using cached search result for: {query}")
                return cls._search_cache[cache_key]['result']
        
        logger.info(f"Searching online for: {query}")
        
        # Try each search API
        for api in cls.SEARCH_APIS:
            try:
                encoded_query = quote(query)
                url = api['url'].format(query=encoded_query)
                
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; JAI-Bot/1.0)'
                })
                
                if response.status_code == 200:
                    data = response.json()
                    result = api['parse'](data)
                    
                    if result and not cls._is_empty_result(result):
                        # Cache the result
                        cls._search_cache[cache_key] = {
                            'result': result,
                            'time': datetime.now()
                        }
                        logger.info(f"✅ Found result from {api['name']}")
                        return result
                        
            except Exception as e:
                logger.warning(f"Search failed for {api['name']}: {e}")
                continue
        
        return None
    
    @classmethod
    def _parse_duckduckgo(cls, data):
        """Parse DuckDuckGo API response"""
        # Check for abstract
        if data.get('AbstractText'):
            return {
                'source': 'DuckDuckGo',
                'title': data.get('Heading', 'Search Result'),
                'content': data.get('AbstractText', ''),
                'url': data.get('AbstractURL', ''),
                'confidence': 0.8
            }
        
        # Check for definition
        if data.get('Definition'):
            return {
                'source': 'DuckDuckGo',
                'title': data.get('Heading', 'Definition'),
                'content': data.get('Definition', ''),
                'url': data.get('DefinitionURL', ''),
                'confidence': 0.7
            }
        
        # Check related topics
        if data.get('RelatedTopics'):
            for topic in data['RelatedTopics']:
                if isinstance(topic, dict) and topic.get('Text'):
                    return {
                        'source': 'DuckDuckGo',
                        'title': topic.get('Text', 'Related Info')[:50],
                        'content': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'confidence': 0.6
                    }
        
        return None
    
    @classmethod
    def _parse_wikipedia(cls, data):
        """Parse Wikipedia API response"""
        if data.get('extract'):
            return {
                'source': 'Wikipedia',
                'title': data.get('title', 'Wikipedia Result'),
                'content': data.get('extract', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'confidence': 0.9
            }
        return None
    
    @classmethod
    def _is_empty_result(cls, result):
        """Check if search result is empty"""
        if not result:
            return True
        content = result.get('content', '')
        if not content or len(content) < 10:
            return True
        return False
    
    @classmethod
    def format_search_response(cls, result, query):
        """Format search result into a nice response"""
        if not result:
            return None
        
        content = result['content']
        source = result['source']
        title = result['title']
        
        # Truncate long content
        if len(content) > 500:
            content = content[:500] + "..."
        
        # Format the response
        formatted = f"🔍 **{title}**\n\n"
        formatted += f"{content}\n\n"
        formatted += f"📌 Source: {source}"
        
        if result.get('url'):
            formatted += f" | 🔗 {result['url']}"
        
        return formatted
    
    @classmethod
    def get_web_search_response(cls, message):
        """Main method to get search response for a user message"""
        # Check if we should search
        if not cls.should_search(message):
            return None
        
        # Try to search online
        search_result = cls.search_online(message)
        
        if search_result:
            return cls.format_search_response(search_result, message)
        
        return None


class JAIWeather:
    """Weather lookup for cities"""
    
    # Free weather API
    WEATHER_API = "https://wttr.in/{city}?format=%C:+%t,+%w,+%h&m"
    
    @classmethod
    def get_weather(cls, city=None):
        """Get weather for a city"""
        if not city:
            city = "Lagos"  # Default city
        
        try:
            url = cls.WEATHER_API.format(city=city)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                weather_data = response.text.strip()
                return f"🌤️ Weather in {city.title()}: {weather_data}"
        except Exception as e:
            logger.warning(f"Weather lookup failed: {e}")
        
        return None
    
    @classmethod
    def detect_weather_query(cls, message):
        """Detect if message is asking for weather"""
        msg_lower = message.lower()
        
        if any(word in msg_lower for word in ['weather', 'temperature', 'forecast', 'raining', 'sunny']):
            # Try to extract city name
            city = None
            words = message.split()
            
            # Look for "weather in [city]" pattern
            if 'in' in msg_lower:
                parts = msg_lower.split('in')
                if len(parts) > 1:
                    city = parts[1].strip().split()[0]
            
            # Look for "weather [city]" pattern
            elif len(words) > 1:
                # Remove common words
                common = ['weather', 'the', 'today', 'like', 'what', 'is']
                for word in words[1:]:
                    if word.lower() not in common and len(word) > 2:
                        city = word
                        break
            
            return cls.get_weather(city)
        
        return None