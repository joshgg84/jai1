# master_mindset_importer.py
"""Intelligent importer for Master's Mindset WhatsApp exports"""

import re
import requests
import json
from datetime import datetime

class MasterMindsetImporter:
    """Import Master's Mindset channel exports into JAI"""
    
    def __init__(self, jai_api_url, client_id="master_mindset"):
        self.api_url = jai_api_url
        self.client_id = client_id
    
    def parse_whatsapp_export(self, export_text):
        """Parse WhatsApp channel export into structured posts"""
        
        posts = []
        
        # Split by date patterns (WhatsApp export format)
        # Pattern matches: 2/15/2024, 9:30 AM - Title
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4}),?\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*(.+?)(?=\n\n|\Z)'
        
        # Find all posts with their dates
        matches = re.finditer(date_pattern, export_text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            date_str = match.group(1)
            time_str = match.group(2)
            title = match.group(3).strip()
            
            # Find the content after the title
            start_pos = match.end()
            
            # Find next date or end of text
            next_date = re.search(r'\d{1,2}/\d{1,2}/\d{4}', export_text[start_pos:])
            if next_date:
                end_pos = start_pos + next_date.start()
            else:
                end_pos = len(export_text)
            
            content = export_text[start_pos:end_pos].strip()
            
            # Clean up content
            content = self.clean_content(content)
            
            posts.append({
                'title': title,
                'date': f"{date_str} {time_str}",
                'content': content,
                'word_count': len(content.split())
            })
        
        return posts
    
    def clean_content(self, content):
        """Clean and format post content"""
        # Remove empty lines at start/end
        content = content.strip()
        
        # Remove the "Read more" text
        content = re.sub(r'Read more\.\.\.\s*$', '', content)
        
        # Clean up multiple newlines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        return content
    
    def extract_quotes_from_content(self, content):
        """Extract powerful quotes from post content"""
        quotes = []
        
        # Look for quoted text
        quoted = re.findall(r'[""](.*?)[""]', content)
        quotes.extend(quoted)
        
        # Look for dash-separated powerful statements
        dash_sections = re.findall(r'—\s*\n(.+?)(?=\n—|\n\n|$)', content, re.DOTALL)
        for section in dash_sections:
            lines = section.strip().split('\n')
            for line in lines:
                if len(line) > 30 and len(line) < 200:
                    quotes.append(line.strip())
        
        # Look for powerful statements with indicators
        indicators = [
            r'but here\'s what I want you to hear:?\s*(.+?)(?=\n|$)',
            r'here\'s what I\'ve learned:?\s*(.+?)(?=\n|$)',
            r'my mind tells me:?\s*(.+?)(?=\n|$)',
            r'success demands:?\s*(.+?)(?=\n|$)',
            r'you cannot\s*(.+?)(?=\n|$)',
            r'loneliness is the price\s*(.+?)(?=\n|$)'
        ]
        
        for indicator in indicators:
            matches = re.findall(indicator, content, re.IGNORECASE)
            for match in matches:
                if len(match) > 30:
                    quotes.append(match.strip())
        
        return list(set(quotes))  # Remove duplicates
    
    def send_to_jai(self, posts, mode="learn"):
        """Send posts to JAI for learning"""
        
        results = []
        
        for i, post in enumerate(posts):
            print(f"\n📝 Processing post {i+1}/{len(posts)}: {post['title']}")
            
            # Extract quotes
            quotes = self.extract_quotes_from_content(post['content'])
            
            # Format for JAI
            message = f"""add post: {post['title']}

{post['content']}"""

            # Send to JAI
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
                    results.append({
                        'title': post['title'],
                        'status': 'success',
                        'quotes_found': len(quotes)
                    })
                    print(f"✅ Learned: {post['title']} ({len(quotes)} quotes extracted)")
                else:
                    results.append({
                        'title': post['title'],
                        'status': 'failed',
                        'error': response.text
                    })
                    print(f"❌ Failed: {post['title']}")
            
            except Exception as e:
                results.append({
                    'title': post['title'],
                    'status': 'error',
                    'error': str(e)
                })
                print(f"❌ Error: {post['title']} - {e}")
        
        return results
    
    def import_from_file(self, filepath):
        """Import from a WhatsApp export file"""
        
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            export_text = f.read()
        
        # Parse posts
        posts = self.parse_whatsapp_export(export_text)
        
        print(f"📊 Found {len(posts)} posts in export file")
        
        # Send to JAI
        results = self.send_to_jai(posts)
        
        # Summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        total_quotes = sum(r.get('quotes_found', 0) for r in results)
        
        print("\n" + "="*50)
        print(f"📊 IMPORT SUMMARY")
        print("="*50)
        print(f"✅ Successfully imported: {success_count}/{len(posts)} posts")
        print(f"💬 Total quotes extracted: {total_quotes}")
        print("\n🎉 Master's Mindset wisdom now lives in JAI!")
        
        return results

# Usage
if __name__ == "__main__":
    importer = MasterMindsetImporter(
        jai_api_url="https://your-jai-app.onrender.com",
        client_id="master_mindset_importer"
    )
    
    # Import your exported WhatsApp file
    results = importer.import_from_file("whatsapp_export.txt")
    
    # Save results for reference
    with open("import_results.json", "w") as f:
        json.dump(results, f, indent=2)