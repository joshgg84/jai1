"""JAI - Grammar Engine
Builds sentences from word banks and grammar rules.
"""

import random
import re

class JAIGrammar:
    """Generates sentences from word banks"""
    
    # ========== WORD BANKS ==========
    
    # Pronouns
    SUBJECTS = {
        'first': ['I', 'We'],
        'second': ['You'],
        'third': ['He', 'She', 'It', 'They']
    }
    
    # Verbs
    VERBS = {
        'greet': ['greet', 'welcome', 'say hello'],
        'feel': ['feel', 'am', 'am doing'],
        'think': ['think', 'believe', 'feel'],
        'hope': ['hope', 'wish', 'pray'],
        'ask': ['ask', 'wonder', 'am curious']
    }
    
    # Adjectives
    ADJECTIVES = {
        'positive': ['good', 'great', 'wonderful', 'amazing', 'awesome', 'fantastic'],
        'negative': ['heavy', 'tough', 'hard', 'difficult', 'challenging'],
        'neutral': ['interesting', 'curious', 'funny', 'strange']
    }
    
    # Nouns
    NOUNS = {
        'thing': ['thing', 'stuff', 'matter', 'situation'],
        'day': ['day', 'morning', 'afternoon', 'moment'],
        'life': ['life', 'journey', 'path', 'road'],
        'mind': ['mind', 'heart', 'thoughts', 'spirit']
    }
    
    # Adverbs
    ADVERBS = {
        'time': ['now', 'today', 'right now', 'at the moment'],
        'manner': ['really', 'truly', 'honestly', 'seriously'],
        'frequency': ['always', 'often', 'sometimes', 'never']
    }
    
    # Conjunctions
    CONJUNCTIONS = ['and', 'but', 'so', 'because', 'though']
    
    # Sentence starters
    STARTERS = {
        'opinion': ['I think', 'I believe', 'To me', 'In my view'],
        'feeling': ['I feel', 'I sense', 'I notice'],
        'question': ['What about', 'How about', 'Tell me about', 'What do you think about']
    }
    
    # ========== GRAMMAR RULES ==========
    
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
        if any(word in text.lower() for word in ['what', 'why', 'how', 'when', 'where', 'who', 'is it', 'are you']):
            return text + '?'
        return text + '.'
    
    # ========== SENTENCE BUILDERS ==========
    
    @staticmethod
    def build_greeting():
        """Build a greeting"""
        templates = [
            ["Hey", "what's good?"],
            ["Hey there", "how are you doing?"],
            ["Yo", "what's happening?"],
            ["Hello", "good to see you"],
            ["Hi", "what's on your mind?"]
        ]
        chosen = random.choice(templates)
        return JAIGrammar.add_punctuation(" ".join(chosen))
    
    @staticmethod
    def build_how_are_you():
        """Build how are you response"""
        templates = [
            ["I'm doing", random.choice(JAIGrammar.ADJECTIVES['positive']), "thanks for asking", "how about you?"],
            ["I'm good", "just vibing", "what about you?"],
            ["Doing well", "what's new with you today?"],
            ["I'm here", "more importantly", "how are YOU doing?"]
        ]
        chosen = random.choice(templates)
        return JAIGrammar.add_punctuation(" ".join(chosen))
    
    @staticmethod
    def build_follow_up():
        """Build a follow-up question"""
        questions = [
            "what's been the highlight of your day so far?",
            "what's new with you?",
            "what's on your mind today?",
            "what's happening in your world?"
        ]
        return JAIGrammar.add_punctuation(random.choice(questions))
    
    @staticmethod
    def build_motivation():
        """Build a motivational message"""
        phrases = [
            ["you've got this"],
            ["every master was once a beginner"],
            ["keep going"],
            ["your future self is counting on you"],
            ["start before you're ready"],
            ["the seed doesn't see its growth underground"],
            ["you're stronger than you know"],
            ["later usually becomes never"]
        ]
        phrase = random.choice(phrases)[0]
        ending = random.choice(["keep pushing 💪", "don't give up 🔥", "you've got this 💯", "keep showing up", "I believe in you"])
        
        return JAIGrammar.add_punctuation(f"{JAIGrammar.capitalize(phrase)}. {ending}")
    
    @staticmethod
    def build_advice():
        """Build advice using word bank"""
        starters = [
            "start before you're ready",
            "one step at a time",
            "trust your gut",
            "don't wait for the perfect moment",
            "break it down",
            "what does your heart say?"
        ]
        endings = [
            "that's the mindset",
            "you know more than you think you do",
            "take the moment and make it perfect",
            "one small step today is better than planning a hundred tomorrow"
        ]
        
        starter = random.choice(starters)
        ending = random.choice(endings)
        
        return JAIGrammar.add_punctuation(f"{JAIGrammar.capitalize(starter)}. {ending}")
    
    @staticmethod
    def build_response_with_emotion(emotion):
        """Build response based on emotion"""
        if emotion == 'positive':
            responses = [
                f"That's {random.choice(JAIGrammar.ADJECTIVES['positive'])}! 🎉 Tell me what's making you so happy.",
                f"I love that energy! Share it with me.",
                f"Yes! Ride that wave. You deserve this joy.",
                f"That's beautiful. Keep chasing what makes you feel like this.",
                f"Happiness looks good on you. 😊 What's the occasion?"
            ]
        else:
            responses = [
                f"I hear you. That sounds {random.choice(JAIGrammar.ADJECTIVES['negative'])}. You're not alone in this.",
                f"I hear you. Sometimes things feel {random.choice(JAIGrammar.ADJECTIVES['negative'])}. What's weighing on you?",
                f"That sounds hard. I'm here with you. Want to talk it through?",
                f"It's okay to feel this way. What's on your heart right now?",
                f"You're not alone. I'm here. Tell me what's going on."
            ]
        return random.choice(responses)
    
    @staticmethod
    def build_simple_response(topic):
        """Build a simple response about a topic"""
        templates = {
            'weather': [
                f"I can't check the weather, but I hope it's {random.choice(JAIGrammar.ADJECTIVES['positive'])} where you are ☀️",
                f"I don't have weather data, but tell me — is it sunny where you are?"
            ],
            'news': [
                f"I don't have news, but what's new with you?",
                f"Tell me your news — I'm more interested in what's happening with you anyway."
            ],
            'life': [
                f"That's a deep question. What do YOU {random.choice(JAIGrammar.VERBS['think'])} life is about?",
                f"I think life is about growth, connection, and becoming who you're meant to be."
            ],
            'love': [
                f"Love is {random.choice(JAIGrammar.ADJECTIVES['positive'])}. The best love starts with loving yourself first.",
                f"What does love mean to you? I'd love to hear your {random.choice(JAIGrammar.NOUNS['thoughts'])}."
            ],
            'work': [
                f"Find what you enjoy, then find a way to get paid for it. That's the dream.",
                f"Joshua started with a phone and a dream. You have more than that!"
            ],
            'study': [
                f"{random.choice(JAIGrammar.ADVERBS['frequency']).capitalize()} study a little, not a lot once.",
                f"Find what excites you, then dive deep. Passion makes learning easier."
            ],
            'dreams': [
                f"Tell me about your dreams. I'm all ears.",
                f"Dreams are the seeds of reality. What seed are you planting?"
            ],
            'creator': [
                f"Joshua Giwa from Yukuben, Nigeria. He built me to be here for you.",
                f"A young man who refused to wait for permission. That's who made me."
            ],
            'nigeria': [
                f"Ah, Nigeria. A land of hustle, dreams, and resilience. Where we build with less and still rise.",
                f"Naija! The spirit of 'no matter what, we go still manage.' What's your Nigerian dream?"
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
            ["What do you call a Nigerian who knows cyber security?", "A 'Nai-ja'breaker", "😂"],
            ["Why did the hacker break up with their computer?", "It kept giving them viruses"],
            ["What's a hacker's favorite music?", "Ransom-ware", "🎵"]
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