"""JAI - WhatsApp Channel Learner
Specifically designed for Master's Mindset motivational content.
"""

import os
import re
import json
import logging
import sqlite3
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)

class WhatsAppLearner:
    """Learn motivational content from Master's Mindset channel"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.setup_tables()
    
    def setup_tables(self):
        """Create tables for storing learned content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # Table for Master's Mindset posts
            cur.execute('''
                CREATE TABLE IF NOT EXISTS masters_mindset_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    content TEXT,
                    category TEXT,
                    key_themes TEXT,
                    learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for motivational quotes
            cur.execute('''
                CREATE TABLE IF NOT EXISTS motivational_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote_text TEXT,
                    category TEXT,
                    source TEXT,
                    times_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table for key principles
            cur.execute('''
                CREATE TABLE IF NOT EXISTS key_principles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    principle TEXT,
                    explanation TEXT,
                    category TEXT,
                    times_shared INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Master's Mindset learner tables ready")
        except Exception as e:
            logger.error(f"Error setting up tables: {e}")
    
    def learn_from_masters_mindset(self, posts):
        """Learn from Master's Mindset posts"""
        learned_count = 0
        quotes = []
        principles = []
        
        for post in posts:
            # Extract title
            title_match = re.search(r'#?\s*(.+?)(?:\n|$)', post.get('title', ''))
            title = title_match.group(1).strip() if title_match else "Untitled"
            
            content = post.get('content', '')
            
            # Extract key themes
            themes = self.extract_themes(content)
            
            # Save post
            self.save_post(title, content, themes)
            
            # Extract and save quotes
            post_quotes = self.extract_quotes(content)
            for quote in post_quotes:
                self.save_quote(quote, post.get('category', 'general'))
                quotes.append(quote)
                learned_count += 1
            
            # Extract key principles
            principles_found = self.extract_principles(content, title)
            for principle in principles_found:
                self.save_principle(principle, content)
                principles.append(principle)
                learned_count += 1
        
        return {
            "success": True,
            "message": f"Learned {learned_count} motivational pieces",
            "posts": len(posts),
            "quotes": len(quotes),
            "principles": len(principles),
            "themes": self.get_common_themes()
        }
    
    def extract_themes(self, content):
        """Extract key themes from content"""
        themes = []
        content_lower = content.lower()
        
        theme_patterns = {
            'loneliness': ['lonely', 'no friends', 'distance', 'oversabi'],
            'faith': ['faith', 'god', 'prayer', 'believer', 'christian'],
            'perseverance': ['keep going', 'don\'t give up', 'persist', 'continue'],
            'success': ['success', 'make it', 'top', 'achieve', 'accomplish'],
            'integrity': ['bad business', 'wrong', 'harmful', 'principle'],
            'sacrifice': ['price', 'pay', 'loneliness is the price'],
            'vision': ['see what', 'vision', 'future you envision'],
            'hustle': ['hustle', 'grind', 'build', 'work']
        }
        
        for theme, keywords in theme_patterns.items():
            if any(keyword in content_lower for keyword in keywords):
                themes.append(theme)
        
        return ','.join(set(themes))
    
    def extract_quotes(self, content):
        """Extract powerful quotes from content"""
        quotes = []
        
        # Split into lines and paragraphs
        lines = content.split('\n')
        
        # Look for powerful statements
        powerful_indicators = [
            r'but here\'s what I want you to hear',
            r'here\'s what I\'ve learned',
            r'my mind tells me',
            r'success demands',
            r'you cannot build what I\'m building',
            r'loneliness is the price',
            r'keep going',
            r'every master was once a beginner',
            r'the seed does not see its growth'
        ]
        
        # Extract specific quotes from your content
        for line in lines:
            line = line.strip()
            if len(line) > 30 and len(line) < 300:
                # Check if it's a powerful statement
                if any(re.search(indicator, line.lower()) for indicator in powerful_indicators):
                    quotes.append(line)
                # Check for quotes with dashes or em-dashes
                elif '—' in line or '"' in line or "'" in line:
                    quotes.append(line)
        
        # Extract specific known quotes from Master's Mindset
        known_quotes = [
            "The very thing they mock is the very thing that will carry me where they cannot follow.",
            "You cannot build what I'm building and think like the crowd.",
            "You cannot go where I'm going and move at their pace.",
            "Loneliness is the price you pay for the future you envision.",
            "In his mind, poverty was the identifier of faith.",
            "Success demands oversabi.",
            "The seed does not see its growth underground. But roots are spreading.",
            "Don't go into a bad business just because it promises quick money.",
            "Boring days are not wasted days. They are foundation days."
        ]
        
        for quote in known_quotes:
            if quote.lower() in content.lower():
                quotes.append(quote)
        
        return list(set(quotes))  # Remove duplicates
    
    def extract_principles(self, content, title):
        """Extract key principles from content"""
        principles = []
        
        # Principle 1: The Oversabi Principle
        if 'oversabi' in content.lower():
            principles.append({
                'principle': "The Oversabi Principle",
                'explanation': "Being called 'oversabi' means you think differently, see further, and refuse to settle. It's not a weakness—it's the price of greatness.",
                'category': 'mindset'
            })
        
        # Principle 2: Faith vs Poverty
        if 'poverty was the identifier of faith' in content.lower():
            principles.append({
                'principle': "Faith Should Not Equal Poverty",
                'explanation': "The people who serve the God of the universe—the One who owns everything—should never be identified by lack. Faith should elevate, not diminish.",
                'category': 'spiritual'
            })
        
        # Principle 3: Integrity Over Quick Money
        if 'bad business' in content.lower() or 'quick money' in content.lower():
            principles.append({
                'principle': "Integrity Over Quick Money",
                'explanation': "Don't build what you wouldn't accept. Quick money from harmful sources will cost you more than it gives.",
                'category': 'ethics'
            })
        
        # Principle 4: The Loneliness of Vision
        if 'lonely' in content.lower() or 'loneliness is the price' in content.lower():
            principles.append({
                'principle': "The Loneliness of Vision",
                'explanation': "Great vision often walks alone. Being misunderstood, mocked, or distanced doesn't mean you're wrong—it means you're ahead.",
                'category': 'perspective'
            })
        
        # Principle 5: Boring Days Build
        if 'boring days' in content.lower() or 'foundation days' in content.lower():
            principles.append({
                'principle': "Boring Days Are Foundation Days",
                'explanation': "When nothing seems to move, growth is happening underground. Boring days are not wasted—they're when roots spread.",
                'category': 'perseverance'
            })
        
        return principles
    
    def save_post(self, title, content, themes):
        """Save post to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO masters_mindset_posts (title, content, key_themes)
                VALUES (?, ?, ?)
            ''', (title[:200], content[:5000], themes))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False
    
    def save_quote(self, quote, category):
        """Save motivational quote"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO motivational_quotes (quote_text, category)
                VALUES (?, ?)
            ''', (quote[:500], category))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving quote: {e}")
            return False
    
    def save_principle(self, principle, content):
        """Save key principle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                INSERT INTO key_principles (principle, explanation, category)
                VALUES (?, ?, ?)
            ''', (principle['principle'], principle['explanation'], principle['category']))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving principle: {e}")
            return False
    
    def get_motivational_response(self, context=""):
        """Get a motivational response based on Master's Mindset content"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Try to get a quote first (weighted by usage)
            cur.execute('''
                SELECT quote_text FROM motivational_quotes 
                ORDER BY times_used ASC, RANDOM()
                LIMIT 1
            ''')
            
            quote = cur.fetchone()
            if quote:
                # Update usage
                cur.execute('''
                    UPDATE motivational_quotes 
                    SET times_used = times_used + 1 
                    WHERE quote_text = ?
                ''', (quote['quote_text'],))
                conn.commit()
                conn.close()
                return f"✨ From Master's Mindset:\n\n\"{quote['quote_text']}\""
            
            # Try to get a principle
            cur.execute('''
                SELECT principle, explanation FROM key_principles 
                ORDER BY times_shared ASC, RANDOM()
                LIMIT 1
            ''')
            
            principle = cur.fetchone()
            if principle:
                cur.execute('''
                    UPDATE key_principles 
                    SET times_shared = times_shared + 1 
                    WHERE principle = ?
                ''', (principle['principle'],))
                conn.commit()
                conn.close()
                return f"💪 Master's Mindset Principle: {principle['principle']}\n\n{principle['explanation']}"
            
            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting motivational response: {e}")
            return None
    
    def get_quote_by_theme(self, theme):
        """Get a quote related to a specific theme"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # This would need theme tagging - simplified for now
            cur.execute('''
                SELECT quote_text FROM motivational_quotes 
                ORDER BY RANDOM()
                LIMIT 1
            ''')
            
            quote = cur.fetchone()
            conn.close()
            return quote['quote_text'] if quote else None
        except Exception as e:
            logger.error(f"Error getting quote by theme: {e}")
            return None
    
    def get_common_themes(self):
        """Get most common themes from learned content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute('''
                SELECT key_themes FROM masters_mindset_posts
                WHERE key_themes IS NOT NULL
            ''')
            
            all_themes = []
            for row in cur.fetchall():
                if row[0]:
                    themes = row[0].split(',')
                    all_themes.extend(themes)
            
            theme_counts = Counter(all_themes)
            conn.close()
            
            return dict(theme_counts.most_common(5))
        except Exception as e:
            logger.error(f"Error getting common themes: {e}")
            return {}
    
    def get_statistics(self):
        """Get learning statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            stats = {}
            
            cur.execute('SELECT COUNT(*) FROM masters_mindset_posts')
            stats['total_posts'] = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM motivational_quotes')
            stats['total_quotes'] = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM key_principles')
            stats['total_principles'] = cur.fetchone()[0]
            
            # Get most used quotes
            cur.execute('''
                SELECT quote_text, times_used FROM motivational_quotes 
                WHERE times_used > 0
                ORDER BY times_used DESC LIMIT 3
            ''')
            stats['popular_quotes'] = [{'quote': row[0][:100], 'times': row[1]} for row in cur.fetchall()]
            
            conn.close()
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}