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
            doc_type = "legal"
            icon = "⚖️"
            doc_name = "Legal Document"
        elif any(word in text_lower for word in ['exam', 'test', 'question', 'student', 'course']):
            doc_type = "educational"
            icon = "📚"
            doc_name = "Educational Document"
        elif any(word in text_lower for word in ['invoice', 'payment', 'amount', 'due']):
            doc_type = "financial"
            icon = "💰"
            doc_name = "Financial Document"
        else:
            doc_type = "general"
            icon = "📄"
            doc_name = "Document"
        
        # Extract key points
        sentences = re.split(r'[.!?]+', text)
        key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        
        # Build response
        simplified = f"{icon} **{doc_name} Simplified**\n\n"
        simplified += f"**Original:** {filename}\n"
        simplified += f"**Length:** {len(text)} characters\n\n"
        
        if key_points:
            simplified += f"**Key Points:**\n\n"
            for i, point in enumerate(key_points, 1):
                simplified += f"{i}. {point}\n\n"
        else:
            preview = text[:500] + "..." if len(text) > 500 else text
            simplified += f"**Content:**\n\n{preview}\n\n"
        
        # Add tips
        tips = {
            "legal": "⚠️ Read carefully. Consider professional advice for important matters.",
            "educational": "📖 Review key points and ask questions about unclear concepts.",
            "financial": "💵 Verify all amounts and dates carefully.",
            "general": "💡 Review the information and ask if anything is unclear."
        }
        simplified += f"**Tip:** {tips.get(doc_type, tips['general'])}"
        
        return simplified, doc_type
    
    @staticmethod
    def answer_question(doc_id, question):
        """Answer questions about a document"""
        if doc_id not in _documents:
            return None
        
        doc = _documents[doc_id]
        content = doc['content']
        filename = doc['filename']
        
        question_lower = question.lower()
        
        # Summary request
        if any(word in question_lower for word in ['summary', 'overview', 'what is this about']):
            return f"📋 **Summary of '{filename}':**\n\n{doc['simplified'][:400]}...\n\nAsk me about specific parts!"
        
        # Keyword search
        keywords = re.findall(r'\b\w+\b', question_lower)
        keywords = [k for k in keywords if len(k) > 3 and k not in ['what', 'does', 'this', 'that', 'tell', 'about']]
        
        for keyword in keywords[:3]:
            if keyword in content.lower():
                sentences = re.split(r'[.!?]+', content)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 20:
                        return f"📖 **About '{keyword}':**\n{sentence.strip()}\n\nAnything else?"
        
        # Fallback
        preview = content[:400] + "..." if len(content) > 400 else content
        return f"📄 **From '{filename}':**\n\n{preview}\n\nCould you be more specific about what you're looking for?"
    
    @staticmethod
    def store_document(filename, text, simplified, doc_type):
        """Store document and return ID"""
        doc_id = datetime.now().strftime("%Y%m%d%H%M%S")
        _documents[doc_id] = {
            'filename': filename,
            'content': text,
            'simplified': simplified,
            'type': doc_type,
            'created_at': datetime.now(),
            'size': len(text)
        }
        return doc_id
    
    @staticmethod
    def get_document(doc_id):
        """Get document by ID"""
        return _documents.get(doc_id)