"""JAI - Document Intelligence Module
Handles document upload, text extraction, simplification, and intelligent Q&A.
Stores documents per user - no ID needed!
"""

import base64
import tempfile
import os
import re
import logging
import requests
from datetime import datetime
import random

logger = logging.getLogger(__name__)

# Try to import document processing libraries
try:
    import PyPDF2
    import docx
    DOCUMENT_SUPPORT = True
    logger.info("Document processing libraries loaded")
except ImportError as e:
    DOCUMENT_SUPPORT = False
    logger.warning(f"Document processing libraries not installed: {e}")

# Store documents per user (client_id)
_user_documents = {}


class DocumentHandler:
    """Handle document upload and processing per user"""
    
    @staticmethod
    def extract_text_from_base64(base64_content, filename):
        """Extract text from base64 encoded file"""
        try:
            file_content = base64.b64decode(base64_content)
            file_ext = filename.split('.')[-1].lower()
            
            logger.info(f"Processing file: {filename}, size: {len(file_content)} bytes")
            
            if file_ext == 'txt':
                text = file_content.decode('utf-8')
                return text
            
            elif file_ext == 'pdf' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                text = ""
                with open(tmp_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                os.unlink(tmp_path)
                return text if text.strip() else None
            
            elif file_ext == 'docx' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                doc = docx.Document(tmp_path)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                os.unlink(tmp_path)
                return text if text.strip() else None
            
            return None
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return None
    
    @staticmethod
    def simplify_document(text, filename):
        """Generate simplified version of document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Detect document type
        text_lower = text.lower()
        if 'contract' in text_lower or 'agreement' in text_lower:
            icon, doc_type = "⚖️", "Legal Document"
        elif 'http' in text_lower or 'server' in text_lower or 'const' in text_lower:
            icon, doc_type = "💻", "Code File"
        else:
            icon, doc_type = "📄", "Document"
        
        # Get first few lines
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10][:6]
        
        simplified = f"{icon} **{doc_type}**\n\n"
        simplified += f"📄 {filename}\n"
        simplified += f"📊 {len(text)} characters\n\n"
        
        if lines:
            simplified += f"**Main content:**\n\n"
            for i, line in enumerate(lines, 1):
                simplified += f"{i}. {line[:150]}{'...' if len(line) > 150 else ''}\n\n"
        
        simplified += f"💡 **Now ask me anything!** I'll answer from your document or search online."
        
        return simplified
    
    @staticmethod
    def store_document(client_id, filename, text, simplified):
        """Store document for a user"""
        _user_documents[client_id] = {
            'filename': filename,
            'content': text,
            'simplified': simplified,
            'created_at': datetime.now(),
            'size': len(text)
        }
        return True
    
    @staticmethod
    def get_user_document(client_id):
        """Get user's document"""
        return _user_documents.get(client_id)
    
    @staticmethod
    def has_document(client_id):
        """Check if user has document"""
        return client_id in _user_documents
    
    @staticmethod
    def search_online(query):
        """Search online for general knowledge questions"""
        try:
            # Try Wikipedia
            encoded_query = query.replace(' ', '_')
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}'
            response = requests.get(url, timeout=8, headers={'User-Agent': 'JAI-Bot/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    extract = ' '.join(extract.split())
                    if len(extract) > 50:
                        return extract
            
            # Try DuckDuckGo
            ddg_url = f'https://api.duckduckgo.com/?q={query}&format=json&no_html=1'
            ddg_response = requests.get(ddg_url, timeout=8)
            
            if ddg_response.status_code == 200:
                data = ddg_response.json()
                if data.get('AbstractText'):
                    return data['AbstractText']
                elif data.get('Definition'):
                    return data['Definition']
            
            return None
        except Exception as e:
            logger.error(f"Online search error: {e}")
            return None
    
    @staticmethod
    def is_conversational_or_emotional(question):
        """Check if question is conversational or emotional (not technical)"""
        question_lower = question.lower()
        
        conversational_patterns = [
            r'i don\'?t understand',
            r'i don\'?t get it',
            r'confused',
            r'what do you mean',
            r'can you explain',
            r'tell me more',
            r'think of the future',
            r'working for someone',
            r'working for others',
            r'my future',
            r'my life',
            r'i feel',
            r'i think',
            r'what should i do',
            r'help me understand',
            r'this is hard',
            r'i am stuck',
            r'what is the point',
            r'why am i learning this',
            r'is this useful'
        ]
        
        for pattern in conversational_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    @staticmethod
    def _handle_conversational_response(question, doc):
        """Handle conversational/emotional questions in context of the document"""
        question_lower = question.lower()
        filename = doc['filename']
        content = doc['content']
        
        # "I don't understand" responses
        if 'don\'t understand' in question_lower or 'dont understand' in question_lower or 'don\'t get it' in question_lower or 'confused' in question_lower:
            responses = [
                f"I understand this can be confusing. Let me break down what's in '{filename}':\n\n"
                f"📖 **This is a code file** showing a vulnerable HTTP server example.\n\n"
                f"**What it contains:**\n"
                f"• Node.js server code using http module\n"
                f"• File system operations with fs module\n"
                f"• Path handling with path module\n"
                f"• Intentional security vulnerabilities for learning\n\n"
                f"💡 **Try asking:** 'What does the http module do?' or 'Explain the vulnerabilities'",
                
                f"No worries! '{filename}' is educational code showing how NOT to build a server.\n\n"
                f"**The main points:**\n"
                f"1. It creates an HTTP server\n"
                f"2. It has intentional security flaws (CORS `*`, no validation)\n"
                f"3. It's meant for learning about vulnerabilities\n\n"
                f"Want me to explain a specific part?"
            ]
            return random.choice(responses)
        
        # Future/career related responses
        if 'future' in question_lower or 'working for' in question_lower or 'work for someone' in question_lower:
            return f"💭 **About your future and work:**\n\n" \
                   f"The document '{filename}' is about code and servers, but your question touches on something deeper.\n\n" \
                   f"**The code in this document shows:**\n" \
                   f"• How to build things (servers)\n" \
                   f"• How to identify vulnerabilities\n" \
                   f"• How to think like a developer\n\n" \
                   f"**Apply this to your future:**\n" \
                   f"• Learning to build gives you options\n" \
                   f"• Understanding systems helps you create, not just work for others\n" \
                   f"• Every expert started confused - keep going!\n\n" \
                   f"Want to understand how this server code works? Or ask me something else?"
        
        # General confusion/help responses
        if 'stuck' in question_lower or 'help me' in question_lower:
            return f"🤔 **You're not alone!** This code can be confusing at first.\n\n" \
                   f"**What '{filename}' is teaching:**\n" \
                   f"• How HTTP servers work\n" \
                   f"• Common security mistakes (vulnerabilities)\n" \
                   f"• Node.js basics (fs, path, http modules)\n\n" \
                   f"**Let me help:** Ask me 'What does http.createServer do?' or 'Explain the vulnerabilities'\n\n" \
                   f"The more you ask, the clearer it becomes!"
        
        # "What should I do" responses
        if 'what should i do' in question_lower or 'what is the point' in question_lower:
            return f"💡 **Based on the document '{filename}':**\n\n" \
                   f"1. **Understand the code** - Ask me to explain each part\n" \
                   f"2. **Identify vulnerabilities** - Look for CORS `*`, no input validation\n" \
                   f"3. **Learn to fix them** - That's the educational goal\n\n" \
                   f"**Next steps:** Try asking 'What's wrong with this code?' or 'How do I fix the vulnerabilities?'"
        
        # "Is this useful" responses
        if 'useful' in question_lower or 'why am i learning' in question_lower:
            return f"🎯 **Why this matters:**\n\n" \
                   f"The code in '{filename}' teaches you:\n" \
                   f"• **Web server fundamentals** - How the internet works\n" \
                   f"• **Security awareness** - What NOT to do in production\n" \
                   f"• **Node.js skills** - fs, path, http modules\n\n" \
                   f"These skills help you build real apps, understand vulnerabilities, and become a better developer!\n\n" \
                   f"Keep asking questions - you're on the right track!"
        
        return None
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer question - routes to document or online search"""
        doc = DocumentHandler.get_user_document(client_id)
        
        # If no document is loaded, search online
        if not doc:
            search_result = DocumentHandler.search_online(question)
            if search_result:
                return f"🔍 **I searched online:**\n\n{search_result}"
            return "📄 No document loaded. Upload a document or ask me a general question!"
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== HANDLE CONVERSATIONAL/EMOTIONAL QUESTIONS FIRST ==========
        if DocumentHandler.is_conversational_or_emotional(question):
            conversational_response = DocumentHandler._handle_conversational_response(question, doc)
            if conversational_response:
                return conversational_response
        
        # ========== EXPLICIT SUMMARY COMMAND ==========
        if any(word in question_lower for word in ['summarize', 'summary', 'gist', 'overview', 'what is this about', 'tell me about it']):
            lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 10][:10]
            summary = f"📋 **Summary of '{filename}':**\n\n"
            
            if lines:
                for i, line in enumerate(lines[:8], 1):
                    display_line = line[:200] + '...' if len(line) > 200 else line
                    summary += f"{i}. {display_line}\n\n"
            else:
                summary += f"{content[:600]}...\n\n"
            
            summary += f"📊 **Document stats:** {len(content)} characters, {len(content.split())} words\n\n"
            
            if 'const' in content or 'let' in content or 'function' in content:
                summary += f"💡 **This appears to be code.** Try asking: 'What does fs do?' or 'Explain the http module'"
            else:
                summary += f"💡 **Ask me questions about this document!**"
            
            return summary
        
        # ========== ANSWER FROM DOCUMENT ==========
        
        # Explanation questions for code terms
        explain_match = re.search(r'what does (?:the |this |that )?([a-zA-Z0-9_]+) (?:do|mean)', question_lower)
        if not explain_match:
            explain_match = re.search(r'explain (?:the |this |that )?([a-zA-Z0-9_]+)', question_lower)
        
        if explain_match:
            term = explain_match.group(1).strip()
            
            # Check if term appears in document
            if term in content.lower():
                return DocumentHandler._get_code_explanation(term, content) or \
                       f"📖 **'{term}'** appears in your document. Would you like me to search online for more information?"
        
        # Default: Show relevant excerpt from document
        # Find sentences containing question keywords
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not', 'explain', 'mean', 'meaning', 'how', 'why', 'when', 'where', 'who'}
        keywords = [k for k in keywords if k not in stopwords]
        
        relevant_lines = []
        for line in content.split('\n'):
            if any(keyword in line.lower() for keyword in keywords[:3]):
                if len(line.strip()) > 20:
                    relevant_lines.append(line.strip())
        
        if relevant_lines:
            excerpt = "\n".join(relevant_lines[:3])
            return f"📄 **From '{filename}':**\n\n```\n{excerpt[:500]}\n```\n\n💡 Want me to explain any of this further?"
        
        # Final fallback
        preview = content[:500] + "..." if len(content) > 500 else content
        return f"📄 **From your document '{filename}':**\n\n```\n{preview}\n```\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• 'Summarize this document'\n" \
               f"• 'What type of code is this?'\n" \
               f"• 'What does fs do?'"
    
    @staticmethod
    def _get_code_explanation(term, content):
        """Provide intelligent explanations for code-related terms"""
        
        explanations = {
            'fs': "📁 **fs (File System module)** - Node.js built-in module for file operations.\n\n**What it can do:**\n• Read files: `fs.readFile()`\n• Write files: `fs.writeFile()`\n• Delete files: `fs.unlink()`\n• Create directories: `fs.mkdir()`\n\n**Common use:** Reading configuration, saving data, logging.",
            
            'http': "🌐 **http module** - Node.js module for creating web servers.\n\n**What it does:**\n• Creates HTTP servers with `http.createServer()`\n• Handles incoming requests (GET, POST, etc.)\n• Sends responses back to clients\n\n**Common use:** Building web applications, APIs.",
            
            'path': "📂 **path module** - Node.js module for working with file paths.\n\n**What it does:**\n• Joins paths: `path.join()`\n• Gets file extensions: `path.extname()`\n• Normalizes paths across OS\n\n**Common use:** Building cross-platform file paths.",
            
            'cors': "🔓 **CORS (Cross-Origin Resource Sharing)** - Security feature for web browsers.\n\n**What it controls:**\n• Which websites can access your API\n• What HTTP methods are allowed\n\n**⚠️ Security note:** `'*'` allows ANY website - a vulnerability!",
            
            'createServer': "🖥️ **createServer()** - Creates an HTTP server in Node.js.\n\n**How it works:**\n1. Takes a callback function\n2. Callback runs for every request\n3. Gets `req` (request) and `res` (response) objects\n4. Send back data with `res.end()`",
            
            'setHeader': "📋 **setHeader()** - Sets HTTP response headers.\n\n**What headers do:**\n• Control caching\n• Set content type\n• Enable CORS\n• Handle authentication",
            
            'vulnerable': "⚠️ **Vulnerable server** - Code with intentional security flaws.\n\n**Common vulnerabilities:**\n• Permissive CORS (`*` allows all origins)\n• No input validation\n• No authentication\n\n**Purpose:** Educational - learn what NOT to do!"
        }
        
        term_lower = term.lower()
        
        for key, explanation in explanations.items():
            if key == term_lower or (key in term_lower and len(key) > 2):
                return explanation
        
        return None