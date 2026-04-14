"""JAI - Text Formatter Module
Converts markdown-style formatting to HTML for display.
Handles bold, italic, code blocks, and lists.
"""

import re


class TextFormatter:
    """Format text with markdown-style syntax to HTML"""
    
    @staticmethod
    def format_bold(text):
        """Convert **text** to <strong>text</strong>"""
        # Pattern for **bold** (non-greedy, not overlapping)
        pattern = r'\*\*(.+?)\*\*'
        return re.sub(pattern, r'<strong>\1</strong>', text)
    
    @staticmethod
    def format_italic(text):
        """Convert *text* to <em>text</em> (but not **bold**)"""
        # First protect bold patterns, then convert italic
        # Temporarily replace bold with placeholder
        bold_placeholders = []
        def replace_bold(match):
            bold_placeholders.append(match.group(0))
            return f'%%BOLD{len(bold_placeholders)-1}%%'
        
        # Replace bold with placeholders
        temp = re.sub(r'\*\*(.+?)\*\*', replace_bold, text)
        
        # Convert italic (*text*)
        temp = re.sub(r'\*(.+?)\*', r'<em>\1</em>', temp)
        
        # Restore bold
        for i, bold in enumerate(bold_placeholders):
            # Convert the original bold to strong
            bold_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', bold)
            temp = temp.replace(f'%%BOLD{i}%%', bold_html)
        
        return temp
    
    @staticmethod
    def format_code_blocks(text):
        """Convert ```code``` to <pre><code>code</code></pre>"""
        pattern = r'```(\w*)\n(.*?)```'
        return re.sub(pattern, r'<pre><code class="language-\1">\2</code></pre>', text, flags=re.DOTALL)
    
    @staticmethod
    def format_inline_code(text):
        """Convert `code` to <code>code</code>"""
        # Protect code blocks first
        code_block_placeholders = []
        def replace_code_block(match):
            code_block_placeholders.append(match.group(0))
            return f'%%CODEBLOCK{len(code_block_placeholders)-1}%%'
        
        temp = re.sub(r'```(\w*)\n.*?```', replace_code_block, text, flags=re.DOTALL)
        
        # Convert inline code
        temp = re.sub(r'`([^`]+?)`', r'<code>\1</code>', temp)
        
        # Restore code blocks
        for i, block in enumerate(code_block_placeholders):
            block_html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', block, flags=re.DOTALL)
            temp = temp.replace(f'%%CODEBLOCK{i}%%', block_html)
        
        return temp
    
    @staticmethod
    def format_lists(text):
        """Convert markdown lists to HTML lists"""
        # Unordered lists (- item or * item)
        lines = text.split('\n')
        in_list = False
        result = []
        list_items = []
        
        for line in lines:
            # Check for list item
            list_match = re.match(r'^[\s]*[-*]\s+(.+)$', line)
            if list_match:
                if not in_list:
                    in_list = True
                    list_items = []
                list_items.append(list_match.group(1))
            else:
                if in_list:
                    # Close the list
                    result.append('<ul>')
                    for item in list_items:
                        result.append(f'<li>{item}</li>')
                    result.append('</ul>')
                    in_list = False
                    list_items = []
                result.append(line)
        
        # Handle list at the end
        if in_list:
            result.append('<ul>')
            for item in list_items:
                result.append(f'<li>{item}</li>')
            result.append('</ul>')
        
        return '\n'.join(result)
    
    @staticmethod
    def format_line_breaks(text):
        """Convert newlines to <br> tags"""
        # Don't convert inside code blocks
        code_block_placeholders = []
        def replace_code_block(match):
            code_block_placeholders.append(match.group(0))
            return f'%%CODEBLOCK{len(code_block_placeholders)-1}%%'
        
        temp = re.sub(r'<pre><code.*?>.*?</code></pre>', replace_code_block, text, flags=re.DOTALL)
        
        # Convert double newlines to paragraph breaks
        temp = re.sub(r'\n\n+', '</p><p>', temp)
        # Convert single newlines to <br>
        temp = re.sub(r'\n', '<br>', temp)
        
        # Wrap in paragraph tags if not already
        if not temp.startswith('<p>'):
            temp = f'<p>{temp}</p>'
        
        # Restore code blocks
        for i, block in enumerate(code_block_placeholders):
            temp = temp.replace(f'%%CODEBLOCK{i}%%', block)
        
        return temp
    
    @staticmethod
    def format_all(text):
        """Apply all formatting to text"""
        if not text:
            return text
        
        # Apply formatting in order
        text = TextFormatter.format_bold(text)
        text = TextFormatter.format_italic(text)
        text = TextFormatter.format_code_blocks(text)
        text = TextFormatter.format_inline_code(text)
        text = TextFormatter.format_lists(text)
        
        return text
    
    @staticmethod
    def to_html(text):
        """Convert markdown text to HTML"""
        return TextFormatter.format_all(text)
    
    @staticmethod
    def strip_formatting(text):
        """Remove all markdown formatting, return plain text"""
        if not text:
            return text
        
        # Remove bold
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        # Remove italic
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`([^`]+?)`', r'\1', text)
        
        return text.strip()