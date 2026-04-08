"""JAI - Image OCR Module
Optional OCR extension for reading text from images.
Requires pytesseract and Tesseract engine.
"""

import base64
import logging
import tempfile
import os
import re

logger = logging.getLogger(__name__)

# Try to import pytesseract for OCR
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR available")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.info("Tesseract not available. Install: pip install pytesseract")


class ImageOCR:
    """OCR capabilities for image text extraction"""
    
    @staticmethod
    def extract_text_from_image(base64_content):
        """Extract text from image using Tesseract OCR"""
        if not TESSERACT_AVAILABLE:
            return None
        
        try:
            # Decode base64 to image
            file_content = base64.b64decode(base64_content)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            # Run OCR
            extracted_text = pytesseract.image_to_string(tmp_path)
            
            # Clean up
            os.unlink(tmp_path)
            
            if extracted_text and len(extracted_text.strip()) > 0:
                return extracted_text.strip()
            return None
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return None
    
    @staticmethod
    def is_ocr_available():
        """Check if OCR is available"""
        return TESSERACT_AVAILABLE
    
    @staticmethod
    def answer_ocr_question(client_id, question, image_data, image_core):
        """Handle OCR-specific questions"""
        if not image_data:
            return None
        
        info = image_data.get('info', {})
        question_lower = question.lower().strip()
        
        # ========== OCR / TEXT READING QUESTIONS ==========
        if any(word in question_lower for word in ['read text', 'extract text', 'what does it say', 'ocr', 'text in image', 'words in image', 'read the text']):
            if info.get('extracted_text'):
                text = info['extracted_text']
                if len(text) > 1000:
                    text = text[:1000] + "...\n\n(Text truncated, first 1000 characters shown)"
                return f"📝 **Text extracted from image:**\n\n```\n{text}\n```\n\n💡 You can ask me to summarize this text or answer questions about it."
            else:
                if TESSERACT_AVAILABLE:
                    return "📝 No text was detected in this image. Try an image with clearer text, better lighting, or higher contrast."
                else:
                    return "📝 OCR (text reading) is not available. Install pytesseract and Tesseract to enable text extraction from images."
        
        # ========== SUMMARIZE TEXT IN IMAGE ==========
        if any(word in question_lower for word in ['summarize text', 'summary of text', 'what does the text say']):
            if info.get('extracted_text'):
                text = info['extracted_text']
                # Simple summarization - take first few sentences
                sentences = re.split(r'[.!?\n]+', text)
                summary_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
                summary = ". ".join(summary_sentences)
                if summary:
                    return f"📝 **Summary of text in image:**\n\n{summary}...\n\n💡 Ask me to 'read the full text' if you need more."
                else:
                    return f"📝 The text in this image is:\n\n{text[:300]}..."
            else:
                return "📝 No text was found in this image to summarize."
        
        # ========== ANSWER QUESTIONS ABOUT EXTRACTED TEXT ==========
        if info.get('extracted_text') and len(question_lower) > 5:
            text = info['extracted_text']
            text_lower = text.lower()
            
            # Check if question contains keywords from the text
            keywords = re.findall(r'\b[a-z]{4,}\b', question_lower)
            for keyword in keywords[:3]:
                if keyword in text_lower:
                    # Find the sentence containing the keyword
                    sentences = re.split(r'[.!?\n]+', text)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            return f"📝 **From the text in your image:**\n\n\"{sentence.strip()}\"\n\n💡 Ask me to 'read all text' for the full content."
        
        return None