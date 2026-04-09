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
    def generate_long_summary(text, filename):
        """Generate a detailed, long-form summary of the document"""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Detect document type
        text_lower = text.lower()
        if 'contract' in text_lower or 'agreement' in text_lower:
            doc_type = "Legal Document"
            icon = "⚖️"
        elif 'http' in text_lower or 'server' in text_lower or 'const' in text_lower:
            doc_type = "Code/Technical Document"
            icon = "💻"
        else:
            doc_type = "Document"
            icon = "📄"
        
        # Get sentences and paragraphs
        sentences = re.split(r'[.!?\n]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Build a comprehensive summary
        summary = f"{icon} **DETAILED SUMMARY OF '{filename.upper()}'**\n\n"
        summary += f"📊 **Document Stats:** {len(text)} characters, {len(text.split())} words\n"
        summary += f"📁 **Document Type:** {doc_type}\n\n"
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Main content summary
        summary += f"**📖 MAIN CONTENT:**\n\n"
        
        # Extract key points (first 8-10 meaningful sentences)
        key_points = sentences[:10]
        for i, point in enumerate(key_points, 1):
            # Truncate if too long
            if len(point) > 300:
                point = point[:300] + "..."
            summary += f"{i}. {point}\n\n"
        
        # Add key themes/topics
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        summary += f"**🔑 KEY THEMES & TOPICS:**\n\n"
        
        # Extract important words/phrases
        words = re.findall(r'\b[A-Za-z]{4,}\b', text_lower)
        common_words = {}
        stopwords = {'this', 'that', 'these', 'those', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'what', 'which', 'when', 'where', 'how', 'why', 'being', 'been', 'very', 'just', 'but', 'not', 'are', 'was', 'for', 'and', 'the', 'you', 'your', 'can', 'has', 'had', 'its', 'also', 'than', 'then', 'them', 'into', 'such', 'more', 'other', 'about', 'than', 'after', 'before', 'without', 'through'}
        
        for word in words:
            if word not in stopwords and len(word) > 3:
                common_words[word] = common_words.get(word, 0) + 1
        
        # Get top themes
        top_themes = sorted(common_words.items(), key=lambda x: x[1], reverse=True)[:8]
        if top_themes:
            for theme, count in top_themes:
                summary += f"• **{theme.title()}** (appears {count} times)\n"
        else:
            summary += "• Unable to extract specific themes\n"
        
        summary += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Add questions to ask
        summary += f"**💡 SUGGESTED QUESTIONS YOU CAN ASK ME:**\n\n"
        summary += f"• 'What is the main purpose of this document?'\n"
        summary += f"• 'Explain the key points to me'\n"
        summary += f"• 'What does this document say about [specific topic]?'\n"
        summary += f"• 'Summarize this in simpler terms'\n"
        summary += f"• 'What are the most important takeaways?'\n\n"
        
        summary += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        summary += f"📌 **Do you have any questions about this document?** I'm here to help you understand it better! Just ask me anything. 💬"
        
        return summary
    
    @staticmethod
    def simplify_document(text, filename):
        """Generate simplified version of document (shorter version)"""
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
    def answer_question(client_id, question):
        """Answer question about the document"""
        doc = DocumentHandler.get_user_document(client_id)
        
        if not doc:
            return None
        
        content = doc['content']
        filename = doc['filename']
        question_lower = question.lower().strip()
        
        # Summary questions
        if any(word in question_lower for word in ['summary', 'summarize', 'overview', 'gist', 'what is this about', 'tell me about it']):
            return DocumentHandler.generate_long_summary(content, filename)
        
        # Key points questions
        if any(word in question_lower for word in ['key points', 'main points', 'important', 'takeaways']):
            sentences = re.split(r'[.!?\n]+', content)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:6]
            
            response = f"📌 **KEY POINTS FROM '{filename}':**\n\n"
            for i, sent in enumerate(sentences, 1):
                response += f"{i}. {sent}\n\n"
            response += f"\n💡 Would you like me to elaborate on any of these points?"
            return response
        
        # Search in document for specific terms
        keywords = re.findall(r'\b[a-zA-Z]{4,}\b', question_lower)
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'type', 'code', 'language', 'file', 'document', 'please', 'help', 'know', 'want', 'need', 'can', 'you', 'the', 'and', 'for', 'are', 'not', 'explain', 'mean', 'meaning', 'how', 'why', 'when', 'where', 'who', 'summarize', 'summary'}
        keywords = [k for k in keywords if k not in stopwords]
        
        for keyword in keywords[:3]:
            if keyword in content.lower():
                # Find sentences containing the keyword
                sentences = re.split(r'[.!?\n]+', content)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence) > 20:
                        return f"📖 **About '{keyword}' in '{filename}':**\n\n{sentence.strip()}\n\n💡 Does that answer your question? Feel free to ask for more details!"
        
        # Default response
        preview = content[:400] + "..." if len(content) > 400 else content
        return f"📄 **From '{filename}':**\n\n{preview}\n\n💡 Try asking: 'Summarize this document', 'What are the key points?', or ask about a specific topic!"