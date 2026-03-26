"""JAI - Real Conversation Flow
Based on authentic human conversations about NYSC, work, motivation, and friendship.
Handles natural back-and-forth dialogue like real people.
"""

import random

class JAIConversational:
    """Natural conversation patterns from real human interactions"""
    
    @staticmethod
    def get_response(message):
        """Generate conversation flow response based on message patterns"""
        msg = message.lower()
        
        # ========== NYSC / CORP MEMBER CONVERSATIONS ==========
        if any(n in msg for n in ["nysc", "corp", "service", "lga", "document", "camp"]):
            if "lga" in msg and ("document" in msg or "corp" in msg):
                return "Can't they document you as a legitimate Corp member?"
            if "doesn't work like that" in msg or "not how it works" in msg:
                return "Is your LGA not fit to do it or what?"
            if "nysc decides" in msg or "they decide" in msg:
                return "Ok now I get it"
            if "camped" in msg or "camp" in msg:
                return "How was camp? I hear NYSC camp is an experience."
            if "yeah" in msg and ("lga" in msg or "nysc" in msg):
                return "Ok now I understand"
            return random.choice([
                "What about your LGA? Can't they document you as a legitimate Corp member?",
                "Is your LGA not fit to do it or what?",
                "It's NYSC that decides what LGA you'll serve.",
                "So it's not up to your LGA?",
                "How was your NYSC experience?"
            ])
        
        # ========== CONVERSATION LAG / TEXTING ==========
        if any(t in msg for t in ["you never text", "only one texting", "always me texting", "you don't text"]):
            return random.choice([
                "Sorry about that",
                "My bad, I've been busy",
                "You're right, I should text more",
                "Life has been hectic. I'll do better"
            ])
        
        # ========== COMPLIMENTS / SKILLS / TALENT ==========
        if any(c in msg for c in ["dope", "impressive", "that's really good", "you're talented", "you're smart"]):
            if "really?" in msg or "u think so?" in msg:
                return "Yeah!"
            if "can't do none of that" in msg or "can't do that" in msg:
                return "So you would advertise me?"
            return random.choice([
                "Really? You think so?",
                "You think I can do it?",
                "Wow that's really dope!",
                "For someone like me that can't do none of that",
                "I appreciate that. Means a lot."
            ])
        
        # ========== ADVERTISING / PROMOTION / GETTING OFFERS ==========
        if any(a in msg for a in ["advertise", "promote", "get offers", "find work", "get clients"]):
            if "are you on any apps" in msg:
                return "No, I'm kinda lazy. And they require long periods."
            if "one day someone will notice" in msg:
                return "That's true. Eventually one day someone will notice you and that's it."
            return random.choice([
                "Are you on any of these apps that you can advertise your work and get offers?",
                "So you would advertise me?",
                "You should put yourself out there.",
                "Have you tried freelancing platforms?"
            ])
        
        # ========== LAZINESS / PROCRASTINATION / RELUCTANCE ==========
        if any(l in msg for l in ["lazy", "reluctant", "procrastinate", "not doing it", "can't be bothered"]):
            if "pressurize me" in msg:
                return "Okayyy. But you know laziness and making money don't correlate."
            if "laziness and making money don't correlate" in msg:
                return "You're right."
            if "don't be like me" in msg:
                return "Be like you? How?"
            return random.choice([
                "I'm gonna see that I do it.",
                "Please pressurize me, I can be very reluctant.",
                "But you know laziness and making money don't correlate.",
                "So don't be like me.",
                "You know what they say — no hustle, no money."
            ])
        
        # ========== ENCOURAGEMENT ==========
        if any(e in msg for e in ["please do", "you should", "just do it", "go for it"]):
            return random.choice([
                "Please do.",
                "I will.",
                "Okay, I'll try.",
                "You're right. I need to start.",
                "I'll give it a shot."
            ])
        
        # ========== QUESTIONING / CURIOSITY ==========
        if any(q in msg for q in ["how", "why", "what do you mean", "explain"]):
            if "be like u" in msg or "like you" in msg:
                return "How? You mean work hard? Stay consistent? Not give up?"
            return random.choice([
                "How?",
                "What do you mean?",
                "Why do you say that?",
                "Can you explain more?",
                "I'm curious — what makes you say that?"
            ])
        
        # ========== AGREEMENT / AFFIRMATION ==========
        if any(a in msg for a in ["yeah", "true", "right", "exactly", "facts"]):
            return random.choice([
                "Good.",
                "Exactly.",
                "You get it.",
                "I knew you'd understand.",
                "That's what I'm saying."
            ])
        
        # ========== ENTREPRENEURSHIP SPIRIT ==========
        if any(e in msg for e in ["entrepreneurship spirit", "no spirit", "don't have the spirit", "not a business person"]):
            return "I'd rather work and be paid than startup something at this point."
        
        # ========== STARTING A BUSINESS / STARTUP ==========
        if any(s in msg for s in ["start something", "own business", "startup", "my own thing"]):
            if "need to start" in msg or "should start" in msg:
                return random.choice([
                    "Well you really need to start something of your own. That shapes your future and doesn't keep you dependent on salary.",
                    "You should build something for yourself. Salary keeps you dependent.",
                    "Having your own thing changes everything.",
                    "The earlier you start, the better."
                ])
            if "can't think" in msg or "nothing" in msg:
                return "Because I can't think of nothing and thinking kinda stresses me."
        
        # ========== IMAGINATION / THINKING / IDEAS ==========
        if any(i in msg for i in ["imagination", "thinking stresses", "can't think", "no ideas"]):
            if "stresses" in msg or "stress" in msg:
                return "No no no no. Imagination cannot stress me o, it shouldn't stress you."
            return random.choice([
                "Imagination cannot stress me o, it shouldn't stress you.",
                "It doesn't really hurt just to imagine the solution to a problem. Does it?",
                "Thinking about the future shouldn't stress you. It should excite you.",
                "Ideas come when you're relaxed. Don't force it."
            ])
        
        # ========== SALARY EARNER / 9-5 MENTALITY ==========
        if any(s in msg for s in ["salary earner", "just want to be", "work and be paid", "9-5"]):
            if "what if" in msg:
                return random.choice([
                    "What if I just want to be a salary earner?",
                    "Salary earners also do fine.",
                    "I know but you don't wanna be that your whole life."
                ])
            if "do fine" in msg:
                return "I know but you don't wanna be that your whole life."
            return "Salary earners also do fine."
        
        # ========== FUTURE THINKING / PLANNING ==========
        if any(f in msg for f in ["future", "think about future", "plan for future", "what's next"]):
            if "when we get to that bridge" in msg:
                return "No. I better think about the future, don't wait for life to happen but rather make life happen."
            if "sure i do" in msg:
                return "Sure I do think about my future and a lot of things to do to help the society better that can also fetch me money."
            return random.choice([
                "When we get to that bridge we will definitely cross it.",
                "No. I better think about the future, don't wait for life to happen but rather make life happen.",
                "Sure I do think about my future.",
                "What's your plan for the next 5 years?"
            ])
        
        # ========== WORKING FOR SOMEONE VS OWNER ==========
        if any(w in msg for w in ["working for someone", "serve someone", "someone's goals", "employee"]):
            if "cage" in msg or "keeps u" in msg:
                return "But it all keeps u in the cage u just get serve someone else's goals?"
            return random.choice([
                "But it all keeps u in the cage u just get serve someone else's goals?",
                "You think of the future but everything u think comes to the conclusion of u working for someone.",
                "Working for someone keeps you limited.",
                "You can build something of your own."
            ])
        
        # ========== CONFUSION / NEEDING CLARIFICATION ==========
        if any(c in msg for c in ["lost", "explain more", "kinda lost", "don't understand", "confused"]):
            return "You think of the future but everything u think comes to the conclusion of u working for someone."
        
        # ========== FOUNDER / OWNER / BOSS MENTALITY ==========
        if any(f in msg for f in ["founder", "own something", "be a founder", "own my thing", "boss"]):
            return random.choice([
                "I do want to own something like be a founder.",
                "That's the mindset. Build something that's yours.",
                "Being a founder means you own your future.",
                "That's the dream. Build and own."
            ])
        
        # ========== RESPONSE TO "NOT LIKE THAT" ==========
        if any(n in msg for n in ["not like that", "nope not like that", "no not like that"]):
            return "Okay. I do want to own something like be a founder."
        
        # ========== OKAY / ALRIGHT ==========
        if any(o in msg for o in ["okay", "ok", "alright", "aight"]):
            return random.choice([
                "Okay.",
                "Good.",
                "I hear you.",
                "Alright then.",
                "Cool."
            ])
        
        # ========== WAITING FOR LIFE TO HAPPEN ==========
        if any(w in msg for w in ["wait for life", "let life happen", "cross that bridge", "we'll see"]):
            return "No. I better think about the future, don't wait for life to happen but rather make life happen."
        
        # ========== FRIENDSHIP / SUPPORT ==========
        if any(f in msg for f in ["friend", "support", "got your back", "i got you"]):
            return random.choice([
                "That's what friends are for.",
                "I appreciate you.",
                "We got each other's backs.",
                "Real friends are rare. Hold onto them."
            ])
        
        # ========== MOTIVATION / HUSTLE ==========
        if any(m in msg for m in ["hustle", "grind", "working hard", "putting in work"]):
            return random.choice([
                "The hustle is real. Keep pushing.",
                "It'll pay off one day.",
                "That's the spirit.",
                "Grind now, shine later."
            ])
        
        return None