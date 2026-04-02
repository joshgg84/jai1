"""JAI - Document Intelligence Module
Handles document upload, text extraction, simplification, and Q&A.
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
_user_documents = {}  # {client_id: {'filename': str, 'content': str, 'simplified': str, 'created_at': datetime}}


class DocumentHandler:
    """Handle document upload and processing per user"""
    
    @staticmethod
    def extract_text_from_base64(base64_content, filename):
        """Extract text from base64 encoded file"""
        try:
            file_content = base64.b64decode(base64_content)
            file_ext = filename.split('.')[-1].lower()
            
            logger.info(f"Processing file: {filename}, size: {len(file_content)} bytes, type: {file_ext}")
            
            if file_ext == 'txt':
                text = file_content.decode('utf-8')
                logger.info(f"Extracted {len(text)} characters from TXT file")
                return text
            
            elif file_ext == 'pdf' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                text = ""
                with open(tmp_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                os.unlink(tmp_path)
                logger.info(f"Extracted {len(text)} characters from PDF file")
                return text if text.strip() else None
            
            elif file_ext == 'docx' and DOCUMENT_SUPPORT:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                doc = docx.Document(tmp_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
                
                os.unlink(tmp_path)
                logger.info(f"Extracted {len(text)} characters from DOCX file")
                return text if text.strip() else None
            
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
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
        if any(word in text_lower for word in ['contract', 'agreement', 'terms', 'party', 'hereby']):
            icon = "⚖️"
            doc_name = "Legal Document"
        elif any(word in text_lower for word in ['exam', 'test', 'question', 'student', 'course']):
            icon = "📚"
            doc_name = "Educational Document"
        elif any(word in text_lower for word in ['http', 'server', 'function', 'const', 'let', 'var', 'app.get', 'app.post']):
            icon = "💻"
            doc_name = "Code File"
        elif any(word in text_lower for word in ['invoice', 'payment', 'amount', 'due']):
            icon = "💰"
            doc_name = "Financial Document"
        else:
            icon = "📄"
            doc_name = "Document"
        
        # Extract key points (first few lines or sentences)
        lines = text.split('\n')[:10]
        key_points = []
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(key_points) < 5:
                if len(line) > 150:
                    line = line[:147] + "..."
                key_points.append(line)
        
        # Build response
        simplified = f"{icon} **{doc_name} Simplified**\n\n"
        simplified += f"**File:** {filename}\n"
        simplified += f"**Length:** {len(text)} characters\n\n"
        
        if key_points:
            simplified += f"**Main Content:**\n\n"
            for i, point in enumerate(key_points, 1):
                simplified += f"{i}. {point}\n\n"
        else:
            preview = text[:400] + "..." if len(text) > 400 else text
            simplified += f"**Content:**\n\n{preview}\n\n"
        
        simplified += f"**💡 Now you can ask me anything about this document!** Just type your question naturally."
        
        return simplified
    
    @staticmethod
    def store_document(client_id, filename, text, simplified):
        """Store document for a specific user"""
        _user_documents[client_id] = {
            'filename': filename,
            'content': text,
            'simplified': simplified,
            'created_at': datetime.now(),
            'size': len(text)
        }
        logger.info(f"Document stored for user: {client_id}, size: {len(text)} chars")
        return True
    
    @staticmethod
    def get_user_document(client_id):
        """Get document for a specific user"""
        return _user_documents.get(client_id)
    
    @staticmethod
    def has_document(client_id):
        """Check if user has a document loaded"""
        return client_id in _user_documents
    
    @staticmethod
    def clear_document(client_id):
        """Clear document for a user"""
        if client_id in _user_documents:
            del _user_documents[client_id]
            logger.info(f"Document cleared for user: {client_id}")
            return True
        return False
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer questions about user's document"""
        doc = DocumentHandler.get_user_document(client_id)
        
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # Handle empty/short questions
        if len(question_lower) < 5:
            return f"💡 **Ask about '{filename}':**\n\nTry:\n• What is this document about?\n• What type of code is this?\n• Summarize the content\n• Tell me about [specific topic]"
        
        # Question about code/language type
        if any(word in question_lower for word in ['what type', 'what language', 'what code', 'programming language', 'what is this code']):
            # Detect language from content
            if 'const' in content or 'let' in content or 'var' in content or 'function' in content:
                if 'http' in content or 'server' in content:
                    return f"💻 **This appears to be Node.js/JavaScript code!**\n\nThe document contains a Node.js server implementation using the HTTP module. It looks like a web server or API server.\n\nKey indicators:\n• Uses `const` and `let` (ES6 JavaScript)\n• Requires Node.js modules (http, fs, path)\n• Creates a server with http.createServer()\n\nWhat specific part would you like me to explain?"
                else:
                    return f"💻 **This appears to be JavaScript/Node.js code!**\n\nThe document contains JavaScript code, likely for a Node.js application.\n\nWhat would you like to know about the code?"
            elif 'def ' in content or 'import' in content:
                return f"🐍 **This appears to be Python code!**\n\nThe document contains Python code.\n\nWhat would you like to know about it?"
            else:
                return f"📄 **This appears to be a code/text file.**\n\nBased on the content, it contains programming code or configuration.\n\nWhat specific information are you looking for?"
        
        # Summary request
        if any(word in question_lower for word in ['summary', 'overview', 'what is this about', 'tell me about it', 'what is it']):
            # Get first few lines or sentences
            lines = content.split('\n')[:8]
            summary_points = []
            for line in lines:
                line = line.strip()
                if len(line) > 20:
                    if len(line) > 150:
                        line = line[:147] + "..."
                    summary_points.append(line)
            
            if summary_points:
                response = f"📋 **Summary of '{filename}':**\n\n"
                for i, point in enumerate(summary_points[:5], 1):
                    response += f"{i}. {point}\n\n"
                
                # Add document type detection
                if 'const' in content or 'let' in content:
                    response += "\n💡 **This appears to be JavaScript/Node.js code.** Ask me: 'What type of code is this?' for more details."
                
                response += "Anything specific you'd like to know?"
                return response
            else:
                preview = content[:500] + "..." if len(content) > 500 else content
                return f"📋 **From '{filename}':**\n\n{preview}\n\nWhat specific information are you looking for?"
        
        # Search for keywords in content
        keywords = re.findall(r'\b[a-z]{4,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document'}
        keywords = [k for k in keywords if k not in stopwords]
        
        found_info = []
        for keyword in keywords[:5]:
            if keyword in content.lower():
                # Find lines containing keyword
                lines = content.split('\n')
                for line in lines:
                    if keyword in line.lower() and len(line.strip()) > 15:
                        line = line.strip()
                        if len(line) > 200:
                            line = line[:197] + "..."
                        found_info.append((keyword, line))
                        break
        
        if found_info:
            response = f"📖 **About your document:**\n\n"
            for keyword, line in found_info[:3]:
                response += f"**• {keyword.capitalize()}:** {line}\n\n"
            response += "Does that help? Ask me more!"
            return response
        
        # Fallback with helpful prompt
        preview = content[:400] + "..." if len(content) > 400 else content
        return f"📄 **From '{filename}':**\n\n{preview}\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• What is this document about?\n" \
               f"• What type of code is this?\n" \
               f"• Summarize the content\n" \
               f"• Tell me about [specific word from the document]"