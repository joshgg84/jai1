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
    def detect_document_type(text, filename):
        """Detect the type of document"""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Code files
        code_extensions = ['.js', '.py', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx', '.html', '.css']
        if any(filename_lower.endswith(ext) for ext in code_extensions):
            return "Code File", "💻"
        
        # Resume/CV indicators
        if 'resume' in filename_lower or 'cv' in filename_lower:
            return "Resume/CV", "📄"
        if any(word in text_lower for word in ['experience', 'education', 'skills', 'work history', 'employment']):
            if any(word in text_lower for word in ['objective', 'summary', 'references']):
                return "Resume/CV", "📄"
        
        # Meeting notes
        if any(word in text_lower for word in ['meeting notes', 'meeting minutes', 'agenda', 'action items', 'attendees']):
            return "Meeting Notes", "📝"
        
        # Legal documents
        if any(word in text_lower for word in ['contract', 'agreement', 'terms and conditions', 'parties', 'hereby', 'whereas']):
            return "Legal Document", "⚖️"
        
        # Reports
        if any(word in text_lower for word in ['report', 'analysis', 'findings', 'recommendations', 'executive summary']):
            return "Report", "📊"
        
        # Technical documentation
        if any(word in text_lower for word in ['api', 'endpoint', 'request', 'response', 'authentication', 'documentation']):
            return "Technical Documentation", "📘"
        
        # Meeting/Conference notes
        if any(word in text_lower for word in ['conference', 'seminar', 'workshop', 'keynote', 'speaker']):
            return "Conference Notes", "🎤"
        
        # Default
        return "Document", "📄"
    
    @staticmethod
    def generate_long_summary(text, filename):
        """Generate a detailed, intelligent summary of the document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        doc_type, icon = DocumentHandler.detect_document_type(text, filename)
        
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
        
        # Helpful tips based on document type
        summary += "**💡 You can ask me:**\n"
        if doc_type == "Resume/CV":
            summary += "• 'What is this person's name?'\n• 'What are their skills?'\n• 'Where are they located?'\n"
        elif doc_type == "Code File":
            summary += "• 'What does this code do?'\n• 'Explain how this works'\n• 'What language is this?'\n"
        elif doc_type == "Meeting Notes":
            summary += "• 'What were the key decisions?'\n• 'What are the action items?'\n• 'Who attended?'\n"
        elif doc_type == "Legal Document":
            summary += "• 'What are the key terms?'\n• 'What are the obligations?'\n• 'What are the important dates?'\n"
        else:
            summary += "• 'Explain this document in simple terms'\n• 'What are the key points?'\n• 'Tell me about a specific section'\n"
        
        return summary
    
    @staticmethod
    def simplify_document(text, filename):
        """Generate simplified version of document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        doc_type, icon = DocumentHandler.detect_document_type(text, filename)
        
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
    def _call_jai_for_explanation(content, filename, question):
        """Use JAI to actually explain the document content"""
        try:
            # Take a relevant portion of the document (first 3000 chars)
            doc_excerpt = content[:3000] if len(content) > 3000 else content
            
            # Build a prompt for JAI to explain - generic for any document type
            prompt = f"""You are analyzing a document named "{filename}". 

DOCUMENT CONTENT:
{doc_excerpt}

USER QUESTION: {question}

Please provide a clear, helpful, and informative answer based ONLY on the document content above.

Guidelines:
- Read and understand the document first
- Answer the user's question directly
- If asking for an explanation, explain in simple, clear terms
- Extract and state specific information (names, dates, skills, decisions, code functions, etc.)
- Be conversational and helpful
- If the document doesn't contain the information, say so politely

Your response:"""
            
            # Call JAI API
            response = requests.post(
                "https://jai1-sh81.onrender.com/api/chat",
                json={"message": prompt, "clientId": "document_handler", "options": {"speech": False}},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("response", None)
            return None
        except Exception as e:
            logger.error(f"JAI explanation error: {e}")
            return None
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer questions about the document using AI explanation"""
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
        
        # ========== USE JAI TO ACTUALLY EXPLAIN ==========
        # For ANY question, let JAI provide an intelligent explanation
        if len(question_lower) > 2:
            ai_explanation = DocumentHandler._call_jai_for_explanation(content, filename, question)
            if ai_explanation and len(ai_explanation) > 10:
                # Clean up the response
                ai_explanation = re.sub(r'^(AI:|Assistant:|Response:)\s*', '', ai_explanation)
                return ai_explanation
        
        # ========== FALLBACK - Show document preview ==========
        lines = content.split('\n')
        preview_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 10][:5]
        
        if preview_lines:
            preview = f"📄 **From '{filename}':**\n\n"
            for line in preview_lines:
                preview += f"• {line[:150]}{'...' if len(line) > 150 else ''}\n"
            preview += f"\n💡 Try asking: 'Summarize this document' or 'Explain what this means'"
            return preview
        
        return f"📖 **I can help you understand '{filename}'.**\n\nTry asking:\n• 'Summarize this document'\n• 'Explain what this means'\n• 'Tell me about [specific topic]'"