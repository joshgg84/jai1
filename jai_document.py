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
        
        # Vulnerable server code (educational)
        if 'vulnerable' in filename_lower or ('const' in text_lower and 'http' in text_lower and 'fs' in text_lower):
            return "Educational Code (Vulnerable Server)", "⚠️"
        
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
        elif "Code" in doc_type:
            summary += "• 'Explain what this code does in detail'\n• 'What are the vulnerabilities?'\n• 'How does this server work?'\n"
        elif doc_type == "Meeting Notes":
            summary += "• 'What were the key decisions?'\n• 'What are the action items?'\n"
        else:
            summary += "• 'Explain this document in simple terms'\n• 'What are the key points?'\n"
        
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
        simplified += "💡 **Ask me:** 'Explain what this code does' or 'What are the vulnerabilities?'"
        
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
        """Use JAI to actually explain the document content with detailed, long explanations"""
        try:
            # Take a larger portion of the document for better context
            doc_excerpt = content[:4000] if len(content) > 4000 else content
            
            # Build a detailed prompt for JAI to provide LONG explanations
            prompt = f"""You are an AI assistant analyzing a document. Provide a VERY DETAILED, COMPREHENSIVE explanation.

DOCUMENT NAME: {filename}
DOCUMENT CONTENT:
{doc_excerpt}

USER QUESTION: {question}

INSTRUCTIONS FOR YOUR RESPONSE:
1. Write a LONG, DETAILED explanation (at least 4-6 sentences, preferably more)
2. DO NOT just repeat or copy the document text
3. EXPLAIN in your own words what the document means
4. If it's code, explain:
   - What each module/function does
   - How the different parts work together
   - What the purpose of the code is
   - Any security implications or vulnerabilities
5. If it's a resume, state:
   - The person's full name
   - Their location
   - Their skills and technologies
   - Their experience and projects
   - Their education
6. If it's meeting notes, summarize:
   - Key decisions made
   - Action items with owners
   - Important discussion points
7. Be conversational, educational, and thorough

Your detailed explanation:"""
            
            # Call JAI API with longer timeout
            response = requests.post(
                "https://jai1-sh81.onrender.com/api/chat",
                json={"message": prompt, "clientId": "document_explainer", "options": {"speech": False}},
                timeout=45
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("response", None)
                if result and len(result) > 50:
                    return result
            return None
        except Exception as e:
            logger.error(f"JAI explanation error: {e}")
            return None
    
    @staticmethod
    def _get_detailed_code_explanation(content, filename):
        """Provide a detailed explanation for code files when JAI is unavailable"""
        lines = content.split('\n')
        code_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 5]
        
        explanation = f"⚠️ **DETAILED CODE ANALYSIS: '{filename}'**\n\n"
        
        # Detect modules used
        modules = []
        if any('http' in l.lower() for l in code_lines):
            modules.append("HTTP (for creating web servers)")
        if any('fs' in l.lower() for l in code_lines):
            modules.append("File System (fs) for reading/writing files")
        if any('path' in l.lower() for l in code_lines):
            modules.append("Path for handling file paths")
        if any('cors' in l.lower() for l in code_lines):
            modules.append("CORS for cross-origin requests")
        
        if modules:
            explanation += f"**What this code is:**\n"
            explanation += f"This is a Node.js server application that uses the following modules:\n"
            for m in modules:
                explanation += f"  • {m}\n"
            explanation += "\n"
        
        # Explain what the code does
        explanation += f"**What it does:**\n"
        if any('createServer' in l for l in code_lines):
            explanation += "• Creates an HTTP web server that listens for incoming requests\n"
        if any('readFile' in l or 'writeFile' in l for l in code_lines):
            explanation += "• Reads and writes files on the server's file system\n"
        if any('listen' in l for l in code_lines):
            explanation += "• Listens for connections on a specific port\n"
        if any('request' in l.lower() or 'response' in l.lower() for l in code_lines):
            explanation += "• Handles HTTP requests and sends back responses\n"
        
        # Security notes
        if 'vulnerable' in filename.lower():
            explanation += "\n**⚠️ Security Warning:**\n"
            explanation += "This code contains intentional vulnerabilities for educational purposes:\n"
            explanation += "• It may have insecure CORS settings (allowing any origin)\n"
            explanation += "• It may not validate user input properly\n"
            explanation += "• It's designed to teach you what NOT to do in production\n"
        
        explanation += "\n💡 For an even more detailed explanation, try asking specific questions like:\n"
        explanation += "• 'What does the http module do?'\n"
        explanation += "• 'How does the server handle requests?'\n"
        explanation += "• 'What are the security risks here?'"
        
        return explanation
    
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
        # Try to get an intelligent, detailed explanation from JAI
        ai_explanation = DocumentHandler._call_jai_for_explanation(content, filename, question)
        if ai_explanation and len(ai_explanation) > 100:
            return ai_explanation
        
        # ========== FALLBACK - Provide a detailed explanation based on document type ==========
        doc_type, icon = DocumentHandler.detect_document_type(content, filename)
        
        if "Code" in doc_type or "vulnerable" in filename.lower():
            return DocumentHandler._get_detailed_code_explanation(content, filename)
        
        # For any other document type, provide a preview with more detail
        lines = content.split('\n')
        meaningful_lines = [l.strip() for l in lines if l.strip() and len(l.strip()) > 20][:6]
        
        if meaningful_lines:
            explanation = f"📄 **Document Analysis: '{filename}'**\n\n"
            explanation += f"**Document Type:** {doc_type}\n"
            explanation += f"**Total Size:** {len(content)} characters, {len(content.split())} words\n\n"
            explanation += f"**Key excerpts from the document:**\n\n"
            
            for i, line in enumerate(meaningful_lines, 1):
                explanation += f"{i}. {line[:250]}{'...' if len(line) > 250 else ''}\n\n"
            
            explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            explanation += f"💡 **To understand this better, try asking:**\n"
            explanation += f"• 'Summarize this document in detail'\n"
            explanation += f"• 'Explain what this document is about'\n"
            explanation += f"• 'What are the key points from this document?'\n"
            explanation += f"• 'Tell me about [specific topic]'"
            return explanation
        
        return f"📖 **I can help you understand '{filename}' in detail.**\n\nTry asking:\n• 'Summarize this document'\n• 'Explain what this document means'\n• 'What are the key points?'\n• 'Tell me about the main topics'"