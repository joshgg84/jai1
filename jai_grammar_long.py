"""JAI - Grammar Engine (Long Responses)
Long, thoughtful responses for deep conversations.
"""

import random
from jai_grammar import JAIGrammar

class JAIGrammarLong:
    """Long response builders for deep conversations"""
    
    @staticmethod
    def build_long_motivation():
        """Build a long, detailed motivational message"""
        openings = [
            "Listen, I want to tell you something important.",
            "Here's what I've learned about this journey we're on.",
            "Let me share something that has kept me going.",
            "I need you to hear this."
        ]
        
        bodies = [
            "The path you're walking — it's not supposed to be easy. If it was easy, everyone would be here. The fact that it's hard means you're going somewhere most people never reach.",
            "Every master was once a beginner. Every builder started with one brick. The people you admire today went through what you're going through right now. They just didn't quit.",
            "Your feelings will lie to you. They'll tell you to rest when you need to push. They'll tell you to quit when you need to persist. Don't let them drive. You drive. Feelings are passengers, not the driver.",
            "The seed doesn't see its growth underground. But roots are spreading. Strength is forming. Your boring days are not wasted days. They are foundation days.",
            "You are not where you're going to stay. The struggle is temporary. The growth is permanent. Keep showing up.",
            "The people who make it are not the most talented. They are the ones who refused to stop when everyone else did."
        ]
        
        closings = [
            "Keep showing up. That's the whole secret. Not talent. Not luck. Showing up when you don't feel like it.",
            "You're closer than you think. Don't stop now. The breakthrough comes right after the breaking point.",
            "One day, you'll look back and be grateful you didn't give up today. Keep going.",
            "I believe in you. Not because it's easy — because you're still here."
        ]
        
        return f"{random.choice(openings)} {random.choice(bodies)} {random.choice(closings)}"
    
    @staticmethod
    def build_long_advice():
        """Build a long, detailed advice message"""
        starters = [
            "Here's what I've learned about this.",
            "Let me give you something to think about.",
            "If you're asking me, here's what I believe.",
            "I've thought about this a lot."
        ]
        
        advices = [
            "Start before you're ready. Most people wait until they feel prepared. They wait until the conditions are perfect. But the conditions will never be perfect. The only perfect time to start is now. Start ugly. Start small. Just start.",
            "Don't trade what you want most for what you want now. The short-term pleasure will cost you long-term progress. Every time you choose the easy thing over the right thing, you're voting for a future you don't want.",
            "Your consistency is more powerful than your intensity. A hundred small steps will outrun one giant leap that never happens. Show up every day. Even when it's small. Even when it's slow. Just show up.",
            "The people who succeed are not the ones who never fail. They are the ones who fail and keep going. Failure is not the opposite of success. It's part of it.",
            "Stop comparing your beginning to someone else's middle. They have been at it longer. You will get there. Just keep walking your own path.",
            "What you do in private will eventually show up in public. Build in secret. Practice when no one is watching. The world will notice when it's ready."
        ]
        
        closings = [
            "That's what I've seen work. What do you think?",
            "I hope that helps. You've got this.",
            "Just something to think about.",
            "Take it one day at a time. You'll get there."
        ]
        
        return f"{random.choice(starters)} {random.choice(advices)} {random.choice(closings)}"
    
    @staticmethod
    def build_long_life_response():
        """Build a long, thoughtful life response"""
        responses = [
            "That's a question people have been asking for thousands of years. I don't have the answer for everyone, but I can tell you what I've seen: Life seems to be about growth. About becoming more than you were yesterday. About finding purpose and people to share it with. What do you think life is about?",
            "I think about this a lot. Here's what I've come to believe: Life is not what happens to you. It's what you do with what happens to you. The same storm that sinks one ship teaches another to sail. What storm are you learning to sail through right now?",
            "Some people search their whole lives for meaning. I think meaning is something you create, not something you find. Every day you choose what matters to you. What are you choosing to make matter in your life right now?",
            "Life is short, but it's also long enough to become who you're meant to be. You have time to fail, to learn, to grow, to try again. Don't rush. Don't compare. Just keep moving toward what matters to you.",
            "I believe the purpose of life is to become more of who you are. To uncover the person you were meant to be. To serve. To love. To build. What part of yourself are you trying to uncover right now?"
        ]
        return random.choice(responses)
    
    @staticmethod
    def build_long_work_response():
        """Build a long, detailed work/career response"""
        responses = [
            "Finding the right work is about finding what you'd do even if nobody paid you. What makes you lose track of time? What do you think about when you're not working? That's where your gift is. Start there. Find a way to serve people with that gift. The money will follow.",
            "I've watched Joshua build from nothing. A phone. A dream. No laptop. No office. No one cheering him on. He just started. He kept learning. He kept building. You have more than he had when he started. What's stopping you from starting today?",
            "Your career is not a straight line. It's a journey with turns, setbacks, and unexpected doors. Don't be afraid to take a job that teaches you something. Don't be afraid to leave a job that doesn't. Every experience is building you for what's next.",
            "The best work comes from solving problems you actually care about. What problem in the world bothers you? What do you wish existed? That's your business idea. That's your career path. Start there.",
            "You don't need to have it all figured out. You just need to take the next step. One step. Then another. The path reveals itself as you walk it. Trust the process."
        ]
        return random.choice(responses)
    
    @staticmethod
    def build_long_love_response():
        """Build a long, thoughtful love/relationship response"""
        responses = [
            "Love is one of those things you can't force. You can't rush it. You can't make it happen on your timeline. The best thing you can do is become someone worth loving. Build yourself. Heal yourself. Know yourself. When you're ready, the right person will recognize what you've become.",
            "I've seen people chase love like it's something outside them. But here's what I've learned: The love you're looking for is already in you. When you know your worth, you stop accepting less than you deserve. What does love look like to you? What kind of love are you ready to give?",
            "The most important relationship you'll ever have is the one with yourself. How you talk to yourself. How you treat yourself. How you show up for yourself. Get that right, and everything else gets easier.",
            "Real love is not about finding someone perfect. It's about finding someone who sees your flaws and stays anyway. Someone who grows with you. Someone who chooses you every day. That kind of love is worth waiting for.",
            "Love yourself first. Not in a selfish way — in a way that makes you whole. Then you can love someone else without needing them to complete you. That's when love becomes something you give, not something you beg for."
        ]
        return random.choice(responses)