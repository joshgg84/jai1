"""JAI - Creative Writer Module
Handles creative writing tasks: love letters, poems, stories.
"""

import re
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CreativeWriter:
    """Creative writing assistance for love letters, poems, and stories"""
    
    @staticmethod
    def detect_creative_request(message):
        """Detect if user is asking for creative writing help"""
        msg_lower = message.lower()
        
        creative_keywords = {
            'love_letter': ['love letter', 'love note', 'romantic letter', 'write to my love', 'letter to my girlfriend', 'letter to my boyfriend', 'letter to my wife', 'letter to my husband'],
            'poem': ['write a poem', 'poem about', 'romantic poem', 'love poem', 'poetry'],
            'story': ['write a story', 'short story', 'creative story', 'tell a story']
        }
        
        for task, keywords in creative_keywords.items():
            for keyword in keywords:
                if keyword in msg_lower:
                    return task, message
        return None, None
    
    @staticmethod
    def generate_love_letter(context):
        """Generate a romantic love letter"""
        context.setdefault('recipient', 'My Love')
        context.setdefault('name', 'Your Name')
        context.setdefault('memories', 'all the beautiful moments we have shared')
        context.setdefault('qualities', 'your kindness, your smile, and the way you make me feel')
        
        # Different styles of love letters
        styles = ["romantic", "poetic", "simple", "deep"]
        style = context.get('style', random.choice(styles))
        
        if style == "poetic":
            letter = f"""💌 **A Love Letter for {context['recipient']}**

My Dearest {context['recipient']},

The sun rises and sets in your eyes. 
Every breath I take is filled with thoughts of you.
Your love is the poetry my soul has always longed to write.

{context['memories']} have painted my world in colors I never knew existed.
{context['qualities']} remind me daily of how blessed I am.

In a world full of temporary things, my love for you is eternal.
You are my home, my heart, my everything.

Forever yours,
{context['name']}

---
✨ *Want me to adjust the tone or add specific memories? Just tell me!*"""
        
        elif style == "deep":
            letter = f"""💌 **A Love Letter for {context['recipient']}**

My Beloved {context['recipient']},

I've been trying to find the right words to express what you mean to me, but I've realized that no words are truly enough. What I feel for you transcends language.

You came into my life and changed everything. The way you understand me, support me, and love me has made me a better person. {context['qualities']} are just a few of the million reasons I love you.

{context['memories']} are treasures I hold close to my heart. Every moment with you is a gift I never take for granted.

I promise to love you, honor you, and stand by you through every season of life. You are my greatest adventure and my safest harbor.

With all my love,
{context['name']}

---
✨ *Want me to adjust the tone or add specific memories? Just tell me!*"""
        
        else:  # romantic or simple
            letter = f"""💌 **A Love Letter for {context['recipient']}**

My Dearest {context['recipient']},

From the moment we met, something in my heart shifted. I didn't know what love truly was until I experienced it with you.

Every day, I find myself grateful for your presence in my life. Your smile brightens my darkest days, and your laughter is the sweetest melody I've ever heard. {context['qualities']}

{context['memories']} remind me of how lucky I am to have you.

I don't know what the future holds, but I know I want you in it. I want to share sunsets, adventures, quiet mornings, and everything in between with you.

Thank you for being you. Thank you for your love, your patience, and your beautiful soul.

Yours always and forever,
{context['name']}

---
✨ *Want me to adjust the tone or add specific memories? Just tell me!*"""
        
        return letter
    
    @staticmethod
    def generate_poem(context):
        """Generate a romantic poem"""
        context.setdefault('topic', 'love')
        context.setdefault('recipient', 'you')
        
        poems = [
            f"""🌹 **A Poem for {context['recipient']}**

In the quiet of the morning light,
I think of you, my heart's delight.
Your love surrounds me, warm and true,
There's nothing else I'd rather do.

Each day with you is like a song,
A melody where I belong.
Your laughter echoes in the air,
A gentle promise, love and care.

So here's my heart, I give it free,
Forever yours, you'll always be.
{context['recipient']}, my love, my everything,
You are the joy that makes me sing.

---
✨ *Want a different style of poem? Let me know!*""",
            
            f"""💕 **A Short Love Poem**

Roses are red,
Violets are blue,
Every day I wake up,
I'm thankful for {context['recipient']}.

Your smile shines bright,
Like stars above,
{context['recipient']}, you are,
My one true love.

---
✨ *Want a longer or different poem? Just ask!*""",
            
            f"""✨ **A Whisper of Love**

I carry your heart with me,
Every step, every breath.
In the silence between words,
I hear your name.

{context['recipient']}, you are
The poetry I never knew
I was writing.

---
✨ *Want more poems? Ask for another style!*"""
        ]
        
        return random.choice(poems)
    
    @staticmethod
    def generate_story(context):
        """Generate a short story"""
        context.setdefault('genre', 'romance')
        context.setdefault('character', 'a young dreamer')
        context.setdefault('setting', 'a small town by the sea')
        
        stories = [
            f"""📖 **A Short Story**

Once upon a time, in {context['setting']}, there lived {context['character']}.

Every day brought new adventures and challenges, but our hero never gave up. With courage in their heart and hope in their eyes, they faced whatever came their way.

The story reminds us that no matter where we come from, we all have the power to create something beautiful. Love, friendship, and determination can move mountains.

And so, our story continues, because every ending is just a new beginning.

---
✨ *Want me to write a specific type of story? Tell me the genre and characters!*""",
            
            f"""📖 **A Love Story**

In the heart of {context['setting']}, two souls were destined to meet. {context['character']} never expected to find love, but fate had other plans.

Their journey together was filled with laughter, tears, and moments that would last a lifetime. Through every challenge, their bond grew stronger.

This is a reminder that love finds us when we least expect it, and when it does, it changes everything.

---
✨ *Want a different story? Tell me what you'd like to read!*"""
        ]
        
        return random.choice(stories)
    
    @staticmethod
    def generate_response(task, user_message):
        """Generate a response based on detected creative writing task"""
        msg_lower = user_message.lower()
        
        # Extract key information from user message
        context = {}
        
        # Extract recipient name for love letters
        recipient_match = re.search(r'(?:to|for)\s+([A-Za-z\s]+?)(?:\s+about|\s+from|$|\.)', msg_lower)
        if recipient_match:
            context['recipient'] = recipient_match.group(1).strip().title()
        else:
            context['recipient'] = 'My Love'
        
        # Extract topic for poems
        topic_match = re.search(r'(?:about|for)\s+([A-Za-z\s]+?)(?:\?|$| please)', msg_lower)
        if topic_match and task == 'poem':
            context['topic'] = topic_match.group(1).strip()
        
        if task == 'love_letter':
            return CreativeWriter.generate_love_letter(context)
        
        elif task == 'poem':
            return CreativeWriter.generate_poem(context)
        
        elif task == 'story':
            return CreativeWriter.generate_story(context)
        
        else:
            return CreativeWriter.get_creative_help()
    
    @staticmethod
    def get_creative_help():
        """Provide help message for creative writing"""
        return """🎨 **Creative Writing Assistant**

I can help you write:

💌 **Love Letters** - Romantic letters for your special someone
🌹 **Poems** - Romantic and heartfelt poems
📖 **Short Stories** - Creative stories

**Try saying:**
• "Write a love letter to Rebecca"
• "Write a poem about love"
• "Tell me a short story"
• "Write a romantic letter to my girlfriend"

What would you like me to create today?"""


class CreativeWriterHandler:
    """Handler for creative writing requests in the main chat"""
    
    @staticmethod
    def handle_creative_request(message):
        """Process creative writing requests from users"""
        task, user_message = CreativeWriter.detect_creative_request(message)
        
        if task:
            return CreativeWriter.generate_response(task, user_message)
        
        return None
    
    @staticmethod
    def is_creative_request(message):
        """Check if message is a creative writing request"""
        creative_indicators = [
            'love letter', 'love note', 'romantic letter',
            'poem', 'poetry', 'short story', 'tell a story'
        ]
        msg_lower = message.lower()
        return any(indicator in msg_lower for indicator in creative_indicators)
    
    @staticmethod
    def get_creative_help():
        """Get creative writing help message"""
        return CreativeWriter.get_creative_help()