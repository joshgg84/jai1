"""JAI - Image Intelligence Module
Integrates core image handling with optional OCR capabilities.
"""

import logging
from jai_image_core import ImageCore, ImageCommandHandler
from jai_image_ocr import ImageOCR

logger = logging.getLogger(__name__)


class ImageHandler:
    """Main image handler integrating core and OCR features"""
    
    @staticmethod
    def process_upload(message, client_id):
        """Process image upload with optional OCR"""
        # Extract text using OCR if available
        extracted_text = None
        if ImageOCR.is_ocr_available():
            try:
                parts = message.split(':', 2)
                if len(parts) >= 3:
                    base64_content = parts[2].strip()
                    extracted_text = ImageOCR.extract_text_from_image(base64_content)
                    if extracted_text:
                        logger.info(f"OCR extracted {len(extracted_text)} characters")
            except Exception as e:
                logger.warning(f"OCR extraction failed: {e}")
        
        # Process upload with extracted text
        return ImageCommandHandler.process_upload(message, client_id, extracted_text)
    
    @staticmethod
    def has_image(client_id):
        """Check if user has an image"""
        return ImageCore.has_image(client_id)
    
    @staticmethod
    def get_user_image(client_id):
        """Get user's image data"""
        return ImageCore.get_user_image(client_id)
    
    @staticmethod
    def clear_image(client_id):
        """Clear user's image"""
        return ImageCore.clear_image(client_id)
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer questions about the image (with OCR support)"""
        image_data = ImageCore.get_user_image(client_id)
        
        if not image_data:
            return "🖼️ No image loaded. Please upload an image first."
        
        # Try OCR-specific questions first if OCR is available
        if ImageOCR.is_ocr_available():
            ocr_answer = ImageOCR.answer_ocr_question(client_id, question, image_data, ImageCore)
            if ocr_answer:
                return ocr_answer
        
        # Fall back to core image questions
        return ImageCore.answer_question(client_id, question)
    
    @staticmethod
    def generate_simplified_description(info, description):
        """Generate simplified description"""
        return ImageCore.generate_simplified_description(info, description)