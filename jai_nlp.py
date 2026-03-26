"""JAI - Natural Language Processing
Handles word formation, grammar, sentiment, and language understanding.
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
    """NLP processor for JAI"""
    
    # Vowels and consonants for word formation
    VOWELS = set('aeiou')
    CONSONANTS = set('bcdfghjklmnpqrstvwxyz')
    
    # Common Nigerian slang and phrases
    NIGERIAN_SLANG = {
        "how far": "how are you",
        "wetin": "what",
        "abeg": "please",
        "na wa": "that's surprising",
        "wahala": "trouble",
        "dey": "is/are",
        "sabi": "know",
        "chop": "eat",
        "money dey": "there's money",
        "no wahala": "no problem",
        "naija": "nigeria",
        "comot": "leave",
        "shey": "is it",
        "oga": "boss",
        "mumu": "foolish"
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
        """Check if a word contains a vowel"""
        return any(char in JAINLP.VOWELS for char in word.lower())
    
    @staticmethod
    def count_syllables(word):
        """Count syllables in a word (basic rule-based)"""
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
    def get_part_of_speech(word):
        """Get part of speech for a word"""
        blob = TextBlob(word)
        if blob.tags:
            return blob.tags[0][1]
        return None
    
    @staticmethod
    def analyze_sentence(sentence):
        """Analyze sentence structure and return comprehensive analysis"""
        if not sentence:
            return None
        
        blob = TextBlob(sentence)
        
        # Get sentiment
        sentiment = blob.sentiment
        
        # Determine emotion based on polarity
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
            'is_greeting': any(g in sentence.lower() for g in ['hi', 'hello', 'hey', 'howdy']),
            'is_thanks': any(t in sentence.lower() for t in ['thank', 'thanks', 'appreciate'])
        }
    
    @staticmethod
    def generate_word_from_pattern(pattern):
        """Generate a word following a pattern (C=consonant, V=vowel)"""
        word = ""
        for char in pattern:
            if char == 'C':
                word += random.choice(list(JAINLP.CONSONANTS))
            elif char == 'V':
                word += random.choice(list(JAINLP.VOWELS))
            else:
                word += char
        return word
    
    @staticmethod
    def is_valid_word_formation(word):
        """Check if a word follows basic vowel-consonant patterns"""
        if len(word) < 2:
            return True
        
        # A word must have at least one vowel
        if not JAINLP.has_vowel(word):
            return False
        
        # No more than 3 consonants in a row
        cons_count = 0
        for char in word.lower():
            if char in JAINLP.CONSONANTS:
                cons_count += 1
                if cons_count > 3:
                    return False
            else:
                cons_count = 0
        
        return True
    
    @staticmethod
    def extract_intent(message):
        """Extract user intent from message"""
        msg = message.lower()
        blob = TextBlob(message)
        
        # Check for questions
        if '?' in msg:
            if any(w in msg for w in ['time', 'clock']):
                return 'ask_time'
            if any(w in msg for w in ['date', 'day', 'today']):
                return 'ask_date'
            if any(w in msg for w in ['calculate', 'math', 'plus', 'minus', 'multiply', 'divide']):
                return 'ask_calculation'
            if any(w in msg for w in ['who', 'creator', 'made you', 'built you']):
                return 'ask_creator'
            if any(w in msg for w in ['what can you', 'capabilities', 'do you do']):
                return 'ask_capabilities'
            return 'ask_general'
        
        # Check for greetings
        if any(g in msg for g in ['hi', 'hello', 'hey', 'howdy', 'sup', 'yo']):
            return 'greeting'
        
        # Check for thanks
        if any(t in msg for t in ['thank', 'thanks', 'appreciate']):
            return 'thanks'
        
        # Check for goodbye
        if any(b in msg for b in ['bye', 'goodbye', 'see you', 'later']):
            return 'goodbye'
        
        # Check for emotions
        sentiment = blob.sentiment.polarity
        if sentiment > 0.3:
            return 'positive_emotion'
        elif sentiment < -0.3:
            return 'negative_emotion'
        
        return 'general_chat'
    
    @staticmethod
    def extract_keywords(message, top_n=3):
        """Extract most important keywords from message"""
        blob = TextBlob(message)
        # Remove stop words (simple approach)
        stop_words = {'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'is', 'am', 'are', 
                      'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'this', 'that', 'with', 'from', 'by', 'as', 'of', 'was', 'were', 'be'}
        
        words = [w.lower() for w in blob.words if w.lower() not in stop_words and len(w) > 2]
        word_counts = Counter(words)
        return [w for w, _ in word_counts.most_common(top_n)]