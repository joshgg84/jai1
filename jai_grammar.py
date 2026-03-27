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
        """Build advice using word bank with prepositions"""
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
        """Build response based on emotion with prepositions"""
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
                f"I hear you. That sounds {random.choice(JAIGrammar.ADJECTIVES['negative'])}. You're not alone {JAIGrammar.add_preposition('this', 'purpose')}.",
                f"I hear you. Sometimes things feel {random.choice(JAIGrammar.ADJECTIVES['negative'])}. What's weighing {JAIGrammar.add_preposition('you', 'direction')}?",
                f"That sounds hard. I'm here {JAIGrammar.add_preposition('you', 'purpose')}. Want to talk it through?",
                f"It's okay to feel this way. What's {JAIGrammar.add_preposition('your heart', 'location')} right now?",
                f"You're not alone. I'm here. Tell me what's going {JAIGrammar.add_preposition('on', 'direction')}."
            ]
        return random.choice(responses)
    
    @staticmethod
    def build_simple_response(topic):
        """Build a simple response about a topic with prepositions"""
        templates = {
            'weather': [
                f"I can't check the weather, but I hope it's {random.choice(JAIGrammar.ADJECTIVES['positive'])} {JAIGrammar.add_preposition('where you are', 'location')} ☀️",
                f"I don't have weather data, but tell me — is it sunny {JAIGrammar.add_preposition('there', 'location')}?"
            ],
            'news': [
                f"I don't have news, but what's new {JAIGrammar.add_preposition('you', 'purpose')}?",
                f"Tell me your news — I'm more interested {JAIGrammar.add_preposition('what\'s happening', 'purpose')} you anyway."
            ],
            'life': [
                f"That's a deep question. What do YOU {random.choice(JAIGrammar.VERBS['think'])} life is {JAIGrammar.add_preposition('about', 'purpose')}?",
                f"I think life is {JAIGrammar.add_preposition('growth, connection, and becoming who you\'re meant to be', 'purpose')}."
            ],
            'love': [
                f"Love is {random.choice(JAIGrammar.ADJECTIVES['positive'])}. The best love starts {JAIGrammar.add_preposition('loving yourself first', 'purpose')}.",
                f"What does love mean {JAIGrammar.add_preposition('you', 'direction')}? I'd love to hear your {random.choice(JAIGrammar.NOUNS['thoughts'])}."
            ],
            'work': [
                f"Find what you enjoy, then find a way {JAIGrammar.add_preposition('get paid', 'purpose')} it. That's the dream.",
                f"Joshua started {JAIGrammar.add_preposition('a phone', 'purpose')} and a dream. You have more than that!"
            ],
            'study': [
                f"{random.choice(JAIGrammar.ADVERBS['frequency']).capitalize()} study a little, not a lot {JAIGrammar.add_preposition('once', 'time')}.",
                f"Find what excites you, then dive deep {JAIGrammar.add_preposition('it', 'direction')}. Passion makes learning easier."
            ],
            'dreams': [
                f"Tell me {JAIGrammar.add_preposition('your dreams', 'purpose')}. I'm all ears.",
                f"Dreams are the seeds {JAIGrammar.add_preposition('reality', 'origin')}. What seed are you planting?"
            ],
            'creator': [
                f"Joshua Giwa {JAIGrammar.add_preposition('Yukuben, Nigeria', 'origin')}. He built me {JAIGrammar.add_preposition('be here for you', 'purpose')}.",
                f"A young man who refused {JAIGrammar.add_preposition('wait for permission', 'purpose')}. That's who made me."
            ],
            'nigeria': [
                f"Ah, Nigeria. A land {JAIGrammar.add_preposition('hustle, dreams, and resilience', 'origin')}. Where we build {JAIGrammar.add_preposition('less', 'purpose')} and still rise.",
                f"Naija! The spirit {JAIGrammar.add_preposition('no matter what, we go still manage', 'origin')}. What's your Nigerian dream?"
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
    
    # ========== ADDITIONAL METHODS ==========
    
    @staticmethod
    def get_thanks():
        """Build a thank you response"""
        responses = [
            "You're welcome! 😊 Anything else you need?",
            "Anytime! That's what I'm here for.",
            "Glad I could help! What's next?"
        ]
        return random.choice(responses)
    
    @staticmethod
    def get_goodbye():
        """Build a goodbye response"""
        responses = [
            "Alright! Take care. Come back anytime!",
            "Later! You're doing great.",
            "See you soon! Remember: start before you're ready."
        ]
        return random.choice(responses)
    
    @staticmethod
    def build_capabilities():
        """Build a capabilities response"""
        return "I can do a few things:\n\n🧮 **Calculate** — percentages, equations, anything\n💰 **Convert currency** — USD, EUR, GBP to NGN\n📅 **Check dates** — today's date, time, day of week\n💬 **Talk** — life, work, relationships, dreams\n📚 **Teach** — cyber security lessons\n\nWhat do you need help with right now?"
    
    @staticmethod
    def get_time():
        """Get current time response"""
        now = datetime.now()
        return f"🕐 It's {now.strftime('%I:%M %p')}. Time to make moves!"
    
    @staticmethod
    def get_date():
        """Get current date response"""
        now = datetime.now()
        return f"📅 Today is {now.strftime('%A, %B %d, %Y')}. What are you doing with it?"