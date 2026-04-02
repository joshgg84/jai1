"""JAI - Document Intelligence Module
Handles document upload, text extraction, simplification, and Q&A.
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

# Store documents in memory
_documents = {}


class DocumentHandler:
    """Handle document upload and processing"""
    
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
        elif any(word in text_lower for word in ['invoice', 'payment', 'amount', 'due']):
            icon = "💰"
            doc_name = "Financial Document"
        else:
            icon = "📄"
            doc_name = "Document"
        
        # Extract key points (first 3-5 substantial sentences)
        sentences = re.split(r'[.!?]+', text)
        key_points = []
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and len(key_points) < 5:
                key_points.append(s)
        
        # Build response
        simplified = f"{icon} **{doc_name} Simplified**\n\n"
        simplified += f"**File:** {filename}\n"
        simplified += f"**Length:** {len(text)} characters\n\n"
        
        if key_points:
            simplified += f"**Main Points:**\n\n"
            for i, point in enumerate(key_points, 1):
                # Truncate long points
                if len(point) > 200:
                    point = point[:197] + "..."
                simplified += f"{i}. {point}\n\n"
        else:
            preview = text[:400] + "..." if len(text) > 400 else text
            simplified += f"**Content:**\n\n{preview}\n\n"
        
        simplified += f"**💡 Tip:** Ask me specific questions like 'What does this say about [topic]?' or 'Summarize the main points'"
        
        return simplified
    
    @staticmethod
    def answer_question(doc_id, question):
        """Answer questions about a document"""
        if doc_id not in _documents:
            return None
        
        doc = _documents[doc_id]
        content = doc['content']
        filename = doc['filename']
        
        question_lower = question.lower().strip()
        
        # Handle empty or very short questions
        if len(question_lower) < 5:
            return f"💡 **Ask me about '{filename}':**\n\nTry asking:\n• 'What is this document about?'\n• 'Summarize the key points'\n• 'Tell me about [specific topic]'\n• 'What does it say regarding...'"
        
        # Summary request
        if any(word in question_lower for word in ['summary', 'overview', 'what is this about', 'tell me about', 'what does it say']):
            # Get first few key sentences
            sentences = re.split(r'[.!?]+', content)
            summary_points = []
            for s in sentences[:10]:
                s = s.strip()
                if len(s) > 30:
                    summary_points.append(s)
            
            if summary_points:
                response = f"📋 **Summary of '{filename}':**\n\n"
                for i, point in enumerate(summary_points[:4], 1):
                    if len(point) > 200:
                        point = point[:197] + "..."
                    response += f"{i}. {point}\n\n"
                response += "Anything specific you'd like to know more about?"
                return response
            else:
                preview = content[:500] + "..." if len(content) > 500 else content
                return f"📋 **From '{filename}':**\n\n{preview}\n\nWhat specific information are you looking for?"
        
        # Search for keywords in content
        # Extract meaningful words from question
        keywords = re.findall(r'\b[a-z]{4,}\b', question_lower)
        # Remove common words
        stopwords = {'what', 'does', 'this', 'that', 'tell', 'about', 'from', 'with', 'have', 'were', 'there', 'their', 'they', 'will', 'would', 'could', 'should', 'been', 'being', 'some', 'such', 'than', 'then', 'these', 'those'}
        keywords = [k for k in keywords if k not in stopwords]
        
        # Search for each keyword
        found_info = []
        for keyword in keywords[:5]:
            if keyword in content.lower():
                # Find sentences containing keyword
                sentences = re.split(r'[.!?]+', content)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 20:
                        sentence = sentence.strip()
                        if len(sentence) > 300:
                            sentence = sentence[:297] + "..."
                        found_info.append((keyword, sentence))
                        break
        
        if found_info:
            response = f"📖 **About your document '{filename}':**\n\n"
            for keyword, sentence in found_info[:3]:
                response += f"**• {keyword.capitalize()}:** {sentence}\n\n"
            response += "Does that help? Ask me more questions!"
            return response
        
        # If no keywords found, offer help
        if len(content) > 100:
            preview = content[:300] + "..." if len(content) > 300 else content
            return f"📄 **From '{filename}':**\n\n{preview}\n\nI couldn't find specific information about that. Could you rephrase your question or ask about a different topic?"
        else:
            return f"📄 **Document content:**\n\n{content}\n\nWhat would you like to know about this?"
    
    @staticmethod
    def store_document(filename, text, simplified):
        """Store document and return ID"""
        doc_id = datetime.now().strftime("%Y%m%d%H%M%S")
        _documents[doc_id] = {
            'filename': filename,
            'content': text,
            'simplified': simplified,
            'created_at': datetime.now(),
            'size': len(text)
        }
        logger.info(f"Document stored with ID: {doc_id}, size: {len(text)} chars")
        return doc_id
    
    @staticmethod
    def get_document(doc_id):
        """Get document by ID"""
        return _documents.get(doc_id)
    
    @staticmethod
    def get_all_documents():
        """Get all documents (for debugging)"""
        return {doc_id: {'filename': doc['filename'], 'size': doc['size']} 
                for doc_id, doc in _documents.items()}