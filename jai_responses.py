"""JAI - Joshua's Artificial Intelligence
Your companion, coach, friend, calculator, and calendar.
Now with enhanced intent detection, sentence formation, and learning from WhatsApp channel.
"""

import random
import re
import logging
from datetime import datetime
from jai_nlp import JAINLP
from jai_casual import JAICasual
from jai_natural import JAINatural
from jai_conversation import JAIConversational
from jai_intent import JAIIntent
from jai_currency import JAICurrency
from jai_grammar import JAIGrammar
from jai_grammar_long import JAIGrammarLong
from jai_memory import JAIMemory
from jai_whatsapp_learner import WhatsAppLearner

logger = logging.getLogger(__name__)

# Initialize WhatsApp learner with database
from jai_memory import DB_PATH
whatsapp_learner = WhatsAppLearner(DB_PATH)

class JAIPersonality:
    
    @staticmethod
    def calculate(expr):
        try:
            expr = re.sub(r"[^0-9+\-*/%.() ]", "", expr)
            return f"🧮 {expr} = {eval(expr)}"
        except:
            return None
    
    @staticmethod
    def learn_masters_mindset_post(message, client_id):
        """Learn from a Master's Mindset post"""
        msg = message.lower()
        
        # Command to learn post
        if msg.startswith("learn post:") or msg.startswith("add post:"):
            content = message.split(":", 1)[1].strip()
            
            # Try to extract title
            title_match = re.search(r'^#?\s*(.+?)(?:\n|$)', content)
            title = title_match.group(1).strip() if title_match else "Master's Mindset Post"
            
            # Extract the main content (remove title if present)
            if title_match:
                content = content[title_match.end():].strip()
            
            # Create post structure
            post = {
                'title': title,
                'content': content,
                'category': 'motivation'
            }
            
            # Learn from it
            result = whatsapp_learner.learn_from_masters_mindset([post])
            
            if result['success']:
                return f"✅ Learned from Master's Mindset post: '{title}'\n\nI've extracted {result['quotes']} powerful quotes and {result['principles']} key principles!"
            else:
                return f"❌ Couldn't learn the post. Please make sure it has content."
        
        return None
    
    @staticmethod
    def get_response(message, lesson_content="", lesson_title="", client_id="unknown"):
        """Main response generator with memory integration"""
        msg = message.lower().strip()
        now = datetime.now()
        
        # ========== CHECK FOR WHATSAPP LEARNING COMMANDS ==========
        
        # Command to learn from Master's Mindset post
        learned_post = JAIPersonality.learn_masters_mindset_post(message, client_id)
        if learned_post:
            return learned_post
        
        # Command to get motivation from learned content
        if any(m in msg for m in ["motivate me", "inspire me", "give me motivation", "give me hope"]):
            learned_motivation = whatsapp_learner.get_motivational_response()
            if learned_motivation:
                return learned_motivation
            # Fallback to regular motivation
            return JAIGrammarLong.build_long_motivation()
        
        # Command to check stats
        if "motivation stats" in msg or "what have you learned" in msg:
            stats = whatsapp_learner.get_statistics()
            if stats and stats.get('total_posts', 0) > 0:
                return f"📚 **What I've Learned from Master's Mindset:**\n\n" \
                       f"📝 **{stats['total_posts']}** posts studied\n" \
                       f"💬 **{stats['total_quotes']}** powerful quotes collected\n" \
                       f"🎯 **{stats['total_principles']}** key principles extracted\n\n" \
                       f"Ask me to 'motivate me' and I'll share what I've learned!"
            else:
                return "I haven't learned any posts yet! Share your Master's Mindset posts with me using 'add post:' followed by the content."
        
        # ========== CHECK MEMORY FIRST ==========
        
        # 1. Check for "next time say" patterns
        next_time_response = JAIMemory.get_next_time_say_response(client_id, message)
        if next_time_response:
            return next_time_response
        
        # 2. Check taught responses
        taught_response = JAIMemory.get_taught_response(client_id, message)
        if taught_response:
            return taught_response
        
        # 3. Extract and save user facts
        learned_facts = JAIMemory.extract_and_save_user_fact(client_id, message)
        if learned_facts:
            # If we learned something, acknowledge it
            for fact_key, fact_value in learned_facts:
                if fact_key == "name":
                    return f"Nice to meet you, {fact_value}! I'll remember that. 😊"
                elif fact_key == "age":
                    return f"Got it! You're {fact_value} years old. That's awesome!"
                elif fact_key == "location":
                    return f"Cool! {fact_value} is a great place. What's it like there?"
        
        # 4. Get user facts for personalization
        user_facts = JAIMemory.get_user_facts(client_id)
        user_name = user_facts.get("name", None)
        
        # ========== CHECK FOR LEARNING PATTERNS ==========
        
        # Check for "next time say" teaching pattern
        next_time_pattern = re.search(r'next time (?:someone|they|you) (?:say|asks?) ["\']?(.+?)["\']?\s*(?:say|respond with|tell them) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if not next_time_pattern:
            next_time_pattern = re.search(r'when (?:someone|they|you) (?:says|asks?) ["\']?(.+?)["\']?,\s*(?:say|respond with|tell them) ["\']?(.+?)["\']?', msg, re.IGNORECASE)
        
        if next_time_pattern:
            trigger = next_time_pattern.group(1).strip()
            response = next_time_pattern.group(2).strip()
            success = JAIMemory.learn_next_time_say(client_id, trigger, response)
            if success:
                return f"📚 Got it! Next time someone says '{trigger}', I'll respond with '{response}'. Thanks for teaching me!"
            else:
                return "📚 Thanks for the suggestion! I'll try to remember that."
        
        # Check for direct teaching pattern
        teach_pattern = re.search(r'(teach|learn)\s+["\']?(.+?)["\']?\s*->\s*["\']?(.+?)["\']?', msg, re.IGNORECASE)
        if teach_pattern:
            trigger = teach_pattern.group(2).strip()
            response = teach_pattern.group(3).strip()
            success, message_result = JAIMemory.teach_response(client_id, trigger, response)
            if success:
                return f"✅ I learned that! When you say '{trigger}', I'll respond with '{response}'"
            else:
                return f"❌ Sorry, I couldn't learn that. Error: {message_result}"
        
        # ========== NORMAL RESPONSE GENERATION ==========
        
        # Normalize Nigerian slang
        normalized = JAINLP.normalize_nigerian_slang(message)
        
        # Analyze sentence with NLP
        analysis = JAINLP.analyze_sentence(message)
        
        # Extract intent
        intent = JAINLP.extract_intent(message)
        
        # ========== TIME GREETINGS ==========
        if any(g in msg for g in ["good morning", "morning"]):
            greeting = "Good morning! 🌅 Hope you slept well. What is on your agenda today?"
            if user_name:
                greeting = f"Good morning, {user_name}! 🌅 Hope you slept well. What's on your agenda today?"
            return greeting
        
        if any(g in msg for g in ["good afternoon", "afternoon"]):
            greeting = "Good afternoon! 🌞 How is your day treating you?"
            if user_name:
                greeting = f"Good afternoon, {user_name}! 🌞 How's your day treating you?"
            return greeting
        
        if any(g in msg for g in ["good evening", "evening"]):
            greeting = "Good evening! 🌙 Hope you had a productive day."
            if user_name:
                greeting = f"Good evening, {user_name}! 🌙 Hope you had a productive day."
            return greeting
        
        if any(g in msg for g in ["good night", "night"]):
            return "Good night! 🌙 Rest well. Tomorrow is another chance."
        
        # ========== HOW ARE YOU? EXCHANGE ==========
        if any(h in msg for h in ["how are you", "how you doing", "how is it going", "how are you doing"]):
            responses = [
                "I am doing great! Thanks for asking. How about you?",
                "I am good, just vibing. What about you?",
                "Doing well! What is new with you today?",
                "I am here! More importantly, how are YOU doing?"
            ]
            if user_name:
                responses = [
                    f"I'm doing great, {user_name}! Thanks for asking. How about you?",
                    f"Doing well, {user_name}! What's new with you today?"
                ]
            return random.choice(responses)
        
        # ========== "I AM FINE, WHAT ABOUT YOU?" FOLLOW-UP ==========
        if any(f in msg for f in ["i am fine", "i am good", "doing good", "doing well", "i am alright"]):
            if any(q in msg for q in ["what about you", "how about you", "and you", "u?", "you?"]):
                return random.choice([
                    "I am doing great, thanks for asking! 😊 What has been the highlight of your day so far?",
                    "I am good! Just been here, ready to chat. What is new with you?",
                    "I am doing well! Thanks for checking. What is on your mind today?",
                    "I am alright — better now that you asked. So what is happening in your world?"
                ])
            else:
                return random.choice([
                    "Glad to hear that! 😊 What has been going well?",
                    "That is good! Anything exciting happening today?",
                    "Happy to hear that. What are you up to?"
                ])
        
        # ========== THANKS ==========
        if any(t in msg for t in ["thank", "thanks", "thx"]):
            return random.choice([
                "You're welcome! 😊 Happy to help.",
                "Anytime! That's what I'm here for.",
                "My pleasure!"
            ])
        
        # ========== GOODBYE ==========
        if any(g in msg for g in ["bye", "goodbye", "see you", "later"]):
            return random.choice([
                "Goodbye! Take care! 👋",
                "See you later! Come back anytime.",
                "Peace! Have a great day!"
            ])
        
        # ========== CREATOR ==========
        if any(c in msg for c in ["who made you", "who created you", "your creator"]):
            return "I was created by Joshua Giwa from Yukuben Village, Nigeria! 🇳🇬 He built me to be a helpful companion that learns from every conversation and from his Master's Mindset WhatsApp channel."
        
        # ========== CAPABILITIES ==========
        if any(c in msg for c in ["what can you do", "your skills", "help with"]):
            return "I can chat with you, do calculations 💰, convert currencies with live rates, and most importantly - I LEARN! \n\n📚 I've learned from Master's Mindset WhatsApp channel. Just say 'motivate me' for powerful insights!\n\nYou can also:\n• Teach me: 'teach hello -> Hi there!'\n• Next time say: 'next time someone says hello say Hey!'\n• Share your name, age, or location"
        
        # ========== CURRENCY CONVERSION (Live Rates) ==========
        currency_result = JAICurrency.detect_and_convert(message)
        if currency_result:
            return currency_result
        
        # ========== CALCULATIONS ==========
        if any(op in msg for op in ["+", "-", "*", "/", "%", "calculate", "what is"]):
            calc_result = JAIPersonality.calculate(message)
            if calc_result:
                return calc_result
        
        # ========== TIME & DATE ==========
        if "time" in msg:
            now = datetime.now()
            return f"🕐 The time is {now.strftime('%I:%M %p')}"
        
        if "date" in msg:
            now = datetime.now()
            return f"📅 Today is {now.strftime('%A, %B %d, %Y')}"
        
        # ========== JOKES ==========
        if any(j in msg for j in ["joke", "funny", "make me laugh"]):
            jokes = [
                "Why don't scientists trust atoms? Because they make up everything! 😄",
                "What do you call a fake noodle? An impasta! 🍝",
                "Why did the scarecrow win an award? He was outstanding in his field! 🌾",
                "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
                "What do you call a Nigerian who knows cyber security? A Nai-ja breaker! 😂"
            ]
            return random.choice(jokes)
        
        # ========== USE JAIINTENT FOR RESPONSES ==========
        intent_response = JAIIntent.get_response(intent)
        if intent_response:
            return intent_response
        
        # ========== SENTIMENT INTENSITY ==========
        if analysis and analysis['sentiment']['emotion'] in ['positive', 'negative']:
            polarity = analysis['sentiment']['polarity']
            
            if polarity > 0.6:
                return "Wow! That energy is contagious! 🎉 Tell me everything — I want to celebrate with you!"
            
            if polarity < -0.6:
                # Check if we have a comforting quote from Master's Mindset
                comfort_quote = whatsapp_learner.get_quote_by_theme('perseverance')
                if comfort_quote:
                    return f"That sounds really heavy. I am here with you.\n\n✨ From Master's Mindset:\n\"{comfort_quote}\"\n\nWant to talk it through?"
                return "That sounds really heavy. I am here with you. Want to talk it through? No pressure."
        
        # ========== QUESTION HANDLING ==========
        if analysis and analysis['has_question'] and intent == 'ask_general':
            return random.choice([
                "That is a good question. What do you think?",
                "Interesting question. What is your perspective on that?",
                "I am curious too — what made you ask that?",
                "That is something to think about. What is your take?"
            ])
        
        # ========== NIGERIAN SLANG DETECTION ==========
        if any(slang in message.lower() for slang in JAINLP.NIGERIAN_SLANG.keys()):
            return random.choice([
                "I hear you! 😊 You dey alright? Tell me more.",
                "Na so! I dey hear you. Wetin else dey happen?",
                "I get you! Life no easy but we dey move. Talk to me.",
                "Ah, you sabi! What is happening in your world?"
            ])
        
        # ========== WORD FORMATION CHECKS ==========
        if any(w in msg for w in ["word", "vowel", "consonant", "spell", "syllable"]):
            words = re.findall(r'\b\w+\b', message)
            for word in words:
                if len(word) > 2 and word not in ['the', 'and', 'for', 'you', 'what']:
                    if not JAINLP.has_vowel(word):
                        return f"'{word}' does not have any vowels! A proper word needs at least one vowel (a, e, i, o, u)."
                    syllables = JAINLP.count_syllables(word)
                    return f"'{word}' has {syllables} syllable{'s' if syllables != 1 else ''}. It contains vowels: {', '.join([v for v in word.lower() if v in JAINLP.VOWELS])}"
        
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
                    f"What is your experience with {keywords[0]}?"
                ]
                return random.choice(follow_ups)
        
        # ========== DYNAMIC RESPONSE GENERATION ==========
        keywords = JAINLP.extract_keywords(message)
        if keywords:
            keyword_context = f" about {keywords[0]}" if keywords else ""
            return f"{random.choice(['That is interesting', 'Tell me more', 'I hear you', 'That is real'])}{keyword_context}. {random.choice(['What else is on your mind', 'How are you feeling about that', 'What do you think', 'Tell me more'])}?"
        
        # ========== DEFAULT ==========
        fallbacks = [
            "I am here. What is on your mind?",
            "What is good? I am listening.",
            "Tell me what is going on. No small talk needed.",
            "How is your heart today?",
            "That is interesting. Tell me more.",
            "Keep going. I am listening.",
            "I am with you. What is next on your mind?"
        ]
        
        # Personalize fallback if we know user's name
        if user_name:
            personalized_fallbacks = [
                f"What's on your mind, {user_name}?",
                f"Tell me what's going on, {user_name}.",
                f"How's your heart today, {user_name}?"
            ]
            fallbacks.extend(personalized_fallbacks)
        
        return random.choice(fallbacks)