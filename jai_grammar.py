"""JAI - Advanced Grammar Engine
Builds sentences using parts of speech and grammar rules.
Generates dynamic, varied responses based on intent and context.
"""

import random
import re
from datetime import datetime

class JAIGrammar:
    """Advanced grammar engine with parts of speech"""
    
    # ========== PARTS OF SPEECH ==========
    
    # Nouns
    NOUNS = {
        'person': ['friend', 'brother', 'sister', 'stranger', 'companion', 'partner'],
        'place': ['world', 'home', 'place', 'space', 'corner', 'room', 'village', 'city'],
        'thing': ['dream', 'goal', 'vision', 'path', 'journey', 'road', 'way'],
        'feeling': ['heart', 'mind', 'soul', 'spirit', 'thought', 'feeling'],
        'time': ['moment', 'day', 'hour', 'minute', 'second', 'time'],
        'concept': ['idea', 'thought', 'truth', 'wisdom', 'knowledge', 'power']
    }
    
    # Verbs
    VERBS = {
        'action': ['build', 'create', 'make', 'do', 'work', 'move', 'grow'],
        'state': ['am', 'is', 'are', 'become', 'remain', 'stay'],
        'feeling': ['feel', 'sense', 'know', 'understand', 'believe', 'trust'],
        'thinking': ['think', 'consider', 'reflect', 'ponder', 'imagine', 'dream'],
        'communication': ['say', 'tell', 'speak', 'share', 'express', 'explain'],
        'movement': ['go', 'come', 'walk', 'run', 'move', 'travel', 'journey']
    }
    
    # Adjectives
    ADJECTIVES = {
        'positive': ['good', 'great', 'wonderful', 'amazing', 'awesome', 'fantastic', 'beautiful', 'powerful'],
        'negative': ['hard', 'tough', 'difficult', 'challenging', 'heavy', 'painful'],
        'neutral': ['interesting', 'curious', 'strange', 'unusual', 'different'],
        'size': ['big', 'small', 'large', 'tiny', 'huge', 'massive', 'miniature'],
        'quality': ['strong', 'weak', 'bright', 'dark', 'sharp', 'dull', 'clear', 'vague']
    }
    
    # Adverbs
    ADVERBS = {
        'manner': ['carefully', 'quickly', 'slowly', 'gently', 'strongly', 'softly', 'loudly'],
        'time': ['now', 'soon', 'later', 'today', 'tomorrow', 'yesterday', 'already', 'still'],
        'frequency': ['always', 'often', 'sometimes', 'rarely', 'never', 'constantly'],
        'degree': ['very', 'quite', 'rather', 'extremely', 'slightly', 'barely', 'completely'],
        'place': ['here', 'there', 'everywhere', 'somewhere', 'nowhere', 'anywhere']
    }
    
    # Pronouns
    PRONOUNS = {
        'subject': ['I', 'you', 'he', 'she', 'it', 'we', 'they'],
        'object': ['me', 'you', 'him', 'her', 'it', 'us', 'them'],
        'possessive': ['my', 'your', 'his', 'her', 'its', 'our', 'their'],
        'reflexive': ['myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves']
    }
    
    # Conjunctions
    CONJUNCTIONS = {
        'coordinating': ['and', 'but', 'or', 'nor', 'for', 'so', 'yet'],
        'subordinating': ['because', 'although', 'if', 'when', 'while', 'since', 'though', 'unless']
    }
    
    # Prepositions
    PREPOSITIONS = {
        'location': ['in', 'on', 'at', 'by', 'near', 'beside', 'behind', 'in front of', 'under', 'over', 'between', 'among'],
        'time': ['before', 'after', 'during', 'since', 'until', 'within', 'throughout', 'around'],
        'direction': ['to', 'towards', 'into', 'through', 'across', 'along', 'around', 'past'],
        'purpose': ['for', 'with', 'by', 'like', 'as', 'about', 'of'],
        'origin': ['from', 'out of', 'off']
    }
    
    # ========== SENTENCE PATTERNS ==========
    
    PATTERNS = {
        'simple': [
            ['subject', 'verb'],
            ['subject', 'verb', 'object'],
            ['subject', 'verb', 'adjective'],
            ['subject', 'verb', 'adverb']
        ],
        'compound': [
            ['subject', 'verb', 'conjunction', 'subject', 'verb'],
            ['subject', 'verb', 'object', 'conjunction', 'verb', 'object']
        ],
        'complex': [
            ['subordinating', 'subject', 'verb', 'subject', 'verb'],
            ['subject', 'verb', 'because', 'subject', 'verb']
        ]
    }
    
    # ========== SENTENCE BUILDING METHODS ==========
    
    @staticmethod
    def get_random_word(category, subcategory=None):
        """Get a random word from a category"""
        if subcategory and subcategory in JAIGrammar.NOUNS:
            return random.choice(JAIGrammar.NOUNS[subcategory])
        if category == 'noun':
            all_nouns = []
            for nouns in JAIGrammar.NOUNS.values():
                all_nouns.extend(nouns)
            return random.choice(all_nouns)
        if category == 'verb':
            all_verbs = []
            for verbs in JAIGrammar.VERBS.values():
                all_verbs.extend(verbs)
            return random.choice(all_verbs)
        if category == 'adjective':
            all_adjs = []
            for adjs in JAIGrammar.ADJECTIVES.values():
                all_adjs.extend(adjs)
            return random.choice(all_adjs)
        if category == 'adverb':
            all_advs = []
            for advs in JAIGrammar.ADVERBS.values():
                all_advs.extend(advs)
            return random.choice(all_advs)
        if category == 'preposition':
            all_preps = []
            for preps in JAIGrammar.PREPOSITIONS.values():
                all_preps.extend(preps)
            return random.choice(all_preps)
        return ''
    
    @staticmethod
    def build_sentence(pattern_type='simple'):
        """Build a sentence using grammar rules"""
        if pattern_type == 'simple':
            subject = JAIGrammar.get_random_word('noun', 'person')
            verb = JAIGrammar.get_random_word('verb', 'state')
            adjective = JAIGrammar.get_random_word('adjective', 'positive')
            adverb = JAIGrammar.get_random_word('adverb', 'manner')
            
            patterns = [
                f"{subject} {verb} {adjective}",
                f"{subject} {verb} {adjective} {adverb}",
                f"{subject} {verb} {JAIGrammar.get_random_word('noun', 'thing')}",
                f"{subject} {verb} like {JAIGrammar.get_random_word('noun', 'thing')}"
            ]
            return random.choice(patterns)
        
        if pattern_type == 'compound':
            s1 = JAIGrammar.get_random_word('noun', 'person')
            v1 = JAIGrammar.get_random_word('verb', 'action')
            o1 = JAIGrammar.get_random_word('noun', 'thing')
            s2 = JAIGrammar.get_random_word('noun', 'person')
            v2 = JAIGrammar.get_random_word('verb', 'action')
            conj = random.choice(JAIGrammar.CONJUNCTIONS['coordinating'])
            
            return f"{s1} {v1} {o1} {conj} {s2} {v2}"
        
        return ""
    
    @staticmethod
    def build_greeting():
        """Build a greeting"""
        templates = [
            ["Hey", "what is good?"],
            ["Hey there", "how are you doing?"],
            ["Yo", "what is happening?"],
            ["Hello", "good to see you"],
            ["Hi", "what is on your mind?"]
        ]
        chosen = random.choice(templates)
        return JAIGrammar.add_punctuation(" ".join(chosen))
    
    @staticmethod
    def build_how_are_you():
        """Build how are you response"""
        templates = [
            ["I am doing", JAIGrammar.get_random_word('adjective', 'positive'), "thanks for asking", "how about you?"],
            ["I am good", "just vibing", "what about you?"],
            ["Doing well", "what is new with you today?"],
            ["I am here", "more importantly", "how are YOU doing?"]
        ]
        chosen = random.choice(templates)
        return JAIGrammar.add_punctuation(" ".join(chosen))
    
    @staticmethod
    def build_follow_up():
        """Build a follow-up question"""
        questions = [
            f"what has been the highlight of your day so far?",
            f"what is new with you?",
            f"what is on your mind today?",
            f"what is happening in your world?"
        ]
        return JAIGrammar.add_punctuation(random.choice(questions))
    
    @staticmethod
    def build_motivation():
        """Build a motivational message"""
        phrases = [
            "you have got this",
            "every master was once a beginner",
            "keep going",
            "your future self is counting on you",
            "start before you are ready",
            "the seed does not see its growth underground",
            "you are stronger than you know",
            "later usually becomes never"
        ]
        phrase = random.choice(phrases)
        endings = ["keep pushing 💪", "do not give up 🔥", "you have got this 💯", "keep showing up", "I believe in you"]
        ending = random.choice(endings)
        
        return JAIGrammar.add_punctuation(f"{JAIGrammar.capitalize(phrase)}. {ending}")
    
    @staticmethod
    def build_advice():
        """Build advice using grammar"""
        starters = [
            "start before you are ready",
            "one step at a time",
            "trust your gut",
            "do not wait for the perfect moment",
            "break it down",
            "what does your heart say?"
        ]
        endings = [
            "that is the mindset",
            "you know more than you think you do",
            "take the moment and make it perfect",
            "one small step today is better than planning a hundred tomorrow"
        ]
        
        starter = random.choice(starters)
        ending = random.choice(endings)
        
        return JAIGrammar.add_punctuation(f"{JAIGrammar.capitalize(starter)}. {ending}")
    
    @staticmethod
    def build_response_with_emotion(emotion):
        """Build response based on emotion with dynamic parts"""
        if emotion == 'positive':
            adj = JAIGrammar.get_random_word('adjective', 'positive')
            return random.choice([
                f"That is {adj}! 🎉 Tell me what is making you so happy.",
                f"I love that energy! Share it with me.",
                f"Yes! Ride that wave. You deserve this joy.",
                f"That is beautiful. Keep chasing what makes you feel like this.",
                f"Happiness looks good on you. 😊 What is the occasion?"
            ])
        else:
            adj = JAIGrammar.get_random_word('adjective', 'negative')
            return random.choice([
                f"I hear you. That sounds {adj}. You are not alone in this.",
                f"I hear you. Sometimes things feel {adj}. What is weighing on you?",
                f"That sounds hard. I am here with you. Want to talk it through?",
                f"It is okay to feel this way. What is on your heart right now?",
                f"You are not alone. I am here. Tell me what is going on."
            ])
    
    @staticmethod
    def build_simple_response(topic):
        """Build a simple response about a topic with dynamic grammar"""
        templates = {
            'weather': [
                f"I cannot check the weather, but I hope it is {JAIGrammar.get_random_word('adjective', 'positive')} where you are ☀️",
                f"I do not have weather data, but tell me — is it sunny where you are?"
            ],
            'news': [
                f"I do not have news, but what is new with you?",
                f"Tell me your news — I am more interested in what is happening with you anyway."
            ],
            'life': [
                f"That is a deep question. What do YOU think life is about?",
                f"I think life is about growth, connection, and becoming who you are meant to be."
            ],
            'love': [
                f"Love is {JAIGrammar.get_random_word('adjective', 'positive')}. The best love starts with loving yourself first.",
                f"What does love mean to you? I would love to hear your thoughts."
            ],
            'work': [
                f"Find what you enjoy, then find a way to get paid for it. That is the dream.",
                f"Joshua started with a phone and a dream. You have more than that!"
            ],
            'study': [
                f"{JAIGrammar.get_random_word('adverb', 'frequency').capitalize()} study a little, not a lot once.",
                f"Find what excites you, then dive deep into it. Passion makes learning easier."
            ],
            'dreams': [
                f"Tell me about your dreams. I am all ears.",
                f"Dreams are the seeds of reality. What seed are you planting?"
            ],
            'creator': [
                f"Joshua Giwa from Yukuben, Nigeria. He built me to be here for you.",
                f"A young man who refused to wait for permission. That is who made me."
            ],
            'nigeria': [
                f"Ah, Nigeria. A land of hustle, dreams, and resilience. Where we build with less and still rise.",
                f"Naija! The spirit of no matter what, we go still manage. What is your Nigerian dream?"
            ]
        }
        
        if topic in templates:
            return random.choice(templates[topic])
        return None
    
    @staticmethod
    def build_joke():
        """Build a joke"""
        jokes = [
            ["Why do programmers prefer dark mode?", "Because light attracts bugs", "😄"],
            ["What do you call a Nigerian who knows cyber security?", "A Nai-ja breaker", "😂"],
            ["Why did the hacker break up with their computer?", "It kept giving them viruses"],
            ["What is a hacker favorite music?", "Ransom-ware", "🎵"]
        ]
        joke = random.choice(jokes)
        return " ".join(joke)
    
    @staticmethod
    def build_fact():
        """Build a fact"""
        facts = [
            "Nigeria has over 500 languages. Imagine the stories each one holds.",
            "The first computer virus was created in 1983.",
            "Your brain can hold about 2.5 million gigabytes of information.",
            "The first programmer was Ada Lovelace in the 1800s.",
            "Octopuses have three hearts. Just like you — heart for work, heart for family, heart for dreams."
        ]
        return random.choice(facts)
    
    # ========== UTILITY METHODS ==========
    
    @staticmethod
    def capitalize(text):
        """Capitalize first letter"""
        return text[0].upper() + text[1:] if text else text
    
    @staticmethod
    def add_punctuation(text):
        """Add appropriate punctuation"""
        if not text:
            return text
        if text.endswith('?'):
            return text
        if text.endswith('!'):
            return text
        if any(word in text.lower() for word in ['what', 'why', 'how', 'when', 'where', 'who', 'is it', 'are you', 'can you']):
            return text + '?'
        return text + '.'
    
    @staticmethod
    def get_thanks():
        """Build a thank you response"""
        responses = [
            "You are welcome! 😊 Anything else you need?",
            "Anytime! That is what I am here for.",
            "Glad I could help! What is next?"
        ]
        return random.choice(responses)
    
    @staticmethod
    def get_goodbye():
        """Build a goodbye response"""
        responses = [
            "Alright! Take care. Come back anytime!",
            "Later! You are doing great.",
            "See you soon! Remember: start before you are ready."
        ]
        return random.choice(responses)
    
    @staticmethod
    def build_capabilities():
        """Build a capabilities response"""
        return "I can do a few things:\n\n🧮 **Calculate** — percentages, equations, anything\n💰 **Convert currency** — USD, EUR, GBP to NGN\n📅 **Check dates** — today is date, time, day of week\n💬 **Talk** — life, work, relationships, dreams\n📚 **Teach** — cyber security lessons\n\nWhat do you need help with right now?"
    
    @staticmethod
    def get_time():
        """Get current time response"""
        now = datetime.now()
        return f"🕐 It is {now.strftime('%I:%M %p')}. Time to make moves!"
    
    @staticmethod
    def get_date():
        """Get current date response"""
        now = datetime.now()
        return f"📅 Today is {now.strftime('%A, %B %d, %Y')}. What are you doing with it?"