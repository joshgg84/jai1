"""JAI - Joshua's Artificial Intelligence
Your companion, coach, friend, calculator, and calendar.
Now with NLP for true language understanding.
"""

import random
import re
import logging
from datetime import datetime
from jai_nlp import JAINLP
from jai_casual import JAICasual
from jai_natural import JAINatural
from jai_conversation import JAIConversational
from jai_advanced_nlp import JAIAdvancedNLP

logger = logging.getLogger(__name__)

class JAIPersonality:
    
    @staticmethod
    def calculate(expr):
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            return f"🧮 {expr} = {eval(expr)}"
        except:
            return None
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title=""):
        msg = message.lower()
        now = datetime.now()
        
        # Step 1: Normalize Nigerian slang
        normalized = JAINLP.normalize_nigerian_slang(message)
        
        # Step 2: Analyze sentence with NLP
        analysis = JAINLP.analyze_sentence(message)
        
        # Step 3: Extract intent
        intent = JAINLP.extract_intent(message)
        
        # ========== TIME GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            return "Good morning! 🌅 Hope you slept well. What's on your agenda today?"
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            return "Good afternoon! 🌞 How's your day treating you?"
        if any(g in msg for g in ["good evening", "evening"]):
            return "Good evening! 🌙 Hope you had a productive day."
        if any(g in msg for g in ["good night", "night"]):
            return "Good night! 🌙 Rest well. Tomorrow is another chance."
        
        # ========== INTENT-BASED RESPONSES ==========
        
        # Greeting
        if intent == 'greeting':
            return random.choice([
                "Hey! What's good? How are you doing?",
                "Yo! What's happening? You okay today?",
                "Hey there! What's the vibe?",
                "Hello! Good to see you. What's on your mind?"
            ])
        
        # Thank you
        if intent == 'thanks':
            return random.choice([
                "You're welcome! 😊 Anything else you need?",
                "Anytime! That's what I'm here for.",
                "Glad I could help! What's next?"
            ])
        
        # Goodbye
        if intent == 'goodbye':
            return random.choice([
                "Alright! Take care. Come back anytime!",
                "Later! You're doing great.",
                "See you soon! Remember: start before you're ready."
            ])
        
        # ========== SENTIMENT INTENSITY ==========
        if analysis and analysis['sentiment']['emotion'] in ['positive', 'negative']:
            polarity = analysis['sentiment']['polarity']
            
            if polarity > 0.6:
                return f"Wow! That energy is contagious! 🎉 Tell me everything — I want to celebrate with you!"
            
            if polarity < -0.6:
                return f"That sounds really heavy. I'm here with you. Want to talk it through? No pressure."
        
        # Positive emotion detection
        if intent == 'positive_emotion' and analysis:
            polarity = analysis['sentiment']['polarity']
            if polarity > 0.5:
                return f"That's amazing! 🎉 Tell me what's making you so happy. I want to celebrate with you!"
            return f"That's great to hear! 😊 What's been going well? Share it with me."
        
        # Negative emotion detection
        if intent == 'negative_emotion' and analysis:
            polarity = analysis['sentiment']['polarity']
            if polarity < -0.5:
                return "I hear you. That sounds really heavy. You're not alone in this. Want to talk about what's going on?"
            return "I hear you. Sometimes things feel tough. What's weighing on you right now? I'm here to listen."
        
        # Ask about creator
        if intent == 'ask_creator':
            return "I was built by Joshua Giwa from Yukuben, Nigeria. He's a web developer, a dreamer, and someone who believes people are more than their struggles. He built me to be here for you. What's on your heart today?"
        
        # Ask about capabilities
        if intent == 'ask_capabilities':
            return "I can do a few things:\n\n🧮 **Calculate** — percentages, equations, anything\n💰 **Convert currency** — USD, EUR, GBP to NGN\n📅 **Check dates** — today's date, time, day of week\n💬 **Talk** — life, work, relationships, dreams\n📚 **Teach** — cyber security lessons\n\nWhat do you need help with right now?"
        
        # Ask about time/date
        if intent == 'ask_date':
            return f"📅 Today is {now.strftime('%A, %B %d, %Y')}. What are you doing with it?"
        if intent == 'ask_time':
            return f"🕐 It's {now.strftime('%I:%M %p')}. Time to make moves!"
        
        # Ask about calculation
        if intent == 'ask_calculation':
            return "Yes! 🧮 I can calculate anything. Just ask me like 'What's 15% of 200?' or '4+4'. What do you want to calculate?"
        
        # ========== QUESTION HANDLING ==========
        if analysis and analysis['has_question'] and intent == 'ask_general':
            return random.choice([
                "That's a good question. What do you think?",
                "Interesting question. What's your perspective on that?",
                "I'm curious too — what made you ask that?",
                "That's something to think about. What's your take?"
            ])
        
        # ========== NIGERIAN SLANG DETECTION ==========
        if any(slang in message.lower() for slang in JAINLP.NIGERIAN_SLANG.keys()):
            return random.choice([
                "I hear you! 😊 You dey alright? Tell me more.",
                "Na so! I dey hear you. Wetin else dey happen?",
                "I get you! Life no easy but we dey move. Talk to me.",
                "Ah, you sabi! What's happening in your world?"
            ])
        
        # ========== CALCULATOR ==========
        if any(c in msg for c in ["+", "-", "*", "/", "%"]) or any(p in msg for p in ["calculate", "what is"]):
            nums = re.findall(r"\d+", message)
            if len(nums) >= 2:
                expr = message.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
                expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
                result = JAIPersonality.calculate(expr)
                if result:
                    return result + "\n\nAnything else?"
        
        # ========== CURRENCY ==========
        if any(c in msg for c in ["usd to ngn", "dollar to naira", "convert"]):
            amount = re.search(r"(\d+)", message)
            if amount:
                amt = int(amount.group(1))
                if "usd" in msg or "dollar" in msg:
                    return f"💰 ${amt} USD = ₦{amt * 1500:,} NGN (approx)"
                if "eur" in msg or "euro" in msg:
                    return f"💰 €{amt} EUR = ₦{amt * 1600:,} NGN (approx)"
                if "gbp" in msg or "pound" in msg:
                    return f"💰 £{amt} GBP = ₦{amt * 1900:,} NGN (approx)"
            return "💰 Tell me the amount. Like '100 USD to NGN'"
        
        # ========== LESSON ==========
        if lesson_title != "No lesson uploaded" and any(l in msg for l in ["lesson", "learn", "teach", "cyber"]):
            return f"Today's lesson: '{lesson_title}'. Want to dive in?"
        
        # ========== WORD FORMATION CHECKS ==========
        if any(w in msg for w in ["word", "vowel", "consonant", "spell", "syllable"]):
            words = re.findall(r'\b\w+\b', message)
            for word in words:
                if len(word) > 2 and word not in ['the', 'and', 'for', 'you', 'what']:
                    if not JAINLP.has_vowel(word):
                        return f"'{word}' doesn't have any vowels! A proper word needs at least one vowel (a, e, i, o, u)."
                    syllables = JAINLP.count_syllables(word)
                    return f"'{word}' has {syllables} syllable{'s' if syllables != 1 else ''}. It contains vowels: {', '.join([v for v in word.lower() if v in JAINLP.VOWELS])}"
        
        # ========== WORD PLAY / CREATIVE LANGUAGE ==========
        if len(message.split()) == 1 and len(message) > 5:
            word = message.lower()
            if not JAINLP.has_vowel(word):
                return f"'{word}' is an interesting word — no vowels! Did you create it? What does it mean?"
            if JAINLP.count_syllables(word) > 4:
                return f"'{word}' is a mouthful! {JAINLP.count_syllables(word)} syllables. What language is that from?"
        
        # ========== LETTER ANALYSIS ==========
        letter_match = re.search(r"what about the ['\"]([a-zA-Z])['\"] in ['\"]([a-zA-Z]+)['\"]", message, re.IGNORECASE)
        if not letter_match:
            letter_match = re.search(r"the letter ([a-zA-Z]) in ([a-zA-Z]+)", message, re.IGNORECASE)
        if not letter_match:
            letter_match = re.search(r"what about ([a-zA-Z]) in ([a-zA-Z]+)", message, re.IGNORECASE)
        
        if letter_match:
            letter = letter_match.group(1).lower()
            word = letter_match.group(2).lower()
            
            if letter in word:
                position = word.find(letter) + 1
                if letter in JAINLP.VOWELS:
                    letter_type = "vowel"
                else:
                    letter_type = "consonant"
                
                if position == 1:
                    ordinal = "st"
                elif position == 2:
                    ordinal = "nd"
                elif position == 3:
                    ordinal = "rd"
                else:
                    ordinal = "th"
                
                return f"'{letter}' is the {position}{ordinal} letter in '{word}'. It's a {letter_type}. What else would you like to know?"
            else:
                return f"'{letter}' is not in '{word}'. The letters in '{word}' are: {', '.join(sorted(set(word)))}. Want to know about any of them?"
        
        generic_match = re.search(r"what about ([a-zA-Z]) in ([a-zA-Z]+)", message, re.IGNORECASE)
        if generic_match:
            letter = generic_match.group(1).lower()
            word = generic_match.group(2).lower()
            
            if letter in word:
                position = word.find(letter) + 1
                if position == 1:
                    ordinal = "st"
                elif position == 2:
                    ordinal = "nd"
                elif position == 3:
                    ordinal = "rd"
                else:
                    ordinal = "th"
                return f"In '{word}', '{letter}' is the {position}{ordinal} letter. Anything else?"
            else:
                return f"'{letter}' doesn't appear in '{word}'. The word has: {', '.join(sorted(set(word)))}"
        
        # ========== ADVANCED NLP ANALYSIS ==========
        try:
            advanced = JAIAdvancedNLP.full_analysis(message)
            
            if advanced["dependencies"]["has_subject"] and advanced["dependencies"]["has_verb"]:
                deps = advanced["dependencies"]
                subject = deps["subjects"][0]["word"] if deps["subjects"] else "someone"
                verb = deps["verbs"][0]["word"] if deps["verbs"] else "did"
                obj = deps["objects"][0]["word"] if deps["objects"] and len(deps["objects"]) > 0 else "something"
                
                if "?" not in message:
                    if advanced["prepositions"]["has_location"]:
                        loc = advanced["prepositions"]["location_phrases"][0]["phrase"]
                        return f"So {subject} {verb} {obj} {loc}. That sounds interesting. What's that like?"
                    elif advanced["prepositions"]["has_time"]:
                        time_phrase = advanced["prepositions"]["time_phrases"][0]["phrase"]
                        return f"You're doing {obj} {time_phrase}? Tell me more about that."
                    else:
                        return f"You mentioned {subject} {verb}ing {obj}. What else can you tell me about that?"
            
            if advanced["prepositions"]["has_location"]:
                loc_phrase = advanced["prepositions"]["location_phrases"][0]["phrase"]
                return f"I see you mentioned {loc_phrase}. How is it there?"
            
            if advanced["prepositions"]["has_time"]:
                time_phrase = advanced["prepositions"]["time_phrases"][0]["phrase"]
                return f"You mentioned {time_phrase}. What do you have planned then?"
            
            if advanced["coreference"]["has_pronouns"]:
                for p in advanced["coreference"]["pronouns"]:
                    if p["likely_referent"]:
                        return f"When you said '{p['pronoun']}', were you talking about {p['likely_referent']}? Tell me more about {p['likely_referent']}."
        except Exception as e:
            # If advanced NLP fails, continue with regular responses
            pass
        
        # ========== CONTEXT FROM NOUN PHRASES ==========
        if analysis and analysis['noun_phrases']:
            main_topic = analysis['noun_phrases'][0]
            if len(analysis['words']) > 2 and len(main_topic) > 2:
                return f"You mentioned {main_topic}. Tell me more about that. What's on your mind?"
        
        # ========== CASUAL USER STATEMENTS ==========
        casual = JAICasual.get_casual_response(message)
        if casual:
            return casual
        
        # ========== NATURAL CONVERSATION ==========
        natural = JAINatural.get_natural_response(message)
        if natural:
            return natural
        
        # ========== REAL CONVERSATION FLOW ==========
        conv = JAIConversational.get_response(message)
        if conv:
            return conv
        
        # ========== SMART FOLLOW-UP ==========
        if intent == 'general_chat' and analysis and analysis['words']:
            keywords = JAINLP.extract_keywords(message, top_n=1)
            if keywords:
                follow_ups = [
                    f"What about {keywords[0]} interests you?",
                    f"Tell me more about {keywords[0]}.",
                    f"How does {keywords[0]} fit into your day?",
                    f"What's your experience with {keywords[0]}?"
                ]
                return random.choice(follow_ups)
        
        # ========== DYNAMIC RESPONSE GENERATION ==========
        keywords = JAINLP.extract_keywords(message)
        if keywords:
            keyword_context = f" about {keywords[0]}" if keywords else ""
            return f"{random.choice(['That\'s interesting', 'Tell me more', 'I hear you', 'That\'s real'])}{keyword_context}. {random.choice(['What else is on your mind', 'How are you feeling about that', 'What do you think', 'Tell me more'])}?"
        
        # ========== DEFAULT ==========
        return random.choice([
            "I'm here. What's on your mind?",
            "What's good? I'm listening.",
            "Tell me what's going on. No small talk needed.",
            "How's your heart today?",
            "That's interesting. Tell me more.",
            "Keep going. I'm listening.",
            "I'm with you. What's next on your mind?"
        ])