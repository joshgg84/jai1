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
        
        simplified += f"💡 **Now ask me anything about this document!** I can also search online for terms you don't understand."
        
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
    def search_online(term):
        """Search online for a term using Wikipedia API"""
        try:
            # Try Wikipedia
            encoded_term = term.replace(' ', '_')
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_term}'
            response = requests.get(url, timeout=8, headers={'User-Agent': 'JAI-Bot/1.0'})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('extract'):
                    extract = data['extract']
                    # Clean up
                    extract = re.sub(r'\([^)]*\)', '', extract)
                    extract = ' '.join(extract.split())
                    if len(extract) > 50:
                        return extract
            
            # Try DuckDuckGo
            ddg_url = f'https://api.duckduckgo.com/?q={term}&format=json&no_html=1'
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
    def _get_code_explanation(term, content):
        """Provide intelligent explanations for code-related terms with online fallback"""
        
        # Built-in explanations for common Node.js terms
        explanations = {
            'fs': "📁 **fs (File System module)** - Node.js built-in module for file operations.\n\n**What it can do:**\n• Read files: `fs.readFile()`\n• Write files: `fs.writeFile()`\n• Delete files: `fs.unlink()`\n• Create directories: `fs.mkdir()`\n• Check if files exist\n\n**Common use:** Reading configuration files, saving user data, logging.",
            
            'http': "🌐 **http module** - Node.js module for creating web servers.\n\n**What it does:**\n• Creates HTTP servers with `http.createServer()`\n• Handles incoming requests (GET, POST, etc.)\n• Sends responses back to clients\n\n**Common use:** Building web applications, APIs, and web services.",
            
            'path': "📂 **path module** - Node.js module for working with file paths.\n\n**What it does:**\n• Joins paths: `path.join()`\n• Gets file extensions: `path.extname()`\n• Normalizes paths across OS\n• Resolves relative paths\n\n**Common use:** Building cross-platform file paths.",
            
            'cors': "🔓 **CORS (Cross-Origin Resource Sharing)** - Security feature for web browsers.\n\n**What it controls:**\n• Which websites can access your API\n• What HTTP methods are allowed\n• What headers can be sent\n\n**⚠️ Security note:** Setting `'Access-Control-Allow-Origin': '*'` allows ANY website to access your server - a security vulnerability!",
            
            'createServer': "🖥️ **createServer()** - Method that creates an HTTP server in Node.js.\n\n**How it works:**\n1. Takes a callback function\n2. Callback runs for every request\n3. Gets `req` (request) and `res` (response) objects\n4. You send back data with `res.end()`\n\n**Example:** `http.createServer((req, res) => { res.end('Hello'); })`",
            
            'setHeader': "📋 **setHeader()** - Sets HTTP response headers.\n\n**What headers do:**\n• Control caching behavior\n• Set content type\n• Enable CORS\n• Handle authentication\n\n**Example:** `res.setHeader('Content-Type', 'application/json')`",
            
            'vulnerable': "⚠️ **Vulnerable server** - Code with intentional security flaws.\n\n**Common vulnerabilities shown:**\n• Permissive CORS (`*` allows all origins)\n• No input validation\n• No authentication\n• SQL injection points\n\n**Purpose:** Educational - learn what NOT to do!",
            
            'require': "📦 **require()** - Node.js function to import modules.\n\n**What it does:**\n• Loads built-in modules: `require('fs')`\n• Loads local files: `require('./file.js')`\n• Loads npm packages: `require('express')`\n\n**Returns:** The exported content of the module."
        }
        
        term_lower = term.lower()
        
        # Check built-in explanations first
        for key, explanation in explanations.items():
            if key == term_lower or (key in term_lower and len(key) > 2):
                return explanation, True  # Found in built-in
        
        # If not found, search online
        online_result = DocumentHandler.search_online(term)
        if online_result:
            return f"🔍 **{term}** (from online search):\n\n{online_result}\n\n💡 This information comes from Wikipedia. For document-specific info, check where it appears in your file.", False
        
        return None, False
    
    @staticmethod
    def answer_question(client_id, question):
        """Intelligently answer ANY question about the document with online fallback"""
        doc = DocumentHandler.get_user_document(client_id)
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SUMMARY QUESTIONS ==========
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
            elif 'http' in content.lower():
                summary += "\n💡 **Purpose:** Node.js HTTP server example.\n\n"
            
            summary += f"💡 Ask me: 'What does fs do?' or 'Explain the code'"
            return summary
        
        # ========== EXPLANATION QUESTIONS (What does X do/mean) ==========
        explain_match = re.search(r'what does (?:the |this |that )?([a-zA-Z0-9_]+) (?:do|mean)', question_lower)
        if not explain_match:
            explain_match = re.search(r'explain (?:the |this |that )?([a-zA-Z0-9_]+)', question_lower)
        if not explain_match:
            explain_match = re.search(r'what is (?:the |a |an )?([a-zA-Z0-9_]+)', question_lower)
        
        if explain_match:
            term = explain_match.group(1).strip()
            
            # First check if term exists in document
            term_in_doc = term in content.lower()
            
            # Get explanation (built-in or online)
            explanation, is_builtin = DocumentHandler._get_code_explanation(term, content)
            
            # Find where it appears in document
            lines = content.split('\n')
            context_line = None
            for line in lines:
                if term in line.lower() and len(line.strip()) > 10:
                    context_line = line.strip()
                    break
            
            result = ""
            
            if explanation:
                result = f"{explanation}\n\n"
            else:
                result = f"📖 **About '{term}':**\n\n"
            
            if context_line and term_in_doc:
                result += f"**Where it appears in your document:**\n```\n{context_line}\n```\n\n"
            elif not is_builtin and not context_line:
                result += f"💡 I couldn't find '{term}' in your document, but here's what I found online.\n\n"
            
            result += "\n💡 Need more details? Ask about another term!"
            return result
        
        # ========== WHAT DOES IT DO? (Contextual) ==========
        if question_lower in ['what does it do', 'what is this', 'what is it']:
            if 'vulnerable' in content.lower():
                return "📖 **This is a vulnerable Node.js server** for educational hacking.\n\n" \
                       "**What it does:**\n" \
                       "• Creates an HTTP server with `http.createServer()`\n" \
                       "• Has intentional security vulnerabilities\n" \
                       "• Uses CORS with `'*'` (allows all origins - insecure!)\n" \
                       "• Stores data in memory arrays\n\n" \
                       "⚠️ **Purpose:** Teaching about web security vulnerabilities.\n\n" \
                       "Ask me: 'What does fs do?' or 'Explain CORS'"
            
            elif 'http' in content.lower():
                return "📖 **This is a Node.js HTTP server example.**\n\n" \
                       "**What it does:**\n" \
                       "• Creates a web server that listens for requests\n" \
                       "• Handles HTTP requests and sends responses\n" \
                       "• Uses Node.js built-in modules\n\n" \
                       "Ask me to explain specific parts like 'What does createServer do?'"
            
            return "📖 **This document contains code/text content.**\n\nAsk me specific questions like:\n• 'What type of code is this?'\n• 'What does fs do?'\n• 'Summarize the document'"
        
        # ========== CODE TYPE QUESTIONS ==========
        if any(word in question_lower for word in ['what type', 'what language', 'what code', 'programming language']):
            if 'const' in content or 'let' in content or 'var' in content:
                return "💻 **This is Node.js/JavaScript code!**\n\n" \
                       "**What this code does:**\n" \
                       "• Creates an HTTP web server\n" \
                       "• Uses Node.js built-in modules (http, fs, path)\n" \
                       "• Handles incoming requests\n\n" \
                       "**Want to understand specific parts?** Ask:\n" \
                       "• 'What does fs do?'\n" \
                       "• 'Explain http.createServer'\n" \
                       "• 'What is CORS?'"
        
        # ========== SPECIFIC TERM SEARCH ==========
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not', 'explain', 'mean', 'meaning'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Search for keywords in document
        lines = content.split('\n')
        found_lines = []
        for keyword in keywords[:3]:
            for line in lines:
                if keyword in line.lower() and len(line.strip()) > 15:
                    found_lines.append((keyword, line.strip()))
                    break
        
        if found_lines:
            response = f"📖 **Found in your document:**\n\n"
            for keyword, line in found_lines:
                explanation, _ = DocumentHandler._get_code_explanation(keyword, content)
                if explanation:
                    response += f"**{keyword}:** {explanation}\n\n"
                else:
                    response += f"**{keyword}:**\n```\n{line}\n```\n\n"
            response += "💡 Ask 'What does [term] do?' for more details!"
            return response
        
        # ========== FALLBACK WITH ONLINE SEARCH ==========
        preview = content[:400] + "..." if len(content) > 400 else content
        return f"📄 **From '{filename}':**\n\n```\n{preview}\n```\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• 'Summarize this document'\n" \
               f"• 'What type of code is this?'\n" \
               f"• 'What does fs do?' (I can search online!)\n" \
               f"• 'Explain http.createServer'"