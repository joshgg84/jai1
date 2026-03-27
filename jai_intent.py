"""JAI - Intent Detection and Handling
All intent patterns and response handlers in one place.
Uses grammar engine for dynamic sentence building.
"""

import random
import re
from datetime import datetime
from jai_grammar import JAIGrammar

class JAIIntent:
    """Intent detection and response generation"""
    
    # Intent patterns for detection
    INTENT_PATTERNS = {
        # Basic intents
        'greeting': [
            r'\b(hi|hello|hey|howdy|sup|yo|good morning|good afternoon|good evening)\b',
            r'\b(what\'s up|wassup|howdy)\b'
        ],
        'how_are_you': [
            r'how (are you|you doing|you feeling|your day)',
            r'how\'s (it going|your day|life)',
            r'what\'s (up|good|happening)'
        ],
        'how_are_you_followup': [
            r'(i\'m|i am) (fine|good|great|okay|alright|doing well)',
            r'(doing|feeling) (good|great|okay|fine)'
        ],
        'thanks': [
            r'\b(thank|thanks|appreciate|grateful)\b'
        ],
        'goodbye': [
            r'\b(bye|goodbye|see you|later|catch you|peace)\b'
        ],
        'ask_creator': [
            r'(who|what) (created|made|built) you',
            r'who is your (creator|maker)',
            r'who are you'
        ],
        'ask_capabilities': [
            r'what can you (do|help with)',
            r'what are your (skills|abilities|features)',
            r'what do you do'
        ],
        'ask_time': [
            r'what (time|hour) (is it|now)',
            r'current time'
        ],
        'ask_date': [
            r'what (date|day) (is it|today)',
            r'today\'s date'
        ],
        'ask_calculation': [
            r'\d+[\+\-\*/%]',
            r'(calculate|what is|how much is)',
            r'(\d+) (plus|minus|times|divided by) (\d+)'
        ],
        'ask_currency': [
            r'(\d+)\s*(usd|dollar|eur|euro|gbp|pound)\s*(to|in)\s*(ngn|naira)',
            r'convert .* to naira'
        ],
        
        # Enhanced intents
        'ask_weather': [
            r'weather (today|tomorrow|now)',
            r'how is the weather',
            r'is it (raining|sunny|cloudy|hot|cold)',
            r'what\'s the (weather|temperature)',
            r'will it rain'
        ],
        'ask_news': [
            r'(what|any) news',
            r'what\'s (happening|going on)',
            r'tell me (news|updates)',
            r'what\'s new (in|around)',
            r'any (breaking|latest) news'
        ],
        'ask_motivation': [
            r'motivate me',
            r'give me (motivation|encouragement)',
            r'i need (motivation|encouragement)',
            r'inspire me',
            r'give me (hope|strength)',
            r'help me keep going'
        ],
        'ask_advice': [
            r'what should i (do|know|learn)',
            r'give me advice',
            r'what do you (think|recommend)',
            r'what would you do',
            r'need (advice|help)',
            r'help me decide'
        ],
        'ask_life': [
            r'what is the (meaning|purpose) of life',
            r'why am i here',
            r'what is life about',
            r'what\'s the point of life',
            r'why do we exist',
            r'what is the secret to life'
        ],
        'ask_love': [
            r'what is love',
            r'how to (find|get) love',
            r'relationship advice',
            r'how do i know if (she|he) loves me',
            r'how to (get|find) a girlfriend',
            r'how to (get|find) a boyfriend',
            r'advice for relationships'
        ],
        'ask_work': [
            r'how to (get|find) a job',
            r'career advice',
            r'what job should i (do|take)',
            r'how to make money',
            r'how to (succeed|excel) at work',
            r'career path'
        ],
        'ask_study': [
            r'how to (learn|study)',
            r'best way to (learn|study)',
            r'what should i learn',
            r'how to (memorize|remember)',
            r'study tips',
            r'how to focus'
        ],
        'ask_dreams': [
            r'what is your (dream|goal)',
            r'what do you (want|dream)',
            r'what are your (aspirations|goals)',
            r'what do you hope to become',
            r'what is your purpose'
        ],
        'ask_about_creator': [
            r'who is (joshua|giwa)',
            r'tell me about (joshua|your creator)',
            r'where is (joshua|your creator) from',
            r'who made you',
            r'tell me about the person who made you'
        ],
        'ask_nigeria': [
            r'(nigeria|naija|lagos|abuja)',
            r'what do you think about nigeria',
            r'tell me about nigeria',
            r'how is nigeria',
            r'nigerian (culture|food|music)'
        ],
        'ask_joke': [
            r'(tell|say) (a|some) joke',
            r'make me laugh',
            r'funny (story|thing)',
            r'tell me something funny'
        ],
        'ask_fact': [
            r'(tell|give) me a fact',
            r'interesting fact',
            r'did you know',
            r'say something interesting'
        ],
        'positive_emotion': [
            r'(happy|excited|great|wonderful|amazing|blessed|grateful)',
            r'i feel (good|great|happy|excited)',
            r'i\'m (so|very) (happy|excited)',
            r'this is (awesome|fantastic)'
        ],
        'negative_emotion': [
            r'(sad|depressed|lonely|tired|stressed|angry|frustrated|overwhelmed|anxious)',
            r'i feel (bad|down|sad|tired)',
            r'i\'m (not|feeling) (good|well|okay)',
            r'this is (hard|difficult)'
        ]
    }
    
    @staticmethod
    def get_response(intent, context=None):
        """Generate response using grammar engine"""
        
        # ========== BASIC INTENTS ==========
        
        if intent == 'greeting':
            return JAIGrammar.build_greeting()
        
        if intent == 'how_are_you':
            return JAIGrammar.build_how_are_you()
        
        if intent == 'thanks':
            return JAIGrammar.get_thanks()
        
        if intent == 'goodbye':
            return JAIGrammar.get_goodbye()
        
        if intent == 'ask_creator':
            return JAIGrammar.build_simple_response('creator')
        
        if intent == 'ask_capabilities':
            return JAIGrammar.build_capabilities()
        
        if intent == 'ask_time':
            return JAIGrammar.get_time()
        
        if intent == 'ask_date':
            return JAIGrammar.get_date()
        
        if intent == 'ask_calculation':
            return "Yes! 🧮 I can calculate anything. Just ask me like 'What's 15% of 200?' or '4+4'. What do you want to calculate?"
        
        if intent == 'ask_currency':
            return "Yes! 💰 I can convert USD, EUR, GBP to NGN. Just say something like '100 USD to NGN'. What do you want to convert?"
        
        # ========== ENHANCED INTENTS ==========
        
        if intent == 'ask_weather':
            return JAIGrammar.build_simple_response('weather')
        
        if intent == 'ask_news':
            return JAIGrammar.build_simple_response('news')
        
        if intent == 'ask_motivation':
            return JAIGrammar.build_motivation()
        
        if intent == 'ask_advice':
            return JAIGrammar.build_advice()
        
        if intent == 'ask_life':
            return JAIGrammar.build_simple_response('life')
        
        if intent == 'ask_love':
            return JAIGrammar.build_simple_response('love')
        
        if intent == 'ask_work':
            return JAIGrammar.build_simple_response('work')
        
        if intent == 'ask_study':
            return JAIGrammar.build_simple_response('study')
        
        if intent == 'ask_dreams':
            return JAIGrammar.build_simple_response('dreams')
        
        if intent == 'ask_about_creator':
            return JAIGrammar.build_simple_response('creator')
        
        if intent == 'ask_nigeria':
            return JAIGrammar.build_simple_response('nigeria')
        
        if intent == 'ask_joke':
            return JAIGrammar.build_joke()
        
        if intent == 'ask_fact':
            return JAIGrammar.build_fact()
        
        if intent == 'positive_emotion':
            return JAIGrammar.build_response_with_emotion('positive')
        
        if intent == 'negative_emotion':
            return JAIGrammar.build_response_with_emotion('negative')
        
        # ========== FOLLOW-UP RESPONSES ==========
        
        if intent == 'how_are_you_followup':
            return JAIGrammar.build_follow_up()
        
        return None