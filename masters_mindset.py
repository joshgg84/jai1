# masters_mindset.py
"""Master's Mindset WhatsApp Channel Importer
Imports your motivational posts into JAI for learning.
"""

import re
import requests
import json
import time
import os
from datetime import datetime

class MastersMindsetImporter:
    """Import Master's Mindset channel exports into JAI"""
    
    def __init__(self, jai_api_url, client_id="masters_mindset"):
        """
        Initialize the importer
        
        Args:
            jai_api_url: Your JAI API URL (e.g., http://localhost:5001 or https://your-app.onrender.com)
            client_id: Identifier for this importer
        """
        self.api_url = jai_api_url
        self.client_id = client_id
        self.imported_posts = []
        self.errors = []
    
    def parse_whatsapp_export(self, export_text):
        """
        Parse WhatsApp channel export into structured posts
        
        Expected format:
        2/15/2024, 9:30 AM - Title Here
        Content lines...
        More content...
        
        2/16/2024, 2:15 PM - Another Title
        More content...
        """
        
        posts = []
        
        # Pattern to match: date, time, dash, title
        # Matches: 2/15/2024, 9:30 AM - Title
        pattern = r'(\d{1,2}/\d{1,2}/\d{4}),?\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(.+?)(?=\n\d{1,2}/\d{1,2}/\d{4}|\Z)'
        
        matches = re.finditer(pattern, export_text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            date_str = match.group(1)
            time_str = match.group(2)
            title = match.group(3).strip()
            
            # Get content (everything after title until next date or end)
            start_pos = match.end()
            remaining = export_text[start_pos:]
            
            # Find next date to know where content ends
            next_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', remaining)
            if next_date:
                end_pos = start_pos + next_date.start()
                content = export_text[start_pos:end_pos].strip()
            else:
                content = remaining.strip()
            
            # Clean up content
            content = self.clean_content(content)
            
            if content and len(content) > 20:  # Only import meaningful content
                posts.append({
                    'title': title,
                    'date': f"{date_str} {time_str}",
                    'content': content,
                    'word_count': len(content.split()),
                    'char_count': len(content)
                })
        
        return posts
    
    def clean_content(self, content):
        """Clean and format post content for JAI"""
        # Remove extra whitespace
        content = content.strip()
        
        # Remove "Read more" links
        content = re.sub(r'Read more\.\.\.\s*$', '', content, flags=re.IGNORECASE)
        
        # Normalize line breaks (keep structure but remove excessive empty lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove WhatsApp timestamps that might appear in content
        content = re.sub(r'\d{1,2}:\d{2}\s*[AP]M', '', content)
        
        # Remove "Master's Mindset" repeated lines
        content = re.sub(r'Master\'s Mindset\s*\d+\s*followers', '', content, flags=re.IGNORECASE)
        
        # Remove the "Read more" at the end
        content = re.sub(r'\.{3,}\s*$', '', content)
        
        return content.strip()
    
    def extract_quotes(self, content):
        """Extract powerful quotes from post content"""
        quotes = []
        
        # Extract quotes in quotes
        quoted = re.findall(r'["\']([^"\']+)["\']', content)
        quotes.extend(quoted)
        
        # Extract dash-separated wisdom
        dash_sections = re.findall(r'—\s*\n(.+?)(?=\n—|\n\n|$)', content, re.DOTALL)
        for section in dash_sections:
            for line in section.strip().split('\n'):
                if len(line) > 20 and len(line) < 300:
                    quotes.append(line.strip())
        
        # Extract powerful statements with common Master's Mindset phrases
        patterns = [
            r'but here\'s what I want you to hear:?\s*(.+?)(?=\n|$)',
            r'here\'s what I\'ve learned:?\s*(.+?)(?=\n|$)',
            r'my mind tells me:?\s*(.+?)(?=\n|$)',
            r'success demands:?\s*(.+?)(?=\n|$)',
            r'you cannot build what I\'m building[:\s]*(.+?)(?=\n|$)',
            r'loneliness is the price[:\s]*(.+?)(?=\n|$)',
            r'the very thing they mock[:\s]*(.+?)(?=\n|$)',
            r'don\'t do that[:\s]*(.+?)(?=\n|$)',
            r'faith was never meant[:\s]*(.+?)(?=\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned = match.strip()
                if len(cleaned) > 20 and len(cleaned) < 300:
                    quotes.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_quotes = []
        for q in quotes:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_quotes.append(q)
        
        return unique_quotes[:10]  # Limit to top 10 quotes per post
    
    def format_for_jai(self, post):
        """Format post into JAI teaching message"""
        # Extract quotes for additional teaching
        quotes = self.extract_quotes(post['content'])
        
        # Build message
        message = f"add post: {post['title']}\n\n{post['content']}"
        
        # Add quotes as separate teaching if they're valuable
        for quote in quotes:
            message += f"\n\n📌 Quote: {quote}"
        
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
                    'response': response.json()
                }
            else:
                return {
                    'success': False,
                    'title': post['title'],
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'title': post['title'],
                'error': str(e)
            }
    
    def import_all_posts(self, posts, delay=1):
        """Import all posts to JAI with delay between requests"""
        
        results = []
        
        print(f"\n📚 Importing {len(posts)} posts to JAI...")
        print("=" * 60)
        
        for i, post in enumerate(posts, 1):
            print(f"\n[{i}/{len(posts)}] 📝 {post['title']}")
            print(f"   📊 {post['word_count']} words, {post['char_count']} chars")
            
            # Send to JAI
            result = self.send_to_jai(post)
            
            if result['success']:
                print(f"   ✅ Successfully learned!")
                results.append(result)
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                self.errors.append(result)
            
            # Delay to avoid overwhelming the server
            if i < len(posts):
                time.sleep(delay)
        
        return results
    
    def import_from_file(self, filepath, delay=1):
        """
        Import posts from a WhatsApp export file
        
        Args:
            filepath: Path to the exported text file
            delay: Seconds between requests (default 1)
        
        Returns:
            Dictionary with import statistics
        """
        
        # Check if file exists
        if not os.path.exists(filepath):
            return {
                'success': False,
                'error': f"File not found: {filepath}"
            }
        
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            export_text = f.read()
        
        # Parse posts
        posts = self.parse_whatsapp_export(export_text)
        
        if not posts:
            return {
                'success': False,
                'error': "No posts found in the export file"
            }
        
        print(f"📊 Found {len(posts)} posts in {filepath}")
        
        # Import all posts
        results = self.import_all_posts(posts, delay)
        
        # Generate summary
        success_count = len([r for r in results if r['success']])
        
        summary = {
            'success': True,
            'file': filepath,
            'total_posts': len(posts),
            'imported': success_count,
            'failed': len(posts) - success_count,
            'errors': self.errors,
            'posts': results
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 IMPORT SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully imported: {success_count}/{len(posts)} posts")
        print(f"❌ Failed: {len(posts) - success_count} posts")
        
        if self.errors:
            print("\n⚠️ Errors:")
            for error in self.errors:
                print(f"   - {error['title']}: {error['error']}")
        
        # Save results to file
        output_file = f"import_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        return summary
    
    def preview_file(self, filepath, num_posts=3):
        """Preview first N posts without importing"""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            export_text = f.read()
        
        posts = self.parse_whatsapp_export(export_text)
        
        print(f"\n📋 Preview of first {min(num_posts, len(posts))} posts:")
        print("=" * 60)
        
        for i, post in enumerate(posts[:num_posts], 1):
            print(f"\n📝 Post {i}: {post['title']}")
            print(f"📅 Date: {post['date']}")
            print(f"📊 Size: {post['word_count']} words, {post['char_count']} chars")
            print("\nContent preview:")
            print("-" * 40)
            print(post['content'][:300] + "..." if len(post['content']) > 300 else post['content'])
            print("-" * 40)
        
        return posts

# ========== USAGE EXAMPLES ==========

if __name__ == "__main__":
    
    # Configuration
    JAI_URL = "https://your-jai-app.onrender.com"  # Replace with your JAI URL
    # For local testing: JAI_URL = "http://localhost:5001"
    
    # Initialize importer
    importer = MastersMindsetImporter(JAI_URL)
    
    # Option 1: Preview your export file first
    print("🔍 Previewing export file...")
    importer.preview_file("whatsapp_export.txt", num_posts=2)
    
    # Option 2: Import all posts
    print("\n" + "=" * 60)
    response = input("Ready to import? (yes/no): ")
    
    if response.lower() == 'yes':
        # Import all posts
        results = importer.import_from_file("whatsapp_export.txt", delay=1)
        
        if results['success']:
            print("\n🎉 All posts successfully imported into JAI!")
            print("\nNow you can ask JAI:")
            print("  • 'motivate me' - Get random wisdom")
            print("  • 'motivation stats' - See what JAI learned")
            print("  • 'what have you learned' - Check imported content")
    
    # Option 3: Import specific post by copying directly
    # single_post = """
    # Everything Bows to Faith
    # 
    # I heard something that broke me...
    # """
    # 
    # post = {
    #     'title': 'Everything Bows to Faith',
    #     'content': single_post,
    #     'date': datetime.now().strftime("%m/%d/%Y %I:%M %p")
    # }
    # importer.import_all_posts([post])