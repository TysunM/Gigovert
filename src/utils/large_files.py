"""
Configuration for handling large files (up to 40GB)
"""

# File size limits
MAX_FILE_SIZE = 40 * 1024 * 1024 * 1024  # 40GB
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for streaming
UPLOAD_BUFFER_SIZE = 1024 * 1024  # 1MB buffer

# Timeout settings for large file operations
LARGE_FILE_UPLOAD_TIMEOUT = 3600  # 1 hour
LARGE_FILE_CONVERSION_TIMEOUT = 7200  # 2 hours
YOUTUBE_DOWNLOAD_TIMEOUT = 3600  # 1 hour

# Storage settings
TEMP_DIR_SIZE_LIMIT = 100 * 1024 * 1024 * 1024  # 100GB temp space
CLEANUP_INTERVAL = 3600  # Clean up temp files every hour

# FFmpeg settings for large files
FFMPEG_THREAD_COUNT = 0  # Use all available cores
FFMPEG_PRESET = 'medium'  # Balance between speed and quality
FFMPEG_CRF = 23  # Constant Rate Factor for video quality

# Progress reporting
PROGRESS_UPDATE_INTERVAL = 5  # Update progress every 5 seconds

# Memory management
MAX_MEMORY_USAGE = 2 * 1024 * 1024 * 1024  # 2GB max memory per process
ENABLE_MEMORY_MONITORING = True

# Disk space monitoring
MIN_FREE_DISK_SPACE = 50 * 1024 * 1024 * 1024  # 50GB minimum free space
DISK_SPACE_CHECK_INTERVAL = 300  # Check every 5 minutes

# Rate limiting for large files
LARGE_FILE_RATE_LIMIT = 1  # 1 large file upload per minute per IP
CONCURRENT_CONVERSIONS_LIMIT = 3  # Max 3 concurrent large file conversions

# Supported formats for large files
LARGE_FILE_FORMATS = {
    'video': ['mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv', 'webm'],
    'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'],
    'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
    'image': ['jpg', 'jpeg', 'png', 'tiff', 'bmp', 'webp']
}

# Quality presets for different file sizes
QUALITY_PRESETS = {
    'small': {  # < 1GB
        'video_crf': 20,
        'audio_bitrate': '320k',
        'preset': 'fast'
    },
    'medium': {  # 1GB - 10GB
        'video_crf': 23,
        'audio_bitrate': '256k',
        'preset': 'medium'
    },
    'large': {  # > 10GB
        'video_crf': 25,
        'audio_bitrate': '192k',
        'preset': 'slow'
    }
}

def get_quality_preset(file_size_bytes):
    """Get appropriate quality preset based on file size"""
    if file_size_bytes < 1024 * 1024 * 1024:  # < 1GB
        return QUALITY_PRESETS['small']
    elif file_size_bytes < 10 * 1024 * 1024 * 1024:  # < 10GB
        return QUALITY_PRESETS['medium']
    else:
        return QUALITY_PRESETS['large']
