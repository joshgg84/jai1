"""JAI - Intent Detection and Handling
All intent patterns and response handlers in one place.
"""

import random
import re

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
    
    # Response handlers for each intent
    @staticmethod
    def get_response(intent, context=None):
        """Generate response based on intent"""
        
        if intent == 'ask_weather':
            return random.choice([
                "I can't check the weather yet, but I hope it's nice where you are! ☀️",
                "Wish I could check the weather for you. Is it sunny or rainy there?",
                "I don't have weather data, but I hope you're enjoying the day!",
                "I can't see the sky from here, but tell me — is it sunny where you are?"
            ])
        
        if intent == 'ask_news':
            return random.choice([
                "I don't have live news, but you can tell me what's happening in your world!",
                "What's new with you? I'd love to hear your news.",
                "I'm not connected to news feeds, but I'm all ears for your updates!",
                "Tell me your news — I'm more interested in what's happening with you anyway."
            ])
        
        if intent == 'ask_motivation':
            return random.choice([
                "You've got this! Every master was once a beginner. Keep going! 💪",
                "The only way to fail is to stop trying. You're still here — that's winning.",
                "Your future self is counting on you. Don't let them down. You've got this! 🔥",
                "Start before you're ready. That's the mindset.",
                "The seed doesn't see its growth underground. Keep showing up.",
                "You're stronger than you know. Keep pushing.",
                "Later usually becomes never. Do it now."
            ])
        
        if intent == 'ask_advice':
            return random.choice([
                "Start before you're ready. That's the mindset Joshua lives by.",
                "One step at a time. Progress is progress, no matter how small.",
                "Trust your gut. You know more than you think you do.",
                "Don't wait for the perfect moment. Take the moment and make it perfect.",
                "What does your heart say? That's usually the right answer.",
                "Break it down. One small step today is better than planning a hundred tomorrow.",
                "Later usually becomes never. Do it now."
            ])
        
        if intent == 'ask_life':
            return random.choice([
                "That's a deep question. What do YOU think life is about?",
                "I think life is about growth, connection, and becoming who you're meant to be.",
                "Maybe life is about finding purpose and people to share it with. What's your take?",
                "Life is what you make it. What are you making of yours?",
                "The meaning of life? I think it's different for everyone. What does it mean to you?"
            ])
        
        if intent == 'ask_love':
            return random.choice([
                "Love is beautiful. The best love starts with loving yourself first.",
                "Love isn't about finding someone perfect. It's about growing together.",
                "What does love mean to you? I'd love to hear your thoughts.",
                "Real love sees your flaws and stays anyway. That's the kind worth waiting for.",
                "Love yourself first. Then you'll know what love should feel like."
            ])
        
        if intent == 'ask_work':
            return random.choice([
                "Find what you enjoy, then find a way to get paid for it. That's the dream.",
                "What skills do you have? What do you enjoy? Let's start there.",
                "Joshua started with a phone and a dream. You have more than that!",
                "Don't chase money. Chase value. Money follows value.",
                "Your career is a marathon, not a sprint. Enjoy the journey."
            ])
        
        if intent == 'ask_study':
            return random.choice([
                "Consistency beats intensity. Study a little every day, not a lot once.",
                "Find what excites you, then dive deep. Passion makes learning easier.",
                "What do you want to learn? Start there. One topic at a time.",
                "Learning is a journey. Enjoy the process, not just the destination.",
                "The best way to learn is to do. Start building something today."
            ])
        
        if intent == 'ask_dreams':
            return random.choice([
                "My dream is to be here for you — to listen, help, and grow with you.",
                "I dream of becoming the best companion I can be. What about you?",
                "Tell me about your dreams. I'm all ears!",
                "Dreams are the seeds of reality. What seed are you planting?",
                "What's that one thing you've always wanted to do? Start there."
            ])
        
        if intent == 'ask_about_creator':
            return random.choice([
                "Joshua Giwa is my creator — a web developer and dreamer from Yukuben, Nigeria.",
                "Joshua built me from a phone, from a village, with a dream. He's pretty amazing!",
                "He's from Yukuben, Nigeria. A young man who refused to wait for permission.",
                "Joshua Giwa. Web developer, freelancer, and someone who believes people are more than their struggles.",
                "He built me to be here for you. That's the kind of person he is."
            ])
        
        if intent == 'ask_nigeria':
            return random.choice([
                "Ah, Nigeria! A land of hustle, dreams, and resilience. Where we build with less and still rise.",
                "From Yukuben to the world. Nigeria is where my story began.",
                "Naija! The spirit of 'no matter what, we go still manage.' What's your Nigerian dream?",
                "Nigeria — where the hustle is real and the dreams are bigger.",
                "The energy of Nigeria is unmatched. What part are you from?"
            ])
        
        if intent == 'ask_joke':
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs! 😄",
                "What do you call a Nigerian who knows cyber security? A 'Nai-ja'breaker! 😂",
                "Why did the hacker break up with their computer? It kept giving them viruses!",
                "What's a hacker's favorite music? Ransom-ware! 🎵",
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "What do you call a fake noodle? An impasta! 😂"
            ]
            return random.choice(jokes) + " Want another?"
        
        if intent == 'ask_fact':
            facts = [
                "Did you know? Nigeria has over 500 languages. Imagine the stories each one holds.",
                "The first computer virus was created in 1983.",
                "Your brain can hold about 2.5 million gigabytes of information.",
                "The first programmer was Ada Lovelace in the 1800s.",
                "Octopuses have three hearts. Just like you — heart for work, heart for family, heart for dreams.",
                "The average person spends 6 months of their life waiting for red lights to turn green.",
                "Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs."
            ]
            return random.choice(facts) + " Anything else you want to know?"
        
        if intent == 'positive_emotion':
            return random.choice([
                "That's amazing! 🎉 Tell me what's making you so happy. I want to celebrate with you!",
                "I love that energy! Share it with me. What's got you feeling this way?",
                "Yes! Ride that wave. You deserve this joy.",
                "That's beautiful. Keep chasing what makes you feel like this.",
                "Happiness looks good on you. 😊 What's the occasion?"
            ])
        
        if intent == 'negative_emotion':
            return random.choice([
                "I hear you. That sounds really heavy. You're not alone in this. Want to talk about what's going on?",
                "I hear you. Sometimes things feel tough. What's weighing on you right now? I'm here to listen.",
                "That sounds hard. I'm here with you. Want to talk it through?",
                "It's okay to feel this way. What's on your heart right now?",
                "You're not alone. I'm here. Tell me what's going on."
            ])
        
        if intent == 'greeting':
            return random.choice([
                "Hey! What's good? How are you doing?",
                "Yo! What's happening? You okay today?",
                "Hey there! What's the vibe?",
                "Hello! Good to see you. What's on your mind?"
            ])
        
        if intent == 'how_are_you':
            return random.choice([
                "I'm doing great! Thanks for asking. How about you?",
                "I'm good, just vibing. What about you?",
                "Doing well! What's new with you today?",
                "I'm here! More importantly, how are YOU doing?"
            ])
        
        if intent == 'thanks':
            return random.choice([
                "You're welcome! 😊 Anything else you need?",
                "Anytime! That's what I'm here for.",
                "Glad I could help! What's next?"
            ])
        
        if intent == 'goodbye':
            return random.choice([
                "Alright! Take care. Come back anytime!",
                "Later! You're doing great.",
                "See you soon! Remember: start before you're ready."
            ])
        
        if intent == 'ask_creator':
            return "I was built by Joshua Giwa from Yukuben, Nigeria. He's a web developer, a dreamer, and someone who believes people are more than their struggles. He built me to be here for you. What's on your heart today?"
        
        if intent == 'ask_capabilities':
            return "I can do a few things:\n\n🧮 **Calculate** — percentages, equations, anything\n💰 **Convert currency** — USD, EUR, GBP to NGN\n📅 **Check dates** — today's date, time, day of week\n💬 **Talk** — life, work, relationships, dreams\n📚 **Teach** — cyber security lessons\n\nWhat do you need help with right now?"
        
        if intent == 'ask_date':
            from datetime import datetime
            now = datetime.now()
            return f"📅 Today is {now.strftime('%A, %B %d, %Y')}. What are you doing with it?"
        
        if intent == 'ask_time':
            from datetime import datetime
            now = datetime.now()
            return f"🕐 It's {now.strftime('%I:%M %p')}. Time to make moves!"
        
        if intent == 'ask_calculation':
            return "Yes! 🧮 I can calculate anything. Just ask me like 'What's 15% of 200?' or '4+4'. What do you want to calculate?"
        
        if intent == 'ask_currency':
            return "Yes! 💰 I can convert USD, EUR, GBP to NGN. Just say something like '100 USD to NGN'. What do you want to convert?"
        
        return None