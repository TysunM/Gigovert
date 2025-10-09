from functools import wraps
from flask import request, jsonify, g
import time
import hashlib
import os
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
    
    def is_rate_limited(self, ip, limit=10, window=60):
        """Check if IP is rate limited (default: 10 requests per minute)"""
        now = time.time()
        
        # Check if IP is temporarily blocked
        if ip in self.blocked_ips:
            if now < self.blocked_ips[ip]:
                return True
            else:
                del self.blocked_ips[ip]
        
        # Clean old requests
        while self.requests[ip] and self.requests[ip][0] < now - window:
            self.requests[ip].popleft()
        
        # Check rate limit
        if len(self.requests[ip]) >= limit:
            # Block IP for 5 minutes
            self.blocked_ips[ip] = now + 300
            return True
        
        # Add current request
        self.requests[ip].append(now)
        return False

rate_limiter = RateLimiter()

def rate_limit(limit=10, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            if rate_limiter.is_rate_limited(ip, limit, window):
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload():
    """Validate file upload security"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' in request.files:
                file = request.files['file']
                
                # Check file size (40GB limit)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > 40 * 1024 * 1024 * 1024:
                    return jsonify({'error': 'File too large. Maximum size is 40GB.'}), 400
                
                # Check for dangerous file extensions
                dangerous_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.jar']
                filename = file.filename.lower()
                
                for ext in dangerous_extensions:
                    if filename.endswith(ext):
                        return jsonify({'error': 'File type not allowed for security reasons.'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def cors_headers():
    """Add CORS headers for security"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add security headers
            if hasattr(response, 'headers'):
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'DENY'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
                response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com"
            
            return response
        return decorated_function
    return decorator
