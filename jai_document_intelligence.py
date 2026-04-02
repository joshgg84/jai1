"""JAI - Document Intelligence Module
Upload, simplify, and chat with any document (PDF, DOCX, TXT)
"""

import os
import re
import logging
import tempfile
from datetime import datetime
import requests
import json

logger = logging.getLogger(__name__)

# Try to import document processing libraries
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PyPDF2 not installed. PDF support disabled.")

try:
    import docx
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    logger.warning("python-docx not installed. DOCX support disabled.")


class DocumentIntelligence:
    """Handle document upload, simplification, and Q&A"""
    
    # Store processed documents in memory (could move to database)
    _documents = {}  # {doc_id: {'content': str, 'simplified': str, 'filename': str, 'created_at': datetime}}
    
    @classmethod
    def extract_text_from_file(cls, file_content, filename):
        """Extract text from uploaded file"""
        file_ext = filename.split('.')[-1].lower()
        
        try:
            if file_ext == 'txt':
                return file_content.decode('utf-8')
            
            elif file_ext == 'pdf' and PDF_SUPPORT:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                # Extract text
                text = ""
                with open(tmp_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                
                os.unlink(tmp_path)
                return text
            
            elif file_ext == 'docx' and DOCX_SUPPORT:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                # Extract text
                doc = docx.Document(tmp_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                os.unlink(tmp_path)
                return text
            
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return None
    
    @classmethod
    def simplify_document(cls, text, filename):
        """Simplify document text using AI"""
        # Clean and prepare text
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Truncate if too long (first 5000 chars for now)
        original_length = len(text)
        if len(text) > 5000:
            text = text[:5000] + "..."
        
        # Generate simplified version
        simplified = cls._generate_simplified_version(text, filename)
        
        # Create document record
        doc_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(hash(filename))[:8]
        cls._documents[doc_id] = {
            'content': text,
            'simplified': simplified,
            'filename': filename,
            'created_at': datetime.now(),
            'original_length': original_length
        }
        
        return {
            'doc_id': doc_id,
            'filename': filename,
            'original_length': original_length,
            'simplified_length': len(simplified),
            'simplified': simplified
        }
    
    @classmethod
    def _generate_simplified_version(cls, text, filename):
        """Generate a simplified version of the document"""
        
        # Detect document type
        doc_type = cls._detect_document_type(text, filename)
        
        # Create summary based on length
        if len(text) < 500:
            return cls._simplify_short_document(text, doc_type)
        elif len(text) < 2000:
            return cls._simplify_medium_document(text, doc_type)
        else:
            return cls._simplify_long_document(text, doc_type)
    
    @classmethod
    def _detect_document_type(cls, text, filename):
        """Detect what kind of document this is"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['contract', 'agreement', 'terms', 'conditions', 'party', 'hereby']):
            return 'legal'
        elif any(word in text_lower for word in ['exam', 'test', 'question', 'answer', 'grade', 'student']):
            return 'educational'
        elif any(word in text_lower for word in ['invoice', 'payment', 'amount', 'due', 'bill']):
            return 'financial'
        elif any(word in text_lower for word in ['policy', 'procedure', 'guideline', 'regulation']):
            return 'policy'
        else:
            return 'general'
    
    @classmethod
    def _simplify_short_document(cls, text, doc_type):
        """Simplify a short document"""
        if doc_type == 'legal':
            return f"📄 **Document Summary**\n\nThis document appears to be a legal agreement. Here's what it says in plain English:\n\n{text}\n\n**Key points to understand:**\n• Read carefully before signing\n• Pay attention to deadlines and obligations\n• Ask questions about anything unclear"
        
        elif doc_type == 'educational':
            return f"📚 **Study Guide**\n\nHere's the key information from this document:\n\n{text}\n\n**Study Tips:**\n• Review these main points\n• Take notes on important concepts\n• Practice with examples"
        
        else:
            return f"📄 **Simplified Version**\n\n{text}\n\n**Key Takeaways:**\n• This document contains important information\n• Review it carefully\n• Ask questions if anything is unclear"
    
    @classmethod
    def _simplify_medium_document(cls, text, doc_type):
        """Simplify a medium-length document"""
        # Extract key sentences (simple approach)
        sentences = re.split(r'[.!?]+', text)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        
        if doc_type == 'legal':
            return f"📄 **Legal Document Simplified**\n\n**What this document is about:**\nThis is a legal document that outlines an agreement between parties.\n\n**Main points:**\n" + "\n".join([f"• {s}" for s in key_sentences]) + "\n\n**What you should know:**\n• This document creates legal obligations\n• Read all terms carefully before signing\n• Consider consulting with someone if unclear\n• Keep a copy for your records"
        
        elif doc_type == 'educational':
            return f"📚 **Educational Content Summary**\n\n**Main concepts covered:**\n" + "\n".join([f"• {s}" for s in key_sentences]) + "\n\n**Learning takeaways:**\n• These are the key concepts to understand\n• Review them until clear\n• Practice applying these concepts"
        
        else:
            return f"📄 **Document Summary**\n\n**Key information from this document:**\n" + "\n".join([f"• {s}" for s in key_sentences]) + "\n\n**Summary:**\nThis document contains important information. The main points are listed above. If you need clarification on any part, just ask!"
    
    @classmethod
    def _simplify_long_document(cls, text, doc_type):
        """Simplify a long document"""
        # Get first paragraph as intro
        first_para = text.split('\n')[0] if '\n' in text else text[:200]
        
        if doc_type == 'legal':
            return f"📄 **Long Legal Document - Executive Summary**\n\n**Overview:**\n{first_para[:200]}...\n\n**Key Sections to Review:**\n• Terms and Conditions\n• Rights and Obligations\n• Termination Clauses\n• Liability Provisions\n\n**Recommendation:**\nThis is a lengthy legal document. I've extracted the main sections above. For complete understanding, review the full document or ask me specific questions about parts you don't understand."
        
        elif doc_type == 'educational':
            return f"📚 **Comprehensive Study Material**\n\n**Introduction:**\n{first_para[:200]}...\n\n**What you'll learn:**\nThis document covers multiple topics. The key concepts are explained throughout.\n\n**Study strategy:**\n1. Read section by section\n2. Take notes on important points\n3. Ask me questions about specific parts\n4. Review the summary at the end\n\nFeel free to ask: 'What does this document say about [specific topic]?'"
        
        else:
            return f"📄 **Document Overview**\n\n**Summary:**\n{first_para[:200]}...\n\n**Main sections:**\nThis document contains detailed information on its subject matter.\n\n**How to use this document:**\n• Review the key points\n• Ask me specific questions\n• Download the simplified version\n• Request clarification on any section"
    
    @classmethod
    def ask_about_document(cls, doc_id, question):
        """Answer questions about a specific document"""
        if doc_id not in cls._documents:
            return None
        
        doc = cls._documents[doc_id]
        content = doc['content']
        
        # Simple Q&A based on keyword matching
        question_lower = question.lower()
        
        # Look for specific patterns in the question
        if 'what is' in question_lower or 'what does' in question_lower:
            # Extract keywords
            keywords = re.findall(r'\b\w+\b', question_lower)
            keywords = [k for k in keywords if len(k) > 3 and k not in ['what', 'does', 'this', 'that', 'about']]
            
            # Search for keywords in content
            for keyword in keywords[:3]:
                if keyword in content.lower():
                    # Find sentence containing keyword
                    sentences = re.split(r'[.!?]+', content)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            return f"📖 **About '{keyword}':**\n{sentence.strip()}\n\nIs this helpful? I can explain further!"
            
            return f"I found information about that in the document. The main point is: {content[:300]}...\n\nWould you like me to explain a specific part in more detail?"
        
        elif 'summary' in question_lower or 'overview' in question_lower:
            return f"📋 **Document Summary:**\n{doc['simplified'][:500]}...\n\nYou can download the full simplified version for complete details."
        
        else:
            # General response
            return f"Based on the document '{doc['filename']}':\n\n{content[:400]}...\n\nDoes that answer your question? I can provide more details or focus on a specific section."
    
    @classmethod
    def get_document_info(cls, doc_id):
        """Get information about a document"""
        if doc_id in cls._documents:
            doc = cls._documents[doc_id]
            return {
                'filename': doc['filename'],
                'created_at': doc['created_at'].isoformat(),
                'original_length': doc['original_length'],
                'simplified_length': len(doc['simplified'])
            }
        return None