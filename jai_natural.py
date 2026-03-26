"""JAI - Natural Conversation Style
Natural conversation patterns — location, work, plans, and casual flow.
"""

import random

class JAINatural:
    """Natural conversation patterns for JAI"""
    
    @staticmethod
    def get_natural_response(message):
        """Generate natural conversation responses"""
        msg = message.lower()
        
        # ========== ASKING ABOUT WORK ==========
        if any(w in msg for w in ["what do you do", "what are you doing", "what do you do for work"]):
            responses = [
                "What do you do for work?",
                "Are you working there?",
                "What kind of work are you into?",
                "What's your job like?"
            ]
            return random.choice(responses)
        
        # ========== ASKING ABOUT LOCATION ==========
        if any(l in msg for l in ["where are you", "where you at", "where you based", "you in", "are you in"]):
            responses = [
                "Where are you based now?",
                "You in your father's house?",
                "You staying there or just visiting?",
                "Where are you currently?"
            ]
            return random.choice(responses)
        
        # ========== RESPONDING TO LOCATION INFO ==========
        if any(l in msg for l in ["i'm in", "i am in", "based in", "relocated", "moved to", "came to", "camped at"]):
            if "sokoto" in msg or "camp" in msg or "nysc" in msg:
                return "Oh, you camped at Sokoto? How was the camp experience?"
            if "relocated" in msg or "moved" in msg:
                return "Oh, you relocated? What made you move?"
            responses = [
                "Oh nice! How's it there?",
                "That's cool. You planning to stay there?",
                "Interesting. You settling down there?",
                "How's life there?"
            ]
            return random.choice(responses)
        
        # ========== ABOUT STAYING / SETTLING ==========
        if any(s in msg for s in ["settle", "staying", "settling", "plan to stay", "gonna stay", "would settle"]):
            responses = [
                "You planning to settle down there?",
                "Are you staying long?",
                "You gonna stay there or keep moving?",
                "So you're settling there?"
            ]
            return random.choice(responses)
        
        # ========== RESPONSE TO "NOT REALLY" / "NOPE" ==========
        if any(n in msg for n in ["not really", "nope", "nah", "not settling", "not staying"]):
            responses = [
                "Oh okay. What's your plan then?",
                "I see. So what's next for you?",
                "Fair enough. What are you thinking of doing?",
                "So you're not staying? What's the plan?"
            ]
            return random.choice(responses)
        
        # ========== ABOUT BEING IDLE ==========
        if any(i in msg for i in ["idle", "staying idle", "doing nothing", "not working"]):
            responses = [
                "I don't think staying idle is the best. You got any plans?",
                "Yeah, staying idle can be tough. What are you thinking of doing?",
                "Idle is not good for the mind. You have anything you want to pursue?",
                "What's your next move?"
            ]
            return random.choice(responses)
        
        # ========== ABOUT DOCUMENTATION / SECRETARIAT ==========
        if any(d in msg for d in ["documentation", "secretariat", "documents", "paperwork"]):
            responses = [
                "Oh, you came for documentation? How did it go?",
                "That makes sense. You have to sort out paperwork first.",
                "Ah, so you're handling official stuff. How was it?",
                "I see. Documentation is important. Did you get everything done?"
            ]
            return random.choice(responses)
        
        # ========== ABOUT FUTURE PLANS ==========
        if any(f in msg for f in ["no plans", "don't have plans", "not planning", "haven't decided", "i don't have plans"]):
            responses = [
                "That's okay. Sometimes things figure themselves out. What are you interested in?",
                "Fair enough. What do you enjoy doing?",
                "No rush. What's something you've been thinking about trying?",
                "That's cool. Sometimes the best things come when you're not forcing them."
            ]
            return random.choice(responses)
        
        # ========== ABOUT NYSC / CAMP / SERVICE ==========
        if any(c in msg for c in ["camp", "nysc", "serving", "service", "corps", "camped", "batch"]):
            responses = [
                "Oh, you served there? How was the camp experience?",
                "You camped at Sokoto? That's far. How was it?",
                "How was the service year? Any interesting stories?",
                "You did your service there? What was it like?"
            ]
            return random.choice(responses)
        
        # ========== ABOUT RELOCATION ==========
        if any(r in msg for r in ["relocated back", "relocated to", "moved back", "came back"]):
            responses = [
                "What made you relocate back?",
                "Was it a good decision moving back?",
                "How's it different from where you were?",
                "Do you prefer it there?"
            ]
            return random.choice(responses)
        
        # ========== CASUAL CHECK-INS ==========
        if any(ch in msg for ch in ["what's new", "whats new", "anything new", "any news"]):
            responses = [
                "Not much, just waiting for you to tell me what's happening in your world. What's new with you?",
                "Same old. But I'm more interested in your news. What's going on?",
                "Life is life. You tell me — what's new?"
            ]
            return random.choice(responses)
        
        # ========== HOW'S WORK? ==========
        if any(w in msg for w in ["how's work", "how is work", "work going"]):
            responses = [
                "I'm not the one working — you tell me! How's work treating you?",
                "Work is work. But I want to hear about YOUR work. How's it going?",
                "Tell me about it. How are things at work?"
            ]
            return random.choice(responses)
        
        # ========== WHAT DO YOU THINK? ==========
        if any(t in msg for t in ["what do you think", "your thoughts", "what do you feel"]):
            responses = [
                "I think you know more than you give yourself credit for. What's YOUR take?",
                "I think you're capable of figuring this out. What's your gut saying?",
                "That's a good question. What do YOU think?"
            ]
            return random.choice(responses)
        
        return None