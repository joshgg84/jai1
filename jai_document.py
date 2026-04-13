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
        elif 'report' in text_lower or 'analysis' in text_lower:
            doc_type = "Report"
            icon = "📊"
        else:
            doc_type = "Document"
            icon = "📄"
        
        # Get key sentences (first few meaningful sentences)
        sentences = re.split(r'[.!?\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Build intelligent summary
        summary = f"{icon} **INTELLIGENT SUMMARY OF '{filename.upper()}'**\n\n"
        summary += f"📊 **Document Stats:** {len(text)} characters, {len(text.split())} words\n"
        summary += f"📁 **Document Type:** {doc_type}\n\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Main content explanation
        summary += f"**📖 WHAT THIS DOCUMENT CONTAINS:**\n\n"
        
        # Extract key points intelligently
        key_points = sentences[:8]
        for i, point in enumerate(key_points, 1):
            if len(point) > 300:
                point = point[:300] + "..."
            summary += f"{i}. {point}\n\n"
        
        # Add contextual understanding
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Intelligent analysis based on content type
        if 'code' in doc_type.lower() or 'const' in text_lower or 'function' in text_lower:
            summary += f"**🔍 UNDERSTANDING THIS CODE:**\n\n"
            summary += f"This appears to be a code file. Here's what I can help you understand:\n\n"
            summary += f"• What each function/component does\n"
            summary += f"• How the different parts work together\n"
            summary += f"• The purpose and logic behind the code\n"
            summary += f"• Potential issues or improvements\n\n"
        elif 'legal' in doc_type.lower() or 'contract' in text_lower:
            summary += f"**🔍 UNDERSTANDING THIS LEGAL DOCUMENT:**\n\n"
            summary += f"This appears to be a legal document. I can help you understand:\n\n"
            summary += f"• Key terms and conditions\n"
            summary += f"• Important clauses and obligations\n"
            summary += f"• Rights and responsibilities\n"
            summary += f"• Potential risks or concerns\n\n"
        else:
            summary += f"**🔍 WHAT YOU CAN ASK ME:**\n\n"
            summary += f"• Explain this document in simple terms\n"
            summary += f"• What are the main points?\n"
            summary += f"• Summarize the key takeaways\n"
            summary += f"• Answer questions about specific content\n\n"
        
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        summary += f"💬 **Go ahead and ask me anything about this document!** I'll explain it in a way that makes sense to you."
        
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
        
        simplified += f"💡 **Ask me to explain anything you don't understand!**"
        
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
        """Intelligently answer questions about the document"""
        doc = DocumentHandler.get_user_document(client_id)
        
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # ========== SUMMARY REQUESTS ==========
        if any(word in question_lower for word in ['summarize', 'summary', 'overview', 'gist', 'what is this about', 'tell me about it', 'explain the document']):
            return DocumentHandler.generate_long_summary(content, filename)
        
        # ========== EXPLAIN IN SIMPLE TERMS ==========
        if any(word in question_lower for word in ['explain simply', 'simple terms', 'easy explanation', 'for a beginner']):
            # Get first few key sentences
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
            
            simple_explanation = f"📖 **Simple Explanation of '{filename}':**\n\n"
            simple_explanation += "Here's what this document is about in simple terms:\n\n"
            
            for i, sent in enumerate(sentences, 1):
                # Shorten long sentences
                if len(sent) > 150:
                    sent = sent[:150] + "..."
                simple_explanation += f"{i}. {sent}\n\n"
            
            simple_explanation += "\n💡 Want me to explain any specific part in more detail?"
            return simple_explanation
        
        # ========== CODE EXPLANATION ==========
        if any(word in question_lower for word in ['what does this code do', 'explain the code', 'how does this code work', 'what is this code for']):
            # Find code blocks or technical content
            code_lines = [l for l in content.split('\n') if any(keyword in l for keyword in ['const', 'let', 'var', 'function', '=>', 'import', 'require'])]
            
            if code_lines:
                explanation = "💻 **Code Explanation:**\n\n"
                explanation += "This appears to be code that:\n\n"
                
                # Analyze code purpose
                if any('http' in l.lower() for l in code_lines):
                    explanation += "• Creates an HTTP web server\n"
                if any('fs' in l.lower() for l in code_lines):
                    explanation += "• Handles file system operations (reading/writing files)\n"
                if any('path' in l.lower() for l in code_lines):
                    explanation += "• Manages file and directory paths\n"
                if any('cors' in l.lower() for l in code_lines):
                    explanation += "• Configures CORS (cross-origin resource sharing)\n"
                if any('vulnerable' in l.lower() for l in code_lines):
                    explanation += "• ⚠️ Contains intentional security vulnerabilities for learning\n"
                
                explanation += "\n**How it works:**\n"
                explanation += "The code sets up a server that listens for requests and responds accordingly.\n\n"
                explanation += "💡 Ask me about specific parts like 'What does the http module do?' or 'Explain the CORS settings'"
                return explanation
            else:
                return "This appears to be a text document. Ask me to summarize it or explain specific parts!"
        
        # ========== EXPLAIN SPECIFIC TOPIC ==========
        # Extract what the user wants explained
        explain_match = re.search(r'explain\s+(?:the\s+)?([a-zA-Z\s]+?)(?:\?|$| please| to me)', question_lower)
        if explain_match:
            topic = explain_match.group(1).strip()
            
            # Search for relevant sentences in the document
            sentences = re.split(r'[.!?\n]+', content)
            relevant_sentences = []
            
            for sentence in sentences:
                if topic.lower() in sentence.lower() and len(sentence) > 20:
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                explanation = f"📖 **About '{topic.title()}' in '{filename}':**\n\n"
                for sent in relevant_sentences[:3]:
                    explanation += f"• {sent}\n\n"
                explanation += "💡 Does that help? Want me to explain further?"
                return explanation
        
        # ========== KEY POINTS ==========
        if any(word in question_lower for word in ['key points', 'main points', 'important', 'takeaways', 'what matters']):
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:6]
            
            response = f"📌 **KEY POINTS FROM '{filename}':**\n\n"
            for i, sent in enumerate(sentences, 1):
                if len(sent) > 200:
                    sent = sent[:200] + "..."
                response += f"{i}. {sent}\n\n"
            response += f"\n💡 Want me to explain any of these points in more detail?"
            return response
        
        # ========== GENERAL EXPLANATION ==========
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
            explanation = f"📖 **From '{filename}':**\n\n"
            for sent in relevant_sentences[:3]:
                if len(sent) > 250:
                    sent = sent[:250] + "..."
                explanation += f"• {sent}\n\n"
            explanation += "💡 Does that answer your question? Want me to explain differently?"
            return explanation
        
        # ========== FALLBACK - OFFER HELP ==========
        return f"📖 **I'm here to help you understand '{filename}'!**\n\n" \
               f"Try asking me:\n" \
               f"• 'Summarize this document'\n" \
               f"• 'Explain this in simple terms'\n" \
               f"• 'What are the key points?'\n" \
               f"• 'Explain what [specific topic] means'\n" \
               f"• 'What does this code do?'\n\n" \
               f"What would you like me to explain?"