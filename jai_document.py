"""JAI - Document Intelligence Module
Handles document upload, text extraction, simplification, and intelligent Q&A.
Stores documents per user - no ID needed!
"""

import base64
import tempfile
import os
import re
import logging
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
        
        simplified += f"💡 **Now ask me anything about this document!**"
        
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
    def _get_code_explanation(term, content):
        """Provide intelligent explanations for code-related terms"""
        explanations = {
            'fs': "📁 **fs (File System module)** - This is a Node.js built-in module that allows you to work with the file system on your computer. It can read, write, delete, and modify files. Common uses: reading files with `fs.readFile()`, writing files with `fs.writeFile()`, and checking if files exist.",
            
            'http': "🌐 **http module** - This creates web servers in Node.js. It handles incoming HTTP requests (like when someone visits a website) and sends back responses. The code uses it to create a server that listens for requests.",
            
            'path': "📂 **path module** - Helps work with file and directory paths. It handles things like joining paths (`path.join()`), getting file extensions, and normalizing paths across different operating systems.",
            
            'cors': "🔓 **CORS (Cross-Origin Resource Sharing)** - This is a security feature that controls which websites can access your server. The code sets `'Access-Control-Allow-Origin': '*'` which allows ANY website to access it - this is a security vulnerability being shown for educational purposes.",
            
            'createServer': "🖥️ **createServer()** - This method creates a web server. It takes a callback function that runs every time a request comes in. The request (req) contains information about what the user asked for, and response (res) is what you send back.",
            
            'setHeader': "📋 **setHeader()** - Sets HTTP response headers. Headers are metadata sent with responses. Here it's setting CORS headers to control access permissions.",
            
            'vulnerable': "⚠️ **Vulnerable server** - This code is intentionally written with security flaws for educational purposes. It shows what NOT to do in production code, like allowing all CORS requests without restrictions."
        }
        
        term_lower = term.lower()
        for key, explanation in explanations.items():
            if key in term_lower or term_lower in key:
                return explanation
        
        return None
    
    @staticmethod
    def answer_question(client_id, question):
        """Intelligently answer ANY question about the document with explanations"""
        doc = DocumentHandler.get_user_document(client_id)
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SUMMARY QUESTIONS ==========
        if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'what is this about', 'tell me about it', 'what does it say', 'gist']):
            lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 15]
            summary = f"📋 **Summary of '{filename}':**\n\n"
            
            if lines:
                for i, line in enumerate(lines[:8], 1):
                    summary += f"{i}. {line[:200]}{'...' if len(line) > 200 else ''}\n\n"
            else:
                summary += f"{content[:600]}...\n\n"
            
            # Add document purpose explanation
            if 'vulnerable' in content.lower():
                summary += "\n⚠️ **Document Purpose:** This appears to be an educational example showing a vulnerable server. It's meant for learning about security issues like CORS misconfiguration.\n\n"
            elif 'http' in content.lower() and 'server' in content.lower():
                summary += "\n💡 **What this is:** A Node.js HTTP server example. It demonstrates how to create a basic web server.\n\n"
            
            summary += f"💡 Ask me specific questions like 'What does fs do?' or 'Explain the CORS settings'"
            return summary
        
        # ========== EXPLANATION QUESTIONS (What does X do/mean) ==========
        explain_match = re.search(r'what does (?:the |this |that )?([a-zA-Z0-9_]+) (?:do|mean)', question_lower)
        if not explain_match:
            explain_match = re.search(r'explain (?:the |this |that )?([a-zA-Z0-9_]+)', question_lower)
        
        if explain_match:
            term = explain_match.group(1).strip()
            
            # First check if we have a pre-defined explanation
            explanation = DocumentHandler._get_code_explanation(term, content)
            if explanation:
                # Also show where it appears in the document
                lines = content.split('\n')
                context_line = None
                for line in lines:
                    if term in line.lower() and len(line.strip()) > 10:
                        context_line = line.strip()
                        break
                
                result = f"{explanation}\n\n"
                if context_line:
                    result += f"**Where it appears in your document:**\n```\n{context_line}\n```\n"
                result += "\n💡 Need more details? Ask me about another term!"
                return result
            
            # If no pre-defined explanation, search document
            lines = content.split('\n')
            for line in lines:
                if term in line.lower():
                    return f"📖 **About '{term}':**\n\n```\n{line.strip()}\n```\n\n**Explanation:** This appears in your document as shown above. Would you like me to explain a specific part in more detail?"
        
        # ========== WHAT DOES IT DO? (Contextual) ==========
        if question_lower == 'what does it do' or question_lower == 'what is it':
            # Analyze document purpose
            if 'vulnerable' in content.lower():
                return "📖 **This document shows a vulnerable Node.js server** designed for educational hacking.\n\n**What it does:**\n• Creates an HTTP server using Node.js\n• Has intentional security vulnerabilities (like permissive CORS)\n• Is meant to teach about security flaws\n\n**Key components:**\n• Uses `http`, `fs`, and `path` modules\n• Stores data in memory arrays\n• Has CORS set to allow all origins (`*`)\n\n⚠️ This code is intentionally insecure for learning purposes."
            
            elif 'http' in content.lower() and 'server' in content.lower():
                return "📖 **This is a Node.js HTTP server example.**\n\n**What it does:**\n• Creates a web server that listens for requests\n• Handles incoming HTTP requests\n• Sends back responses\n\n**Common uses:**\n• Building web applications\n• Creating APIs\n• Serving static files"
            
            else:
                return "📖 **This document contains code/text content.**\n\nAsk me:\n• 'What type of code is this?'\n• 'Summarize the document'\n• 'What does [specific term] do?'"
        
        # ========== CODE TYPE QUESTIONS ==========
        if any(word in question_lower for word in ['what type', 'what language', 'what code', 'programming language']):
            if 'const' in content or 'let' in content or 'var' in content:
                if 'http' in content or 'server' in content:
                    return "💻 **This is Node.js/JavaScript code!**\n\n" \
                           "**What this code does:**\n" \
                           "• Creates an HTTP web server\n" \
                           "• Uses Node.js built-in modules (http, fs, path)\n" \
                           "• Handles incoming requests and sends responses\n\n" \
                           "**Key features:**\n" \
                           "• `http.createServer()` - Creates the server\n" \
                           "• `req` and `res` - Request and response objects\n" \
                           "• CORS headers for cross-origin requests\n\n" \
                           "Want me to explain any specific part?"
            elif 'def ' in content or 'import ' in content:
                return "🐍 **This is Python code!**\n\nWould you like me to explain what it does?"
            else:
                return "📄 **This appears to be a code/text file.**\n\nWhat specific information are you looking for?"
        
        # ========== SPECIFIC TERM SEARCH (with explanation) ==========
        # Extract keywords from question
        keywords = re.findall(r'\b[a-zA-Z]{3,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Search for each keyword
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
                # Check if we have an explanation for this keyword
                explanation = DocumentHandler._get_code_explanation(keyword, content)
                if explanation:
                    response += f"**{keyword}:** {explanation}\n\n"
                else:
                    response += f"**{keyword}:**\n```\n{line}\n```\n\n"
            response += "💡 Need more details? Ask 'What does [term] do?'"
            return response
        
        # ========== FALLBACK ==========
        preview = content[:500] + "..." if len(content) > 500 else content
        return f"📄 **From '{filename}':**\n\n```\n{preview}\n```\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• 'Summarize this document'\n" \
               f"• 'What type of code is this?'\n" \
               f"• 'What does fs do?'\n" \
               f"• 'Explain the CORS settings'\n" \
               f"• 'What is this server for?'"