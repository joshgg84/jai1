# masters_mindset.py
"""Master's Mindset WhatsApp Channel Importer
Specifically designed for the Master's Mindset channel format.
"""

import re
import requests
import json
import time
import os
from datetime import datetime

class MastersMindsetImporter:
    """Import Master's Mindset channel content into JAI"""
    
    def __init__(self, jai_api_url, client_id="masters_mindset"):
        """
        Initialize the importer
        
        Args:
            jai_api_url: Your JAI API URL
            client_id: Identifier for this importer
        """
        self.api_url = jai_api_url
        self.client_id = client_id
        self.imported_posts = []
        self.errors = []
    
    def parse_channel_content(self, text):
        """
        Parse Master's Mindset channel content from text
        
        Handles format like:
        # Master's Mindset
        7 followers
        
        ---
        
        But my mind tells:  
        demands oversa  
        The very thing that will ca cannot follow.  
        
        You cannot build and think like the go where I'm goi pace. 
        
        ---
        
        Loneliness is the price you pay for the future you envision.  
        
        So don't be discouraged...
        """
        
        posts = []
        
        # Split by the separator (---)
        sections = re.split(r'\n---+\n', text)
        
        current_post = None
        current_content = []
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Skip channel metadata section
            if 'Master\'s Mindset' in section and 'followers' in section:
                continue
            
            # Skip insights section
            if 'Insights for last' in section or 'Accounts reached' in section:
                continue
            
            # Skip media section
            if 'Media and links' in section:
                continue
            
            # This is content - check if it's a new post or continuation
            lines = section.split('\n')
            
            # Check if this section has a title-like structure
            if lines[0].startswith('#') or lines[0].startswith('**') or (lines[0].isupper() and len(lines[0]) > 10):
                # New post detected
                if current_post and current_content:
                    # Save previous post
                    posts.append({
                        'title': current_post,
                        'content': '\n'.join(current_content).strip(),
                        'date': datetime.now().strftime("%m/%d/%Y")
                    })
                
                # Start new post
                current_post = lines[0].strip('#').strip('*').strip()
                current_content = lines[1:] if len(lines) > 1 else []
            else:
                # Add to current post content
                if current_content is not None:
                    current_content.extend(lines)
                else:
                    # No current post, start one
                    current_post = "Master's Mindset Wisdom"
                    current_content = lines
        
        # Add the last post
        if current_post and current_content:
            posts.append({
                'title': current_post,
                'content': '\n'.join(current_content).strip(),
                'date': datetime.now().strftime("%m/%d/%Y")
            })
        
        return posts
    
    def extract_quotes_from_content(self, content):
        """Extract powerful quotes from Master's Mindset content"""
        quotes = []
        
        # Split into lines
        lines = content.split('\n')
        
        # Look for lines that are powerful statements
        for line in lines:
            line = line.strip()
            if not line or len(line) < 15:
                continue
            
            # Check for Master's Mindset signature phrases
            if any(phrase in line.lower() for phrase in [
                'my mind tells me',
                'success demands',
                'the very thing they mock',
                'you cannot build',
                'you cannot go where',
                'loneliness is the price',
                'don\'t be discouraged',
                'oversabi'
            ]):
                quotes.append(line)
            
            # Check for lines with special formatting
            elif line.startswith('—') or line.startswith('*') or line.startswith('>'):
                quotes.append(line.lstrip('—*> '))
            
            # Check for lines that are complete thoughts
            elif len(line) > 40 and line.endswith('.') and ' ' in line:
                quotes.append(line)
        
        # Clean quotes
        cleaned_quotes = []
        for q in quotes:
            # Remove any "Read more" text
            q = re.sub(r'Read more\.\.\.$', '', q)
            q = q.strip()
            if q and len(q) > 10:
                cleaned_quotes.append(q)
        
        # Remove duplicates
        seen = set()
        unique_quotes = []
        for q in cleaned_quotes:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_quotes.append(q)
        
        return unique_quotes[:15]  # Limit to top 15 quotes
    
    def clean_content(self, content):
        """Clean and format content for JAI"""
        # Remove "Read more" links
        content = re.sub(r'Read more\.\.\.\s*$', '', content, flags=re.IGNORECASE)
        
        # Remove markdown formatting
        content = re.sub(r'\*\*', '', content)
        content = re.sub(r'#+\s*', '', content)
        
        # Clean up line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove empty lines at start and end
        content = content.strip()
        
        return content
    
    def format_for_jai(self, post):
        """Format post into JAI teaching message"""
        # Clean content
        content = self.clean_content(post['content'])
        
        # Extract quotes
        quotes = self.extract_quotes_from_content(content)
        
        # Build message with clear formatting
        message = f"add post: {post['title']}\n\n"
        message += content
        
        # Add quotes as key takeaways
        if quotes:
            message += "\n\n---\n📌 **Key Takeaways:**\n"
            for i, quote in enumerate(quotes[:5], 1):
                message += f"{i}. \"{quote}\"\n"
        
        return message
    
    def send_to_jai(self, post):
        """Send a single post to JAI"""
        message = self.format_for_jai(post)
        
        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={
                    "message": message,
                    "clientId": self.client_id,
                    "options": {}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'title': post['title'],
                    'quotes_found': len(self.extract_quotes_from_content(post['content'])),
                    'response': response.json()
                }
            else:
                return {
                    'success': False,
                    'title': post['title'],
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'title': post['title'],
                'error': str(e)
            }
    
    def import_from_text(self, text, delay=1):
        """Import posts directly from text"""
        
        # Parse content
        posts = self.parse_channel_content(text)
        
        if not posts:
            return {
                'success': False,
                'error': "No posts found in the text"
            }
        
        print(f"\n📊 Found {len(posts)} posts")
        
        # Import all posts
        results = []
        
        for i, post in enumerate(posts, 1):
            print(f"\n[{i}/{len(posts)}] 📝 {post['title']}")
            
            # Send to JAI
            result = self.send_to_jai(post)
            
            if result['success']:
                print(f"   ✅ Learned! ({result['quotes_found']} quotes extracted)")
                results.append(result)
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                self.errors.append(result)
            
            # Delay to avoid overwhelming
            if i < len(posts):
                time.sleep(delay)
        
        return {
            'success': True,
            'total_posts': len(posts),
            'imported': len(results),
            'failed': len(posts) - len(results),
            'results': results
        }
    
    def import_from_file(self, filepath, delay=1):
        """Import posts from a text file"""
        
        if not os.path.exists(filepath):
            return {
                'success': False,
                'error': f"File not found: {filepath}"
            }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return self.import_from_text(text, delay)

# ========== USAGE ==========

if __name__ == "__main__":
    # Configuration
    JAI_URL = "http://localhost:5001"  # Change to your JAI URL
    
    # Initialize importer
    importer = MastersMindsetImporter(JAI_URL)
    
    # Your Master's Mindset content (paste from screenshots)
    content = """# Master's Mindset
7 followers

---

But my mind tells me: success demands oversabi.

The very thing they mock is the very thing that will carry me where they cannot follow.

You cannot build what I'm building and think like the crowd. You cannot go where I'm going and move at their pace. You cannot see what I see and be understood by those who refuse to look up.

---

Loneliness is the price you pay for the future you envision.

So don't be discouraged. Don't think that because nobody is applauding your process, you must be doing something wrong.
"""
    
    # Import the content
    print("🚀 Importing Master's Mindset content to JAI...")
    print("=" * 50)
    
    result = importer.import_from_text(content)
    
    if result['success']:
        print("\n" + "=" * 50)
        print("✅ IMPORT COMPLETE")
        print("=" * 50)
        print(f"📚 Posts imported: {result['imported']}/{result['total_posts']}")
        print("\n🎯 Now ask JAI:")
        print("   • 'motivate me' - Get inspiration")
        print("   • 'what is oversabi' - Learn the concept")
        print("   • 'tell me about loneliness and vision'")
        print("   • 'motivation stats' - See what I've learned")
    else:
        print(f"\n❌ Error: {result.get('error')}")