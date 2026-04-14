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
        summary = f"{icon} **DETAILED ANALYSIS OF '{filename.upper()}'**\n\n"
        summary += f"📊 **Document Stats:** {len(text)} characters, {len(text.split())} words\n"
        summary += f"📁 **Document Type:** {doc_type}\n\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Main content explanation
        summary += f"**📖 WHAT THIS DOCUMENT CONTAINS:**\n\n"
        
        # Extract key points
        key_points = sentences[:10]
        for i, point in enumerate(key_points, 1):
            if len(point) > 300:
                point = point[:300] + "..."
            summary += f"{i}. {point}\n\n"
        
        # Add contextual understanding
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Intelligent analysis based on content type
        if 'resume' in doc_type.lower() or 'cv' in doc_type.lower():
            summary += f"**🔍 UNDERSTANDING THIS RESUME/CV:**\n\n"
            summary += f"This appears to be a resume or CV. Here's what I can help you understand:\n\n"
            summary += f"• The person's contact information and location\n"
            summary += f"• Their professional experience and skills\n"
            summary += f"• Their education background\n"
            summary += f"• Their career achievements\n"
            summary += f"• Areas where they might need improvement\n\n"
        elif 'code' in doc_type.lower() or 'const' in text_lower or 'function' in text_lower:
            summary += f"**🔍 UNDERSTANDING THIS CODE:**\n\n"
            summary += f"This appears to be a code file. Here's what I can help you understand:\n\n"
            summary += f"• What each function/component does\n"
            summary += f"• How the different parts work together\n"
            summary += f"• The purpose and logic behind the code\n"
            summary += f"• Potential issues or improvements\n"
            summary += f"• How to run or test the code\n\n"
        elif 'legal' in doc_type.lower() or 'contract' in text_lower:
            summary += f"**🔍 UNDERSTANDING THIS LEGAL DOCUMENT:**\n\n"
            summary += f"This appears to be a legal document. I can help you understand:\n\n"
            summary += f"• Key terms and conditions\n"
            summary += f"• Important clauses and obligations\n"
            summary += f"• Rights and responsibilities of each party\n"
            summary += f"• Potential risks or concerns\n"
            summary += f"• Deadlines and important dates\n\n"
        else:
            summary += f"**🔍 WHAT YOU CAN ASK ME:**\n\n"
            summary += f"• 'Explain this document in detail'\n"
            summary += f"• 'What are the main points?'\n"
            summary += f"• 'Summarize the key takeaways'\n"
            summary += f"• 'Tell me about [specific section]'\n"
            summary += f"• 'What does this document say about [topic]?'\n\n"
        
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        summary += f"💬 **Go ahead and ask me anything about this document!** I'll provide detailed, helpful explanations."
        
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
        else:
            icon, doc_type = "📄", "Document"
        
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10][:6]
        
        simplified = f"{icon} **{doc_type}**\n\n"
        simplified += f"📄 {filename}\n"
        simplified += f"📊 {len(text)} characters\n\n"
        
        if lines:
            simplified += f"**Main content:**\n\n"
            for i, line in enumerate(lines, 1):
                simplified += f"{i}. {line[:150]}{'...' if len(line) > 150 else ''}\n\n"
        
        simplified += f"💡 **Ask me to explain anything you don't understand in detail!**"
        
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
        """Intelligently answer questions about the document with detailed explanations"""
        doc = DocumentHandler.get_user_document(client_id)
        
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SUMMARY REQUESTS ==========
        if any(word in question_lower for word in ['summarize', 'summary', 'overview', 'gist', 'what is this about', 'tell me about it', 'explain the document']):
            return DocumentHandler.generate_long_summary(content, filename)
        
        # ========== EXPLAIN IN SIMPLE TERMS (LONGER VERSION) ==========
        if any(word in question_lower for word in ['explain simply', 'simple terms', 'easy explanation', 'for a beginner', 'explain like']):
            # Get more sentences for a longer explanation
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:12]
            
            simple_explanation = f"📖 **DETAILED SIMPLE EXPLANATION OF '{filename}':**\n\n"
            simple_explanation += "Here's what this document is about, explained in simple, easy-to-understand terms:\n\n"
            simple_explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            # Add context about the document type
            if 'resume' in filename.lower() or 'cv' in filename.lower():
                simple_explanation += "**📄 This is a Resume/CV document** - It contains information about a person's professional background.\n\n"
                simple_explanation += "**Key sections found in this document:**\n\n"
            elif 'code' in filename.lower() or '.js' in filename.lower() or '.py' in filename.lower():
                simple_explanation += "**💻 This is a Code document** - It contains programming instructions.\n\n"
                simple_explanation += "**What this code appears to do:**\n\n"
            else:
                simple_explanation += "**📄 Document Overview:**\n\n"
            
            for i, sent in enumerate(sentences, 1):
                # Shorten very long sentences but keep meaning
                if len(sent) > 200:
                    sent = sent[:200] + "..."
                simple_explanation += f"{i}. {sent}\n\n"
            
            simple_explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            simple_explanation += "💡 **Want me to go deeper?** Ask me:\n"
            simple_explanation += "• 'Tell me more about [specific section]'\n"
            simple_explanation += "• 'What does this mean for me?'\n"
            simple_explanation += "• 'Explain [specific term] in more detail'\n\n"
            simple_explanation += "I'm here to help you fully understand this document!"
            return simple_explanation
        
        # ========== EXPLAIN SPECIFIC TOPIC IN DETAIL ==========
        explain_match = re.search(r'explain\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\?|$| please| to me| in detail)', question_lower)
        if explain_match:
            topic = explain_match.group(1).strip()
            
            # Search for relevant sentences in the document
            sentences = re.split(r'[.!?\n]+', content)
            relevant_sentences = []
            
            for sentence in sentences:
                if topic.lower() in sentence.lower() and len(sentence) > 20:
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                explanation = f"📖 **DETAILED EXPLANATION OF '{topic.title()}' IN '{filename}':**\n\n"
                explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                for i, sent in enumerate(relevant_sentences[:5], 1):
                    explanation += f"{i}. {sent}\n\n"
                explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                explanation += "💡 **Does this answer your question?** I can provide even more detail if needed!\n"
                explanation += "• Ask 'Tell me more about this'\n"
                explanation += "• Ask 'Give me examples'\n"
                explanation += "• Ask 'Why is this important?'"
                return explanation
            else:
                return f"I couldn't find specific information about '{topic}' in this document. Could you rephrase your question or ask about something else?"
        
        # ========== CODE EXPLANATION (DETAILED) ==========
        if any(word in question_lower for word in ['what does this code do', 'explain the code', 'how does this code work', 'what is this code for']):
            # Find code blocks or technical content
            code_lines = [l for l in content.split('\n') if any(keyword in l for keyword in ['const', 'let', 'var', 'function', '=>', 'import', 'require', 'app.', 'server'])]
            
            if code_lines:
                explanation = "💻 **DETAILED CODE EXPLANATION:**\n\n"
                explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                explanation += "**What this code does:**\n\n"
                
                # Analyze code purpose
                if any('http' in l.lower() for l in code_lines):
                    explanation += "• **HTTP Server:** This code creates a web server that listens for incoming requests from browsers or other applications.\n\n"
                if any('fs' in l.lower() for l in code_lines):
                    explanation += "• **File System Operations:** This code can read, write, and manage files on the computer's storage.\n\n"
                if any('path' in l.lower() for l in code_lines):
                    explanation += "• **Path Management:** This code handles file and directory paths, making sure they work across different operating systems.\n\n"
                if any('cors' in l.lower() for l in code_lines):
                    explanation += "• **CORS Configuration:** This code controls which websites are allowed to access this server (important for security).\n\n"
                if any('vulnerable' in l.lower() for l in code_lines):
                    explanation += "• **⚠️ Security Note:** This code contains intentional vulnerabilities meant for learning about security risks.\n\n"
                
                explanation += "**How it works step by step:**\n\n"
                explanation += "1. The server starts and listens for connections on a specific port\n"
                explanation += "2. When a request comes in, the server processes it based on the URL path\n"
                explanation += "3. The server sends back a response (HTML, JSON, or other data)\n"
                explanation += "4. Error handling catches any issues that might occur\n\n"
                
                explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                explanation += "💡 **Want to learn more? Ask me:**\n"
                explanation += "• 'What is a web server?'\n"
                explanation += "• 'How do I run this code?'\n"
                explanation += "• 'What are the security risks here?'\n"
                explanation += "• 'How can I improve this code?'"
                return explanation
            else:
                return "This appears to be a text document. Ask me to summarize it or explain specific parts in detail!"
        
        # ========== KEY POINTS WITH DETAILS ==========
        if any(word in question_lower for word in ['key points', 'main points', 'important', 'takeaways', 'what matters', 'most important']):
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:8]
            
            response = f"📌 **KEY POINTS FROM '{filename}' (WITH DETAILS):**\n\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, sent in enumerate(sentences, 1):
                if len(sent) > 250:
                    sent = sent[:250] + "..."
                response += f"{i}. {sent}\n\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            response += f"💡 **Would you like me to elaborate on any of these points?** Just ask!\n"
            response += f"• 'Tell me more about point {sentences[0][:30]}...'\n"
            response += f"• 'Explain the first point in detail'"
            return response
        
        # ========== GENERAL DETAILED EXPLANATION ==========
        # Try to find relevant content
        keywords = re.findall(r'\b[a-zA-Z]{4,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not', 'explain', 'mean', 'meaning', 'how', 'why', 'when', 'where', 'who'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Find sentences containing keywords
        sentences = re.split(r'[.!?\n]+', content)
        relevant_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords[:3]):
                if len(sentence.strip()) > 20:
                    relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            explanation = f"📖 **FROM '{filename}':**\n\n"
            explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, sent in enumerate(relevant_sentences[:4], 1):
                if len(sent) > 300:
                    sent = sent[:300] + "..."
                explanation += f"{i}. {sent}\n\n"
            explanation += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            explanation += "💡 **Need more detail?** Try asking:\n"
            explanation += "• 'Explain this in more depth'\n"
            explanation += "• 'What does this mean practically?'\n"
            explanation += "• 'Give me examples of this'"
            return explanation
        
        # ========== FALLBACK - OFFER DETAILED HELP ==========
        return f"📖 **I'm here to help you understand '{filename}' in detail!**\n\n" \
               f"Try asking me:\n\n" \
               f"• 'Explain this document in simple terms' - I'll break it down for you\n" \
               f"• 'What are the key points?' - I'll list the most important information\n" \
               f"• 'Tell me about [specific topic]' - I'll find and explain that section\n" \
               f"• 'What does this code do?' - I'll explain the code step by step\n" \
               f"• 'Explain this like I'm 5' - I'll use very simple language\n\n" \
               f"What would you like me to explain in detail?"