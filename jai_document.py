"""JAI - Document Intelligence Module
Handles document upload, text extraction, simplification, and intelligent Q&A.
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
    def generate_long_summary(text, filename):
        """Generate a detailed, intelligent summary of the document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Detect document type
        text_lower = text.lower()
        if 'contract' in text_lower or 'agreement' in text_lower:
            doc_type = "Legal Document"
            icon = "⚖️"
        elif 'http' in text_lower or 'server' in text_lower or 'const' in text_lower or 'function' in text_lower:
            doc_type = "Code/Technical Document"
            icon = "💻"
        elif 'resume' in text_lower or 'cv' in text_lower or 'experience' in text_lower:
            doc_type = "Resume/CV"
            icon = "📄"
        elif 'report' in text_lower or 'analysis' in text_lower:
            doc_type = "Report"
            icon = "📊"
        else:
            doc_type = "Document"
            icon = "📄"
        
        # Get key sentences
        sentences = re.split(r'[.!?\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Build intelligent summary
        summary = f"{icon} **DOCUMENT SUMMARY: '{filename}'**\n\n"
        summary += f"📊 **Stats:** {len(text)} characters, {len(text.split())} words\n"
        summary += f"📁 **Type:** {doc_type}\n\n"
        summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Main content
        summary += "**📖 MAIN CONTENT:**\n\n"
        
        key_points = sentences[:10]
        for i, point in enumerate(key_points, 1):
            if len(point) > 300:
                point = point[:300] + "..."
            summary += f"{i}. {point}\n\n"
        
        summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Helpful tips
        summary += "**💡 You can ask me:**\n"
        summary += "• 'Explain this document in simple terms'\n"
        summary += "• 'What are the key points?'\n"
        summary += "• 'Tell me about a specific section'\n"
        
        return summary
    
    @staticmethod
    def simplify_document(text, filename):
        """Generate simplified version of document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        text_lower = text.lower()
        if 'contract' in text_lower or 'agreement' in text_lower:
            icon, doc_type = "⚖️", "Legal Document"
        elif 'http' in text_lower or 'server' in text_lower or 'const' in text_lower:
            icon, doc_type = "💻", "Code File"
        elif 'resume' in text_lower or 'cv' in text_lower:
            icon, doc_type = "📄", "Resume/CV"
        else:
            icon, doc_type = "📄", "Document"
        
        # Get key lines
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10][:8]
        
        simplified = f"{icon} **{doc_type}:** {filename}\n\n"
        simplified += f"📊 **Size:** {len(text)} characters, {len(text.split())} words\n\n"
        
        if lines:
            simplified += f"**📝 Content:**\n\n"
            for i, line in enumerate(lines, 1):
                clean_line = line[:200] + '...' if len(line) > 200 else line
                simplified += f"{i}. {clean_line}\n\n"
        
        simplified += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        simplified += "💡 **Ask me:** 'Explain this document' or 'What are the key points?'"
        
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
        """Answer questions about the document"""
        doc = DocumentHandler.get_user_document(client_id)
        
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SUMMARY REQUESTS ==========
        summary_patterns = [
            r'summarize',
            r'summary',
            r'overview',
            r'gist',
            r'what is this about',
            r'tell me about it',
            r'explain the document',
            r'simplify',
            r'break it down',
            r'step by step',
            r'give me the main points',
            r'what\'s in this document'
        ]
        
        for pattern in summary_patterns:
            if re.search(pattern, question_lower):
                return DocumentHandler.generate_long_summary(content, filename)
        
        # ========== SIMPLE EXPLANATION (HANDLE "explain" ALONE) ==========
        # If user just says "explain" or "explain this" without more context
        if question_lower == 'explain' or question_lower == 'explain this' or (question_lower.startswith('explain') and len(question_lower) < 15):
            # Get first few key sentences from the document
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:8]
            
            if sentences:
                explanation = f"📖 **EXPLANATION OF '{filename}':**\n\n"
                for i, sent in enumerate(sentences, 1):
                    if len(sent) > 250:
                        sent = sent[:250] + "..."
                    explanation += f"{i}. {sent}\n\n"
                explanation += "\n💡 Ask me for more details about any specific part."
                return explanation
            else:
                return f"📖 I can help explain '{filename}'. What would you like to know? Try asking about a specific section."
        
        # ========== KEY POINTS ==========
        if any(word in question_lower for word in ['key points', 'main points', 'important', 'takeaways']):
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:6]
            
            if sentences:
                response = f"📌 **KEY POINTS FROM '{filename}':**\n\n"
                for i, sent in enumerate(sentences, 1):
                    if len(sent) > 200:
                        sent = sent[:200] + "..."
                    response += f"{i}. {sent}\n\n"
                return response
            else:
                return f"📌 I couldn't extract clear key points from '{filename}'. Try asking me to summarize instead."
        
        # ========== SPECIFIC TOPIC ==========
        # Handle "explain about X" or "tell me about X"
        explain_match = re.search(r'(?:explain|tell me about|what about)\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\?|$)', question_lower)
        if explain_match and len(explain_match.group(1)) > 3:
            topic = explain_match.group(1).strip()
            
            sentences = re.split(r'[.!?\n]+', content)
            relevant = []
            for sentence in sentences:
                if topic.lower() in sentence.lower() and len(sentence) > 20:
                    relevant.append(sentence.strip())
            
            if relevant:
                response = f"📖 **About '{topic.title()}' in '{filename}':**\n\n"
                for sent in relevant[:3]:
                    response += f"• {sent}\n\n"
                return response
            else:
                return f"I couldn't find information about '{topic}' in '{filename}'. Try asking about something else or ask me to summarize the whole document."
        
        # ========== CODE EXPLANATION ==========
        if any(word in question_lower for word in ['what does this code do', 'explain the code', 'how does this code work']):
            code_lines = [l for l in content.split('\n') if any(k in l for k in ['const', 'let', 'var', 'function', '=>', 'import', 'require'])]
            
            if code_lines:
                explanation = "💻 **CODE EXPLANATION:**\n\n"
                explanation += "This code appears to:\n\n"
                
                if any('http' in l.lower() for l in code_lines):
                    explanation += "• Create an HTTP web server\n"
                if any('fs' in l.lower() for l in code_lines):
                    explanation += "• Handle file system operations\n"
                if any('path' in l.lower() for l in code_lines):
                    explanation += "• Manage file paths\n"
                if any('cors' in l.lower() for l in code_lines):
                    explanation += "• Configure CORS for security\n"
                
                explanation += "\n💡 Ask me about specific parts for more details."
                return explanation
        
        # ========== FALLBACK - Show document preview ==========
        # Show first few lines of the document as a preview
        lines = content.split('\n')
        preview_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 10][:5]
        
        if preview_lines:
            preview = f"📄 **From '{filename}':**\n\n"
            for line in preview_lines:
                preview += f"• {line[:150]}{'...' if len(line) > 150 else ''}\n"
            preview += f"\n💡 Try asking: 'Summarize this document' or 'Explain the key points'"
            return preview
        
        return f"📖 **I can help you understand '{filename}'.**\n\nTry asking:\n• 'Summarize this document'\n• 'Explain the key points'\n• 'Tell me about [specific topic]'"