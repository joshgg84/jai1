"""JAI - Image Core Module
Core image handling without OCR dependencies.
Handles image upload, basic analysis, and Q&A.
"""

import base64
import re
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

# Store images per user (client_id)
_user_images = {}

# Try to import PIL for basic image info (optional - works without it)
try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
    logger.info("PIL available for image dimensions")
except ImportError:
    PIL_AVAILABLE = False
    logger.info("PIL not available - using basic image info")


class ImageCore:
    """Core image handling without OCR"""
    
    @staticmethod
    def extract_image_info(base64_content, filename):
        """Extract basic info from base64 encoded image"""
        try:
            file_content = base64.b64decode(base64_content)
            file_ext = filename.split('.')[-1].lower()
            
            logger.info(f"Processing image: {filename}, size: {len(file_content)} bytes")
            
            info = {
                'filename': filename,
                'size': len(file_content),
                'type': file_ext,
                'base64_preview': base64_content[:500],
                'uploaded_at': datetime.now()
            }
            
            # Try to get image dimensions if PIL is available
            if PIL_AVAILABLE:
                try:
                    img = Image.open(io.BytesIO(file_content))
                    info['width'] = img.width
                    info['height'] = img.height
                    info['mode'] = img.mode
                    info['aspect_ratio'] = round(img.width / img.height, 2)
                    logger.info(f"Image dimensions: {img.width}x{img.height}")
                except Exception as e:
                    logger.warning(f"Could not read image dimensions: {e}")
                    info['width'] = 0
                    info['height'] = 0
                    info['aspect_ratio'] = 0
            else:
                info['width'] = 0
                info['height'] = 0
                info['aspect_ratio'] = 0
            
            return info
        except Exception as e:
            logger.error(f"Error extracting image info: {e}")
            return None
    
    @staticmethod
    def analyze_image(base64_content, filename):
        """Analyze image and generate description using local pattern recognition"""
        
        filename_lower = filename.lower()
        
        # Build description based on multiple factors
        description_parts = []
        
        # 1. Filename-based detection
        filename_indicators = ImageCore._detect_from_filename(filename_lower)
        if filename_indicators:
            description_parts.append(filename_indicators)
        
        # 2. Size-based detection
        file_content = base64.b64decode(base64_content)
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > 5:
            description_parts.append(f"📦 Large image ({size_mb:.1f} MB)")
        elif size_mb > 1:
            description_parts.append(f"📦 Medium image ({size_mb:.1f} MB)")
        else:
            description_parts.append(f"📦 Small image ({size_mb * 1024:.0f} KB)")
        
        # 3. Try to detect content from base64 patterns
        content_type = ImageCore._detect_content_from_base64(base64_content[:500])
        if content_type:
            description_parts.append(content_type)
        
        # 4. Color analysis if PIL available
        if PIL_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(file_content))
                colors = ImageCore._analyze_colors(img)
                if colors:
                    description_parts.append(colors)
            except:
                pass
        
        # Build final description
        if description_parts:
            description = "🖼️ **Image Analysis:**\n\n" + "\n\n".join(description_parts)
        else:
            description = "🖼️ **Image uploaded** - I can see this image. Tell me what you'd like to know about it!"
        
        # Add helpful prompt
        description += "\n\n💡 **You can ask:** 'Describe this image', 'What format is it?', 'What are the dimensions?'"
        
        return description
    
    @staticmethod
    def _detect_from_filename(filename_lower):
        """Detect image type from filename patterns"""
        
        patterns = {
            'screenshot': "📸 **Screenshot** - Shows a screen capture, likely of an app, website, or conversation",
            'photo': "📷 **Photo** - A photographic image",
            'selfie': "🤳 **Selfie** - A self-portrait photo",
            'portrait': "👤 **Portrait** - A person's portrait",
            'logo': "🏷️ **Logo** - A brand or company logo",
            'icon': "🔘 **Icon** - A small icon or symbol",
            'diagram': "📊 **Diagram** - Shows relationships or processes",
            'chart': "📈 **Chart/Graph** - Shows data visualization",
            'graph': "📉 **Graph** - Shows plotted data",
            'meme': "😂 **Meme** - A humorous internet image",
            'code': "💻 **Code Screenshot** - Shows programming code",
            'coding': "💻 **Code Screenshot** - Shows programming code",
            'wallpaper': "🎨 **Wallpaper** - A background image",
            'art': "🎭 **Artwork** - Artistic or creative image",
            'drawing': "✏️ **Drawing** - Hand-drawn or digital illustration",
            'sketch': "✏️ **Sketch** - A rough drawing",
            'infographic': "📊 **Infographic** - Information with graphics",
            'document': "📄 **Document Scan** - Appears to be a scanned document",
            'receipt': "🧾 **Receipt** - A purchase receipt",
            'letter': "✉️ **Letter** - A written letter",
            'note': "📝 **Note** - Handwritten or typed note"
        }
        
        for key, description in patterns.items():
            if key in filename_lower:
                return description
        
        return None
    
    @staticmethod
    def _detect_content_from_base64(base64_preview):
        """Try to detect content type from base64 patterns"""
        
        try:
            if 'iVBORw0KGgo' in base64_preview:
                return "🖼️ **PNG Format** - Portable Network Graphics"
            elif '/9j/' in base64_preview:
                return "🖼️ **JPEG Format** - Common photo format"
            elif 'R0lGOD' in base64_preview:
                return "🖼️ **GIF Format** - May be animated"
            elif 'UklGR' in base64_preview:
                return "🖼️ **WebP Format** - Modern web format"
        except:
            pass
        
        return None
    
    @staticmethod
    def _analyze_colors(img):
        """Analyze dominant colors in image (simplified)"""
        try:
            img_small = img.copy()
            img_small.thumbnail((100, 100))
            
            colors = img_small.getcolors(maxcolors=1000)
            if colors:
                colors.sort(reverse=True)
                top_colors = colors[:3]
                
                color_names = []
                for count, rgb in top_colors:
                    if isinstance(rgb, tuple):
                        r, g, b = rgb[:3]
                        if r > 200 and g > 200 and b > 200:
                            color_names.append("white/light")
                        elif r < 50 and g < 50 and b < 50:
                            color_names.append("black/dark")
                        elif r > 200 and g < 100 and b < 100:
                            color_names.append("reddish")
                        elif r < 100 and g > 200 and b < 100:
                            color_names.append("greenish")
                        elif r < 100 and g < 100 and b > 200:
                            color_names.append("bluish")
                        elif r > 200 and g > 200 and b < 100:
                            color_names.append("yellowish")
                        else:
                            color_names.append("colorful")
                
                if color_names:
                    unique_colors = list(dict.fromkeys(color_names))
                    return f"🎨 **Colors:** {', '.join(unique_colors[:2])} tones"
        except:
            pass
        
        return None
    
    @staticmethod
    def store_image(client_id, filename, info, description):
        """Store image info for a user"""
        _user_images[client_id] = {
            'filename': filename,
            'info': info,
            'description': description,
            'created_at': datetime.now()
        }
        return True
    
    @staticmethod
    def get_user_image(client_id):
        """Get user's image info"""
        return _user_images.get(client_id)
    
    @staticmethod
    def has_image(client_id):
        """Check if user has an image loaded"""
        return client_id in _user_images
    
    @staticmethod
    def clear_image(client_id):
        """Clear user's image"""
        if client_id in _user_images:
            del _user_images[client_id]
            return True
        return False
    
    @staticmethod
    def update_extracted_text(client_id, extracted_text):
        """Update image with extracted text (used by OCR module)"""
        if client_id in _user_images:
            _user_images[client_id]['info']['extracted_text'] = extracted_text
            return True
        return False
    
    @staticmethod
    def answer_question(client_id, question):
        """Answer questions about the uploaded image"""
        image_data = ImageCore.get_user_image(client_id)
        
        if not image_data:
            return "🖼️ No image loaded. Please upload an image first."
        
        filename = image_data['filename']
        description = image_data['description']
        info = image_data['info']
        
        question_lower = question.lower().strip()
        
        # ========== DESCRIPTION QUESTIONS ==========
        if any(word in question_lower for word in ['what is this', 'describe', 'what do you see', 'tell me about', 'what\'s in', 'explain this image']):
            response = f"🖼️ **About '{filename}':**\n\n{description}\n\n"
            if info.get('width') and info.get('height'):
                response += f"📊 **Details:** {info['width']}x{info['height']}px, {info.get('type', 'unknown').upper()}\n"
            if info.get('extracted_text'):
                response += f"📝 **Contains text:** Yes ({len(info['extracted_text'])} characters). Ask me to 'read the text'.\n"
            response += f"\n💡 What else would you like to know?"
            return response
        
        # ========== FORMAT QUESTIONS ==========
        if any(word in question_lower for word in ['format', 'type', 'extension', 'file type', 'what format']):
            response = f"📁 **File format:** {info.get('type', 'unknown').upper()}\n"
            response += f"📏 **File size:** {info.get('size', 0) / 1024:.2f} KB\n\n"
            if info.get('extracted_text'):
                response += f"📝 **Text detected:** Yes\n"
            return response
        
        # ========== DIMENSION QUESTIONS ==========
        if any(word in question_lower for word in ['dimensions', 'resolution', 'width', 'height', 'pixels', 'how big', 'size in pixels']):
            if info.get('width') and info.get('height'):
                return f"📐 **Dimensions:** {info['width']} x {info['height']} pixels\n" \
                       f"📏 **Aspect ratio:** {info.get('aspect_ratio', '?')}:1\n\n" \
                       f"💡 Total pixels: {info['width'] * info['height']:,}"
            else:
                return f"📐 Could not detect exact dimensions. The image is {info.get('size', 0) / 1024:.2f} KB in size."
        
        # ========== FILE SIZE QUESTIONS ==========
        if any(word in question_lower for word in ['file size', 'how many kb', 'how many mb', 'storage', 'memory']):
            size_kb = info.get('size', 0) / 1024
            if size_kb > 1024:
                return f"💾 **File size:** {size_kb / 1024:.2f} MB ({size_kb:.0f} KB)"
            else:
                return f"💾 **File size:** {size_kb:.2f} KB ({info.get('size', 0):,} bytes)"
        
        # ========== WHAT CAN I ASK ==========
        if any(word in question_lower for word in ['what can i ask', 'help', 'questions', 'what questions']):
            response = f"💡 **You can ask me about this image:**\n\n" \
                   f"• 'What is this image?'\n" \
                   f"• 'Describe this image'\n" \
                   f"• 'What format is this?'\n" \
                   f"• 'What are the dimensions?'\n" \
                   f"• 'How big is this file?'\n"
            if info.get('extracted_text'):
                response += f"• 'Read the text in this image' (OCR)\n"
                response += f"• 'Summarize the text in this image'\n"
            response += f"\nTry asking something specific!"
            return response
        
        # ========== DEFAULT RESPONSE ==========
        response = f"🖼️ **Image: {filename}**\n\n{description}\n\n"
        if info.get('extracted_text'):
            response += f"📝 **This image contains text.** Ask me to 'read the text' or 'summarize the text'!\n\n"
        response += f"💡 **Try asking:**\n" \
               f"• 'Describe this image'\n" \
               f"• 'What format is this?'\n" \
               f"• 'What are the dimensions?'"
        return response
    
    @staticmethod
    def generate_simplified_description(info, description):
        """Generate a simplified version for display"""
        simplified = f"📷 **Image Analysis**\n\n"
        simplified += f"📄 **File:** {info['filename']}\n"
        simplified += f"📏 **Size:** {info['size'] / 1024:.2f} KB\n"
        simplified += f"🔤 **Type:** {info.get('type', 'unknown').upper()}\n"
        
        if info.get('width') and info.get('height'):
            simplified += f"📐 **Dimensions:** {info['width']} x {info['height']} pixels\n"
            simplified += f"📊 **Aspect Ratio:** {info.get('aspect_ratio', '?')}:1\n"
        
        if info.get('extracted_text'):
            text_preview = info['extracted_text'][:200] + "..." if len(info['extracted_text']) > 200 else info['extracted_text']
            simplified += f"\n📝 **Text detected:**\n{text_preview}\n"
        
        simplified += f"\n**Description:**\n{description}\n\n"
        simplified += f"💡 **Ask me questions about this image!**"
        
        return simplified


# ========== IMAGE COMMAND HANDLER ==========
class ImageCommandHandler:
    """Handle image-related commands from frontend"""
    
    @staticmethod
    def process_upload(message, client_id, extracted_text=None):
        """Process image upload command"""
        try:
            # Format: upload_img: filename : base64content
            parts = message.split(':', 2)
            if len(parts) >= 3:
                filename = parts[1].strip()
                base64_content = parts[2].strip()
                
                # Extract image info
                info = ImageCore.extract_image_info(base64_content, filename)
                if not info:
                    return "❌ Could not process image. Please check the file and try again."
                
                # Add extracted text if provided
                if extracted_text:
                    info['extracted_text'] = extracted_text
                
                # Analyze image
                description = ImageCore.analyze_image(base64_content, filename)
                
                # Store image
                ImageCore.store_image(client_id, filename, info, description)
                
                # Generate simplified display
                simplified = ImageCore.generate_simplified_description(info, description)
                
                # Add OCR status message
                if extracted_text:
                    return f"✅ **Image uploaded!**\n\n{simplified}\n\n📝 **Text detected!** Ask me to 'read the text' or 'summarize the text'.\n\n💡 **Now ask me questions about this image!**"
                else:
                    return f"✅ **Image uploaded!**\n\n{simplified}\n\n💡 **Now ask me questions about this image!**"
            else:
                return "❌ Invalid upload format. Please use the upload button."
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return f"❌ Error: {str(e)}"
    
    @staticmethod
    def is_image_command(message):
        """Check if message is an image command"""
        return message.lower().startswith('upload_img:')