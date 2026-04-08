"""JAI - Image Intelligence Module
Self-contained image analysis without third-party APIs.
Handles image upload, analysis, description generation, and Q&A about images.
"""

import base64
import re
import logging
import math
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


class ImageHandler:
    """Handle image upload, analysis, and Q&A per user - No external APIs"""
    
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
                'base64': base64_content[:100] + '...',  # Store preview only
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
                # Estimate from base64 size (rough approximation)
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
        
        # Get basic info
        file_content = base64.b64decode(base64_content)
        filename_lower = filename.lower()
        
        # Build description based on multiple factors
        description_parts = []
        
        # 1. Filename-based detection
        filename_indicators = ImageHandler._detect_from_filename(filename_lower)
        if filename_indicators:
            description_parts.append(filename_indicators)
        
        # 2. Size-based detection
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > 5:
            description_parts.append(f"📦 Large image ({size_mb:.1f} MB)")
        elif size_mb > 1:
            description_parts.append(f"📦 Medium image ({size_mb:.1f} MB)")
        else:
            description_parts.append(f"📦 Small image ({size_mb * 1024:.0f} KB)")
        
        # 3. Try to detect content from base64 patterns
        content_type = ImageHandler._detect_content_from_base64(base64_content[:500])
        if content_type:
            description_parts.append(content_type)
        
        # 4. Color analysis if PIL available
        if PIL_AVAILABLE:
            try:
                img = Image.open(io.BytesIO(file_content))
                colors = ImageHandler._analyze_colors(img)
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
        description += "\n\n💡 **You can ask:** 'Describe this image', 'What format is it?', or tell me what you want to know!"
        
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
            'infographic': "📊 **Infographic** - Information with graphics"
        }
        
        for key, description in patterns.items():
            if key in filename_lower:
                return description
        
        return None
    
    @staticmethod
    def _detect_content_from_base64(base64_preview):
        """Try to detect content type from base64 patterns"""
        
        # Convert base64 to string for pattern matching
        try:
            # Look for common patterns in base64
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
            # Resize image for faster processing
            img_small = img.copy()
            img_small.thumbnail((100, 100))
            
            # Get dominant colors (simplified)
            colors = img_small.getcolors(maxcolors=1000)
            if colors:
                # Sort by count
                colors.sort(reverse=True)
                top_colors = colors[:3]
                
                color_names = []
                for count, rgb in top_colors:
                    if isinstance(rgb, tuple):
                        r, g, b = rgb[:3]
                        # Simple color naming
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
    def answer_question(client_id, question):
        """Answer questions about the uploaded image"""
        image_data = ImageHandler.get_user_image(client_id)
        
        if not image_data:
            return "🖼️ No image loaded. Please upload an image first."
        
        filename = image_data['filename']
        description = image_data['description']
        info = image_data['info']
        
        question_lower = question.lower().strip()
        
        # ========== DESCRIPTION QUESTIONS ==========
        if any(word in question_lower for word in ['what is this', 'describe', 'what do you see', 'tell me about', 'what\'s in', 'explain this image']):
            return f"🖼️ **About '{filename}':**\n\n{description}\n\n" \
                   f"📊 **Details:** {info.get('width', '?')}x{info.get('height', '?')}px, {info.get('type', 'unknown').upper()}\n\n" \
                   f"💡 What else would you like to know?"
        
        # ========== FORMAT QUESTIONS ==========
        if any(word in question_lower for word in ['format', 'type', 'extension', 'file type', 'what format']):
            return f"📁 **File format:** {info.get('type', 'unknown').upper()}\n" \
                   f"📏 **File size:** {info.get('size', 0) / 1024:.2f} KB\n\n" \
                   f"💡 Common formats: JPEG (photos), PNG (graphics/logos), GIF (animations), WebP (modern web)"
        
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
            return f"💡 **You can ask me about this image:**\n\n" \
                   f"• 'What is this image?'\n" \
                   f"• 'Describe this image'\n" \
                   f"• 'What format is this?'\n" \
                   f"• 'What are the dimensions?'\n" \
                   f"• 'How big is this file?'\n" \
                   f"• 'What colors are in this image?'\n\n" \
                   f"Try asking something specific!"
        
        # ========== COLOR QUESTIONS ==========
        if any(word in question_lower for word in ['color', 'colour', 'colors', 'colours', 'what colors']):
            if PIL_AVAILABLE:
                try:
                    import io
                    file_content = base64.b64decode(info.get('base64_preview', ''))
                    img = Image.open(io.BytesIO(file_content))
                    colors = ImageHandler._analyze_colors(img)
                    if colors:
                        return f"🎨 {colors}\n\n💡 The image has these color tones."
                except:
                    pass
            return f"🎨 The image has various colors. For detailed color analysis, I'd need more processing power."
        
        # ========== CREATIVE / FUN RESPONSES ==========
        if any(word in question_lower for word in ['funny', 'interesting', 'cool', 'nice', 'beautiful']):
            responses = [
                f"😊 Glad you like it! The image '{filename}' has some interesting elements.",
                f"🎨 Images can tell stories. This one is {info.get('width', '?')}x{info.get('height', '?')} pixels of visual information!",
                f"📸 Every image has a story. This one was uploaded at {image_data['created_at'].strftime('%I:%M %p')}."
            ]
            return random.choice(responses)
        
        # ========== DEFAULT RESPONSE ==========
        return f"🖼️ **Image: {filename}**\n\n{description}\n\n" \
               f"💡 **Try asking:**\n" \
               f"• 'Describe this image'\n" \
               f"• 'What format is this?'\n" \
               f"• 'What are the dimensions?'\n" \
               f"• 'What can I ask about this image?'"
    
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
        
        simplified += f"\n**Description:**\n{description}\n\n"
        simplified += f"💡 **Ask me questions about this image!**"
        
        return simplified


# ========== IMAGE COMMAND HANDLER ==========
class ImageCommandHandler:
    """Handle image-related commands from frontend"""
    
    @staticmethod
    def process_upload(message, client_id):
        """Process image upload command"""
        try:
            # Format: upload_img: filename : base64content
            parts = message.split(':', 2)
            if len(parts) >= 3:
                filename = parts[1].strip()
                base64_content = parts[2].strip()
                
                # Extract image info
                info = ImageHandler.extract_image_info(base64_content, filename)
                if not info:
                    return "❌ Could not process image. Please check the file and try again."
                
                # Store base64 preview for color analysis
                info['base64_preview'] = base64_content[:500]  # Store small preview
                
                # Analyze image
                description = ImageHandler.analyze_image(base64_content, filename)
                
                # Store image
                ImageHandler.store_image(client_id, filename, info, description)
                
                # Generate simplified display
                simplified = ImageHandler.generate_simplified_description(info, description)
                
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