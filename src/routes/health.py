from flask import Blueprint, jsonify
import os
# import psutil  # Removed for deployment compatibility
from datetime import datetime
from src.utils.logging import health_monitor
from src.models.job import Job, db

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    health_status = {
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'version': '1.0.0',
        'service': 'Universal File Converter'
    }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@health_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get application metrics"""
    try:
        # Get job statistics
        total_jobs = Job.query.count()
        completed_jobs = Job.query.filter_by(status='completed').count()
        failed_jobs = Job.query.filter_by(status='failed').count()
        processing_jobs = Job.query.filter_by(status='processing').count()
        queued_jobs = Job.query.filter_by(status='queued').count()
        
        # Get health monitor stats
        health_stats = health_monitor.get_health_status()
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'jobs': {
                'total': total_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs,
                'processing': processing_jobs,
                'queued': queued_jobs,
                'success_rate_percent': round((completed_jobs / total_jobs * 100) if total_jobs > 0 else 0, 2)
            },
            'application': health_stats
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get metrics: {str(e)}'}), 500

@health_bp.route('/status', methods=['GET'])
def get_status():
    """Get detailed application status"""
    try:
        # Recent job statistics (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        recent_jobs = Job.query.filter(Job.created_at >= yesterday).all()
        recent_completed = len([j for j in recent_jobs if j.status == 'completed'])
        recent_failed = len([j for j in recent_jobs if j.status == 'failed'])
        
        # Format conversion statistics
        format_stats = {}
        for job in recent_jobs:
            conversion = f"{job.from_format} -> {job.to_format}"
            if conversion not in format_stats:
                format_stats[conversion] = {'total': 0, 'completed': 0, 'failed': 0}
            
            format_stats[conversion]['total'] += 1
            if job.status == 'completed':
                format_stats[conversion]['completed'] += 1
            elif job.status == 'failed':
                format_stats[conversion]['failed'] += 1
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'Universal File Converter',
            'version': '1.0.0',
            'uptime_seconds': health_monitor.get_health_status()['uptime_seconds'],
            'recent_activity': {
                'last_24h_jobs': len(recent_jobs),
                'last_24h_completed': recent_completed,
                'last_24h_failed': recent_failed,
                'success_rate_percent': round((recent_completed / len(recent_jobs) * 100) if recent_jobs else 0, 2)
            },
            'popular_conversions': format_stats,
            'current_queue_size': Job.query.filter_by(status='queued').count(),
            'active_conversions': Job.query.filter_by(status='processing').count()
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

@health_bp.route('/logs', methods=['GET'])
def get_recent_logs():
    """Get recent log entries (for debugging)"""
    try:
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log')
        
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'message': 'No log file found'})
        
        # Read last 50 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        return jsonify({
            'logs': [line.strip() for line in recent_lines],
            'total_lines': len(recent_lines),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get logs: {str(e)}'}), 500
