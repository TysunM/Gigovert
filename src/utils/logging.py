import logging
import os
import json
from datetime import datetime
from flask import request, g
import traceback

# Create logs directory
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ConversionLogger:
    def __init__(self):
        self.conversion_log_file = os.path.join(log_dir, 'conversions.log')
        self.error_log_file = os.path.join(log_dir, 'errors.log')
        self.security_log_file = os.path.join(log_dir, 'security.log')
    
    def log_conversion_start(self, job_id, from_format, to_format, source_type, ip_address):
        """Log when a conversion starts"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'conversion_start',
            'job_id': job_id,
            'from_format': from_format,
            'to_format': to_format,
            'source_type': source_type,
            'ip_address': ip_address,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        with open(self.conversion_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info(f"Conversion started: {job_id} ({from_format} -> {to_format})")
    
    def log_conversion_complete(self, job_id, duration, file_size=None):
        """Log when a conversion completes"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'conversion_complete',
            'job_id': job_id,
            'duration_seconds': duration,
            'output_file_size': file_size
        }
        
        with open(self.conversion_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info(f"Conversion completed: {job_id} in {duration:.2f}s")
    
    def log_conversion_error(self, job_id, error_message, error_type=None):
        """Log conversion errors"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'conversion_error',
            'job_id': job_id,
            'error_message': error_message,
            'error_type': error_type,
            'traceback': traceback.format_exc()
        }
        
        with open(self.error_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.error(f"Conversion failed: {job_id} - {error_message}")
    
    def log_security_event(self, event_type, ip_address, details=None):
        """Log security-related events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'security_event',
            'event_type': event_type,
            'ip_address': ip_address,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'details': details or {}
        }
        
        with open(self.security_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        logger.warning(f"Security event: {event_type} from {ip_address}")
    
    def log_api_request(self, endpoint, method, status_code, response_time):
        """Log API requests for monitoring"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'api_request',
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time_ms': response_time,
            'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        with open(self.conversion_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

# Global logger instance
conversion_logger = ConversionLogger()

def log_request():
    """Middleware to log all requests"""
    g.start_time = datetime.utcnow()

def log_response(response):
    """Middleware to log response details"""
    if hasattr(g, 'start_time'):
        duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000
        conversion_logger.log_api_request(
            endpoint=request.endpoint or request.path,
            method=request.method,
            status_code=response.status_code,
            response_time=duration
        )
    return response

class HealthMonitor:
    def __init__(self):
        self.stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_requests': 0,
            'start_time': datetime.utcnow()
        }
    
    def increment_conversion(self, success=True):
        """Increment conversion counters"""
        self.stats['total_conversions'] += 1
        if success:
            self.stats['successful_conversions'] += 1
        else:
            self.stats['failed_conversions'] += 1
    
    def increment_requests(self):
        """Increment request counter"""
        self.stats['total_requests'] += 1
    
    def get_health_status(self):
        """Get current health status"""
        uptime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        success_rate = 0
        
        if self.stats['total_conversions'] > 0:
            success_rate = (self.stats['successful_conversions'] / self.stats['total_conversions']) * 100
        
        return {
            'status': 'healthy',
            'uptime_seconds': uptime,
            'total_conversions': self.stats['total_conversions'],
            'successful_conversions': self.stats['successful_conversions'],
            'failed_conversions': self.stats['failed_conversions'],
            'success_rate_percent': round(success_rate, 2),
            'total_requests': self.stats['total_requests']
        }

# Global health monitor instance
health_monitor = HealthMonitor()
