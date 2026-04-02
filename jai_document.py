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
    def is_general_knowledge_question(question):
        """Determine if question is general knowledge (not about the document)"""
        question_lower = question.lower()
        
        # General knowledge indicators - these are unlikely to be in a code file
        general_patterns = [
            r'who created', r'who founded', r'who invented', r'who is',
            r'what is the capital', r'what year', r'when was',
            r'history of', r'background of', r'born', r'died',
            r'president of', r'prime minister', r'ceo of',
            r'population of', r'area of', r'located in',
            r'toyota', r'honda', r'nissan', r'ferrari', r'tesla', r'bmw', r'mercedes',
            r'microsoft', r'apple', r'google', r'amazon', r'facebook',
            r'world war', r'american', r'european', r'african', r'asian'
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    @staticmethod
    def is_document_specific_question(question, content):
        """Check if question is likely about the document content"""
        question_lower = question.lower()
        content_lower = content.lower()
        
        # Extract keywords from question
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not', 'explain', 'mean', 'meaning', 'how', 'why', 'when', 'where', 'who'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Check if keywords appear in document
        matches = 0
        for keyword in keywords[:5]:
            if keyword in content_lower:
                matches += 1
        
        # If at least one keyword matches, it's likely document-specific
        return matches >= 1
    
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
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer question - routes to document or online search"""
        doc = DocumentHandler.get_user_document(client_id)
        
        # Check if this is general knowledge (not document-related)
        if DocumentHandler.is_general_knowledge_question(question):
            # Search online for answer
            search_result = DocumentHandler.search_online(question)
            if search_result:
                return f"🔍 **I searched online:**\n\n{search_result}"
            else:
                return f"🔍 I couldn't find information about that. Try rephrasing your question."
        
        # If no document is loaded, search online
        if not doc:
            search_result = DocumentHandler.search_online(question)
            if search_result:
                return f"🔍 **I searched online:**\n\n{search_result}"
            return "📄 No document loaded. Upload a document or ask me a general question!"
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # Check if question is document-specific
        if not DocumentHandler.is_document_specific_question(question, content):
            # Not about document - search online
            search_result = DocumentHandler.search_online(question)
            if search_result:
                return f"🔍 **That's not in your document, so I searched online:**\n\n{search_result}\n\n💡 Your document is about code. Ask me about `fs`, `http`, or 'what does this code do'?"
            else:
                return f"🔍 I couldn't find information about that. Your document contains code. Try asking about `fs`, `http`, or 'summarize this document'."
        
        # ========== ANSWER FROM DOCUMENT ==========
        
        # Summary questions
        if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'what is this about', 'tell me about it', 'gist']):
            lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 15]
            summary = f"📋 **Summary of '{filename}':**\n\n"
            
            if lines:
                for i, line in enumerate(lines[:8], 1):
                    summary += f"{i}. {line[:200]}{'...' if len(line) > 200 else ''}\n\n"
            else:
                summary += f"{content[:600]}...\n\n"
            
            if 'vulnerable' in content.lower():
                summary += "\n⚠️ **Purpose:** Educational example showing server vulnerabilities.\n\n"
            
            summary += f"💡 Ask me: 'What does fs do?' or 'Explain the code'"
            return summary
        
        # Explanation questions
        explain_match = re.search(r'what does (?:the |this |that )?([a-zA-Z0-9_]+) (?:do|mean)', question_lower)
        if not explain_match:
            explain_match = re.search(r'explain (?:the |this |that )?([a-zA-Z0-9_]+)', question_lower)
        if not explain_match:
            explain_match = re.search(r'what is (?:the |a |an )?([a-zA-Z0-9_]+)', question_lower)
        
        if explain_match:
            term = explain_match.group(1).strip()
            
            explanation = DocumentHandler._get_code_explanation(term, content)
            
            # Find where it appears in document
            lines = content.split('\n')
            context_line = None
            for line in lines:
                if term in line.lower() and len(line.strip()) > 10:
                    context_line = line.strip()
                    break
            
            if explanation:
                result = f"{explanation}\n\n"
                if context_line:
                    result += f"**Where it appears in your document:**\n```\n{context_line}\n```\n"
                return result
            elif context_line:
                return f"📖 **About '{term}':**\n\n```\n{context_line}\n```\n\nThis appears in your document. Want me to search online for more info?"
        
        # Code type questions
        if any(word in question_lower for word in ['what type', 'what language', 'what code', 'programming language']):
            if 'const' in content or 'let' in content:
                return "💻 **This is Node.js/JavaScript code!**\n\n**What it does:**\n• Creates an HTTP web server\n• Uses Node.js built-in modules (http, fs, path)\n• Handles incoming requests\n\n**Ask me:** 'What does fs do?' or 'Explain http.createServer'"
        
        # Default document response
        preview = content[:400] + "..." if len(content) > 400 else content
        return f"📄 **From your document '{filename}':**\n\n```\n{preview}\n```\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• 'Summarize this document'\n" \
               f"• 'What type of code is this?'\n" \
               f"• 'What does fs do?'"