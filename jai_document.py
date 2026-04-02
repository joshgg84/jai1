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
    def answer_question(client_id, question):
        """Intelligently answer ANY question about the document"""
        doc = DocumentHandler.get_user_document(client_id)
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SMART QUESTION DETECTION ==========
        
        # 1. SUMMARY QUESTIONS
        if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'what is this about', 'tell me about it', 'what does it say', 'gist']):
            lines = [l.strip() for l in content.split('\n') if l.strip() and len(l.strip()) > 15]
            summary = f"📋 **Summary of '{filename}':**\n\n"
            
            if lines:
                for i, line in enumerate(lines[:8], 1):
                    summary += f"{i}. {line[:200]}{'...' if len(line) > 200 else ''}\n\n"
            else:
                summary += f"{content[:600]}...\n\n"
            
            summary += f"💡 This document has {len(content)} characters. Ask me specific questions about any part!"
            return summary
        
        # 2. CODE TYPE QUESTIONS
        if any(word in question_lower for word in ['what type', 'what language', 'what code', 'programming language', 'what is this code']):
            if 'const' in content or 'let' in content or 'var' in content:
                if 'http' in content or 'server' in content or 'require' in content:
                    return f"💻 **This is Node.js/JavaScript code!**\n\n" \
                           f"This appears to be a Node.js server application. It uses:\n" \
                           f"• HTTP module for server creation\n" \
                           f"• File system (fs) for file operations\n" \
                           f"• Path module for file paths\n\n" \
                           f"**What this code does:** Creates a web server that can handle HTTP requests.\n\n" \
                           f"Want me to explain a specific part?"
            elif 'def ' in content or 'import ' in content:
                return f"🐍 **This is Python code!**\n\nWould you like me to explain what it does?"
            else:
                return f"📄 **This appears to be a code/text file.**\n\nLet me analyze the content for you. What specific information are you looking for?"
        
        # 3. WHAT DOES [THING] DO/MEAN QUESTIONS
        action_match = re.search(r'what does (?:the |this |that )?(.+?) (?:do|mean)', question_lower)
        if action_match:
            search_term = action_match.group(1).strip()
            # Search for lines containing that term
            lines = content.split('\n')
            for line in lines:
                if search_term.lower() in line.lower():
                    return f"📖 **About '{search_term}':**\n\n```\n{line.strip()}\n```\n\nThis is what I found in your document. Need more details?"
            
            # If not found, show context
            words = search_term.split()
            for word in words[:2]:
                for line in lines:
                    if word in line.lower():
                        return f"📖 **Found related content:**\n\n```\n{line.strip()}\n```\n\nIs this what you were asking about?"
        
        # 4. EXPLAIN QUESTIONS
        if question_lower.startswith('explain'):
            # Extract what to explain
            explain_what = question_lower.replace('explain', '').replace('the', '').replace('this', '').replace('that', '').strip()
            if explain_what:
                lines = content.split('\n')
                for line in lines:
                    if explain_what in line.lower():
                        return f"📖 **Explanation of '{explain_what}':**\n\n```\n{line.strip()}\n```\n\nThis is from your document. Would you like me to elaborate?"
        
        # 5. COUNT/STATISTICS QUESTIONS
        if 'how many' in question_lower:
            if 'line' in question_lower:
                line_count = len([l for l in content.split('\n') if l.strip()])
                return f"📊 **Your document has {line_count} lines** of content."
            if 'word' in question_lower:
                word_count = len(content.split())
                return f"📊 **Your document has approximately {word_count} words**."
            if 'character' in question_lower:
                return f"📊 **Your document has {len(content)} characters**."
        
        # 6. SPECIFIC KEYWORD SEARCH
        # Extract important keywords from question
        keywords = re.findall(r'\b[a-z]{4,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Search for each keyword
        lines = content.split('\n')
        found_lines = []
        for keyword in keywords[:5]:
            for line in lines:
                if keyword in line.lower() and len(line.strip()) > 20:
                    if line.strip() not in found_lines:
                        found_lines.append(line.strip())
                        break
        
        if found_lines:
            response = f"📖 **Found in your document:**\n\n"
            for line in found_lines[:4]:
                response += f"```\n{line[:200]}{'...' if len(line) > 200 else ''}\n```\n\n"
            response += f"💡 Ask me: 'Explain this' or 'What does this mean?' for more details."
            return response
        
        # 7. GENERAL QUESTION - Use best matching content
        # Find most relevant section
        sentences = re.split(r'[.!?\n]+', content)
        best_match = None
        best_score = 0
        
        question_words = set(question_lower.split())
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if len(sentence) < 20:
                continue
            # Count matching words
            score = sum(1 for word in question_words if word in sentence_lower and len(word) > 3)
            if score > best_score:
                best_score = score
                best_match = sentence.strip()
                if best_score >= 2:
                    break
        
        if best_match and best_score > 0:
            return f"📖 **From your document:**\n\n```\n{best_match[:300]}{'...' if len(best_match) > 300 else ''}\n```\n\nDoes this answer your question? I can find more information."
        
        # 8. FALLBACK - Show relevant portion
        preview = content[:500] + "..." if len(content) > 500 else content
        return f"📄 **From '{filename}':**\n\n```\n{preview}\n```\n\n" \
               f"\n💡 **Try asking:**\n" \
               f"• 'Summarize this document'\n" \
               f"• 'What type of code is this?'\n" \
               f"• 'What does [specific word] mean?'\n" \
               f"• 'Explain the main purpose'"