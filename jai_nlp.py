"""JAI - Natural Language Processing
Enhanced with advanced intent detection and sentence formation rules.
"""

import re
import random
import nltk
from textblob import TextBlob
from collections import Counter

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

class JAINLP:
    """Enhanced NLP processor for JAI"""
    
    VOWELS = set('aeiou')
    CONSONANTS = set('bcdfghjklmnpqrstvwxyz')
    
    # Nigerian slang dictionary
    NIGERIAN_SLANG = {
        "how far": "how are you",
        "wetin": "what",
        "abeg": "please",
        "na wa": "that's surprising",
        "wahala": "trouble",
        "dey": "is/are",
        "sabi": "know",
        "chop": "eat",
        "no wahala": "no problem",
        "naija": "nigeria",
        "comot": "leave",
        "shey": "is it",
        "oga": "boss",
        "mumu": "foolish"
    }
    
    # Enhanced intent patterns
    INTENT_PATTERNS = {
        # Greetings
        'greeting': [
            r'\b(hi|hello|hey|howdy|sup|yo|good morning|good afternoon|good evening)\b',
            r'\b(what\'s up|wassup|howdy)\b'
        ],
        # How are you
        'how_are_you': [
            r'how (are you|you doing|you feeling|your day)',
            r'how\'s (it going|your day|life)',
            r'what\'s (up|good|happening)'
        ],
        # Follow-up to "how are you"
        'how_are_you_followup': [
            r'(i\'m|i am) (fine|good|great|okay|alright|doing well)',
            r'(doing|feeling) (good|great|okay|fine)'
        ],
        # Thank you
        'thanks': [
            r'\b(thank|thanks|appreciate|grateful)\b'
        ],
        # Goodbye
        'goodbye': [
            r'\b(bye|goodbye|see you|later|catch you|peace)\b'
        ],
        # Creator questions
        'ask_creator': [
            r'(who|what) (created|made|built) you',
            r'who is your (creator|maker)',
            r'who are you'
        ],
        # Capabilities
        'ask_capabilities': [
            r'what can you (do|help with)',
            r'what are your (skills|abilities|features)',
            r'what do you do'
        ],
        # Time/date
        'ask_time': [
            r'what (time|hour) (is it|now)',
            r'current time'
        ],
        'ask_date': [
            r'what (date|day) (is it|today)',
            r'today\'s date'
        ],
        # Calculation
        'ask_calculation': [
            r'\d+[\+\-\*/%]',
            r'(calculate|what is|how much is)',
            r'(\d+) (plus|minus|times|divided by) (\d+)'
        ],
        # Currency
        'ask_currency': [
            r'(\d+)\s*(usd|dollar|eur|euro|gbp|pound)\s*(to|in)\s*(ngn|naira)',
            r'convert .* to naira'
        ],
        # Weather
        'ask_weather': [
            r'weather (today|tomorrow|now)',
            r'how is the weather',
            r'is it (raining|sunny|cloudy)'
        ],
        # News
        'ask_news': [
            r'(what|any) news',
            r'what\'s happening',
            r'tell me (news|updates)'
        ],
        # Motivation
        'ask_motivation': [
            r'motivate me',
            r'give me (motivation|encouragement)',
            r'i need (motivation|encouragement)',
            r'inspire me'
        ],
        # Advice
        'ask_advice': [
            r'what should i (do|know|learn)',
            r'give me advice',
            r'what do you (think|recommend)'
        ],
        # Life questions
        'ask_life': [
            r'what is the (meaning|purpose) of life',
            r'why am i here',
            r'what is life about'
        ],
        # Love/relationships
        'ask_love': [
            r'what is love',
            r'how to (find|get) love',
            r'relationship advice'
        ],
        # Work/career
        'ask_work': [
            r'how to (get|find) a job',
            r'career advice',
            r'what job should i (do|take)'
        ],
        # Study/learning
        'ask_study': [
            r'how to (learn|study)',
            r'best way to (learn|study)',
            r'what should i learn'
        ],
        # Negative emotions
        'negative_emotion': [
            r'(sad|depressed|lonely|tired|stressed|angry|frustrated|overwhelmed|anxious)',
            r'i feel (bad|down|sad|tired)',
            r'i\'m (not|feeling) (good|well|okay)'
        ],
        # Positive emotions
        'positive_emotion': [
            r'(happy|excited|great|wonderful|amazing|blessed|grateful)',
            r'i feel (good|great|happy|excited)',
            r'i\'m (so|very) (happy|excited)'
        ],
        # Dreams/goals
        'ask_dreams': [
            r'what is your (dream|goal)',
            r'what do you (want|dream)',
            r'what are your (aspirations|goals)'
        ],
        # About Joshua
        'ask_about_creator': [
            r'who is (joshua|giwa)',
            r'tell me about (joshua|your creator)',
            r'where is (joshua|your creator) from'
        ],
        # About Nigeria
        'ask_nigeria': [
            r'(nigeria|naija|lagos|abuja)',
            r'what do you think about nigeria',
            r'tell me about nigeria'
        ],
        # Jokes
        'ask_joke': [
            r'(tell|say) (a|some) joke',
            r'make me laugh',
            r'funny (story|thing)'
        ],
        # Facts
        'ask_fact': [
            r'(tell|give) me a fact',
            r'interesting fact',
            r'did you know'
        ]
    }
    
    @staticmethod
    def normalize_nigerian_slang(text):
        """Convert Nigerian slang to standard English"""
        text_lower = text.lower()
        for slang, standard in JAINLP.NIGERIAN_SLANG.items():
            text_lower = text_lower.replace(slang, standard)
        return text_lower
    
    @staticmethod
    def has_vowel(word):
        return any(char in JAINLP.VOWELS for char in word.lower())
    
    @staticmethod
    def count_syllables(word):
        word = word.lower()
        count = 0
        vowels = 'aeiou'
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index-1] not in vowels:
                count += 1
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count += 1
        return count
    
    @staticmethod
    def analyze_sentence(sentence):
        if not sentence:
            return None
        
        blob = TextBlob(sentence)
        sentiment = blob.sentiment
        
        if sentiment.polarity > 0.3:
            emotion = "positive"
        elif sentiment.polarity < -0.3:
            emotion = "negative"
        else:
            emotion = "neutral"
        
        return {
            'words': [str(w) for w in blob.words],
            'tags': [(str(w), str(t)) for w, t in blob.tags],
            'noun_phrases': [str(np) for np in blob.noun_phrases],
            'sentiment': {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'emotion': emotion
            },
            'word_count': len(blob.words),
            'has_question': '?' in sentence,
            'is_greeting': any(g in sentence.lower() for g in ['hi', 'hello', 'hey']),
            'is_thanks': any(t in sentence.lower() for t in ['thank', 'thanks'])
        }
    
    @staticmethod
    def extract_intent(message):
        """Enhanced intent detection using regex patterns"""
        msg_lower = message.lower()
        
        # Check each intent pattern
        for intent, patterns in JAINLP.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        # Default
        return 'general_chat'
    
    @staticmethod
    def extract_keywords(message, top_n=3):
        blob = TextBlob(message)
        stop_words = {'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'is', 'am', 'are', 
                      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'this', 'that', 'with', 'from', 'by', 'as', 'of', 'was', 'were', 'be',
                      'what', 'why', 'how', 'when', 'where', 'who'}
        
        words = [w.lower() for w in blob.words if w.lower() not in stop_words and len(w) > 2]
        word_counts = Counter(words)
        return [w for w, _ in word_counts.most_common(top_n)]
    
    @staticmethod
    def detect_sentence_structure(sentence):
        """Analyze sentence structure (subject, verb, object)"""
        blob = TextBlob(sentence)
        words = blob.words
        tags = blob.tags
        
        subjects = []
        verbs = []
        objects = []
        
        for i, (word, tag) in enumerate(tags):
            if tag.startswith('NN') or tag == 'PRP':  # Noun or pronoun
                subjects.append(word)
            elif tag.startswith('VB'):  # Verb
                verbs.append(word)
            elif tag.startswith('JJ'):  # Adjective
                pass  # Could be used for descriptions
        
        return {
            'has_subject': len(subjects) > 0,
            'has_verb': len(verbs) > 0,
            'subjects': subjects,
            'verbs': verbs,
            'structure': 'complete' if subjects and verbs else 'incomplete'
        }