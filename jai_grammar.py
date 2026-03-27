"""JAI - Grammar Engine
Builds sentences from word banks and grammar rules.
Now with prepositions for more natural sentences.
"""

import random
import re
from datetime import datetime

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
        'ask': ['ask', 'wonder', 'am curious'],
        'action': ['do', 'make', 'build', 'create', 'work'],
        'movement': ['go', 'come', 'move', 'walk', 'run']
    }
    
    # Adjectives
    ADJECTIVES = {
        'positive': ['good', 'great', 'wonderful', 'amazing', 'awesome', 'fantastic'],
        'negative': ['heavy', 'tough', 'hard', 'difficult', 'challenging'],
        'neutral': ['interesting', 'curious', 'funny', 'strange'],
        'time': ['early', 'late', 'soon', 'quick', 'slow'],
        'emotion': ['happy', 'sad', 'excited', 'calm', 'peaceful']
    }
    
    # Nouns
    NOUNS = {
        'thing': ['thing', 'stuff', 'matter', 'situation'],
        'day': ['day', 'morning', 'afternoon', 'moment'],
        'life': ['life', 'journey', 'path', 'road'],
        'mind': ['mind', 'heart', 'thoughts', 'spirit'],
        'thoughts': ['thoughts', 'ideas', 'perspective', 'take'],
        'place': ['place', 'space', 'corner', 'room', 'world'],
        'time': ['time', 'moment', 'hour', 'minute', 'second']
    }
    
    # Adverbs
    ADVERBS = {
        'time': ['now', 'today', 'right now', 'at the moment'],
        'manner': ['really', 'truly', 'honestly', 'seriously'],
        'frequency': ['always', 'often', 'sometimes', 'never'],
        'place': ['here', 'there', 'everywhere', 'somewhere', 'anywhere'],
        'degree': ['very', 'quite', 'rather', 'extremely', 'barely']
    }
    
    # ========== PREPOSITIONS ==========
    PREPOSITIONS = {
        'location': ['in', 'on', 'at', 'by', 'near', 'beside', 'behind', 'in front of', 'under', 'over', 'between'],
        'time': ['before', 'after', 'during', 'since', 'until', 'within', 'throughout'],
        'direction': ['to', 'towards', 'into', 'through', 'across', 'along', 'around'],
        'purpose': ['for', 'with', 'by', 'like', 'as'],
        'origin': ['from', 'out of', 'off']
    }
    
    # Conjunctions
    CONJUNCTIONS = ['and', 'but', 'so', 'because', 'though', 'although', 'however', 'therefore']
    
    # Sentence starters
    STARTERS = {
        'opinion': ['I think', 'I believe', 'To me', 'In my view', 'From my perspective'],
        'feeling': ['I feel', 'I sense', 'I notice', 'It seems to me'],
        'question': ['What about', 'How about', 'Tell me about', 'What do you think about', 'Can you share about']
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
        if any(word in text.lower() for word in ['what', 'why', 'how', 'when', 'where', 'who', 'is it', 'are you', 'can you']):
            return text + '?'
        return text + '.'
    
    @staticmethod
    def add_preposition(phrase, prep_type=None):
        """Add a preposition to a phrase"""
        if prep_type:
            prep = random.choice(JAIGrammar.PREPOSITIONS[prep_type])
        else:
            all_preps = []
            for preps in JAIGrammar.PREPOSITIONS.values():
                all_preps.extend(preps)
            prep = random.choice(all_preps)
        return f"{prep} {phrase}"
    
    @staticmethod
    def combine_with_preposition(part1, part2, prep_type='location'):
        """Combine two parts with a preposition"""
        prep = random.choice(JAIGrammar.PREPOSITIONS[prep_type])
        return f"{part1} {prep} {part2}"
    
    # ========== SENTENCE BUILDERS ==========
    
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
            ["I am doing", random.choice(JAIGrammar.ADJECTIVES['positive']), "thanks for asking", "how about you?"],
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
            "what has been the highlight of your day so far?",
            "what is new with you?",
            "what is on your mind today?",
            "what is happening in your world?"
        ]
        return JAIGrammar.add_punctuation(random.choice(questions))
    
    @staticmethod
    def build_motivation():
        """Build a motivational message"""
        phrases = [
            ["you have got this"],
            ["every master was once a beginner"],
            ["keep going"],
            ["your future self is counting on you"],
            ["start before you are ready"],
            ["the seed does not see its growth underground"],
            ["you are stronger than you know"],
            ["later usually becomes never"]
        ]
        phrase = random.choice(phrases)[0]
        ending = random.choice(["keep pushing 💪", "do not give up 🔥", "you have got this 💯", "keep showing up", "I believe in you"])
        
        return JAIGrammar.add_punctuation(f"{JAIGrammar.capitalize(phrase)}. {ending}")
    
    @staticmethod
    def build_advice():
        """Build advice using word bank"""
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
        """Build response based on emotion"""
        if emotion == 'positive':
            responses = [
                f"That is {random.choice(JAIGrammar.ADJECTIVES['positive'])}! 🎉 Tell me what is making you so happy.",
                f"I love that energy! Share it with me.",
                f"Yes! Ride that wave. You deserve this joy.",
                f"That is beautiful. Keep chasing what makes you feel like this.",
                f"Happiness looks good on you. 😊 What is the occasion?"
            ]
        else:
            responses = [
                f"I hear you. That sounds {random.choice(JAIGrammar.ADJECTIVES['negative'])}. You are not alone in this.",
                f"I hear you. Sometimes things feel {random.choice(JAIGrammar.ADJECTIVES['negative'])}. What is weighing on you?",
                f"That sounds hard. I am here with you. Want to talk it through?",
                f"It is okay to feel this way. What is on your heart right now?",
                f"You are not alone. I am here. Tell me what is going on."
            ]
        return random.choice(responses)
    
    @staticmethod
    def build_simple_response(topic):
        """Build a simple response about a topic"""
        templates = {
            'weather': [
                f"I cannot check the weather, but I hope it is {random.choice(JAIGrammar.ADJECTIVES['positive'])} where you are ☀️",
                f"I do not have weather data, but tell me — is it sunny where you are?"
            ],
            'news': [
                f"I do not have news, but what is new with you?",
                f"Tell me your news — I am more interested in what is happening with you anyway."
            ],
            'life': [
                f"That is a deep question. What do YOU {random.choice(JAIGrammar.VERBS['think'])} life is about?",
                f"I think life is about growth, connection, and becoming who you are meant to be."
            ],
            'love': [
                f"Love is {random.choice(JAIGrammar.ADJECTIVES['positive'])}. The best love starts with loving yourself first.",
                f"What does love mean to you? I would love to hear your {random.choice(JAIGrammar.NOUNS['thoughts'])}."
            ],
            'work': [
                f"Find what you enjoy, then find a way to get paid for it. That is the dream.",
                f"Joshua started with a phone and a dream. You have more than that!"
            ],
            'study': [
                f"{random.choice(JAIGrammar.ADVERBS['frequency']).capitalize()} study a little, not a lot once.",
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
    
    # ========== ADDITIONAL METHODS ==========
    
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