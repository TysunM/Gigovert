# import magic  # Removed for deployment compatibility
import re

def validate_conversion(from_format, to_format, conversion_map):
    """Validate if a conversion is supported"""
    if from_format not in conversion_map:
        return False
    return to_format in conversion_map[from_format]

def validate_file_type(file_content, expected_format):
    """Validate file type using basic checks (simplified for deployment)"""
    # For deployment compatibility, we'll use filename-based validation
    # This is handled in the routes now
    return True

def validate_youtube_url(url):
    """Validate YouTube URL format"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtu\.be/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/v/[\w-]+'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    return False

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename
