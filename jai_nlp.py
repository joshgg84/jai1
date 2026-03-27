"""JAI - Natural Language Processing
Enhanced with advanced intent detection and sentence formation rules.
"""

import os
import re
import random
import nltk
from textblob import TextBlob
from collections import Counter
from jai_intent import JAIIntent

# ========== NLTK DATA SETUP ==========
# Set up NLTK data directory
NLTK_DATA_DIR = os.path.join(os.path.dirname(__file__), 'nltk_data')
os.makedirs(NLTK_DATA_DIR, exist_ok=True)
nltk.data.path.insert(0, NLTK_DATA_DIR)

# Download required NLTK data
def download_nltk_data():
    resources = {
        'punkt': 'tokenizers/punkt',
        'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger',
        'wordnet': 'corpora/wordnet',
        'brown': 'corpora/brown'
    }
    
    for name, path in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"Downloading {name}...")
            nltk.download(name, download_dir=NLTK_DATA_DIR)

download_nltk_data()

class JAINLP:
    """Enhanced NLP processor for JAI"""
    
    VOWELS = set('aeiou')
    CONSONANTS = set('bcdfghjklmnpqrstvwxyz')
    
    # Nigerian slang dictionary
    NIGERIAN_SLANG = {
        "how far": "how are you",
        "wetin": "what",
        "abeg": "please",
        "na wa": "that is surprising",
        "wahala": "trouble",
        "dey": "is are",
        "sabi": "know",
        "chop": "eat",
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
        """Extract user intent using JAIIntent patterns"""
        msg_lower = message.lower().strip()
        
        # Check for single-word clarification
        if msg_lower in ['wat', 'what', 'huh', 'eh', 'say', 'repeat']:
            return 'ask_clarification'
        
        for intent, patterns in JAIIntent.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        return 'general_chat'
    
    @staticmethod
    def extract_keywords(message, top_n=3):
        """Extract most important keywords from message"""
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
        tags = blob.tags
        
        subjects = []
        verbs = []
        
        for word, tag in tags:
            if tag.startswith('NN') or tag == 'PRP':
                subjects.append(word)
            elif tag.startswith('VB'):
                verbs.append(word)
        
        return {
            'has_subject': len(subjects) > 0,
            'has_verb': len(verbs) > 0,
            'subjects': subjects,
            'verbs': verbs,
            'structure': 'complete' if subjects and verbs else 'incomplete'
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
        
        if not JAINLP.has_vowel(word):
            return False
        
        cons_count = 0
        for char in word.lower():
            if char in JAINLP.CONSONANTS:
                cons_count += 1
                if cons_count > 3:
                    return False
            else:
                cons_count = 0
        
        return True