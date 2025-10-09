from flask import Blueprint, request, jsonify, send_file
import os
from src.models.job import Job, db
from src.services.conversion_service import ConversionService
from src.utils.validators import validate_conversion, sanitize_filename
from src.utils.large_file_handler import LargeFileHandler

conversion_bp = Blueprint('conversion', __name__)

# Initialize large file handler
upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
large_file_handler = LargeFileHandler(upload_dir)

@conversion_bp.route('/convert', methods=['POST'])
def convert_file():
    """Start a file conversion job"""
    try:
        # Get conversion parameters
        from_format = request.form.get('from')
        to_format = request.form.get('to')
        source = request.form.get('source')  # 'upload' or 'youtube'
        
        if not from_format or not to_format or not source:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Validate conversion
        conversion_map = {
            'youtube': ['wav', 'mp3', 'aiff', 'mp4', 'flac'],
            'mp3': ['flac', 'wav'],
            'wav': ['mp3', 'flac', 'ogg', 'aiff'],
            'flac': ['mp3', 'wav', 'ogg', 'aiff'],
            'rar': ['iso', 'zip'],
            'iso': ['rar', 'zip'],
            'png': ['jpg'],
            'jpg': ['png'],
            'mp4': ['mov'],
            'mov': ['mp4']
        }
        
        if not validate_conversion(from_format, to_format, conversion_map):
            return jsonify({'error': 'Unsupported conversion'}), 400
        
        # Create job
        job = Job(from_format=from_format, to_format=to_format)
        
        if source == 'youtube':
            url = request.form.get('url')
            if not url:
                return jsonify({'error': 'YouTube URL required'}), 400
            job.source_url = url
        elif source == 'upload':
            if 'file' not in request.files:
                return jsonify({'error': 'File required'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)
            
            # Save file
            file_path = large_file_handler.save_large_file(file, safe_filename)
            job.source_file_path = file_path
        
        # Save job to database
        db.session.add(job)
        db.session.commit()
        
        # Queue conversion job
        from flask import current_app
        conversion_service = ConversionService(current_app._get_current_object())
        conversion_service.queue_conversion(job.job_id)
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@conversion_bp.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a conversion job"""
    try:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'progress': job.progress,
            'error_message': job.error_message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@conversion_bp.route('/download/<job_id>', methods=['GET'])
def download_file(job_id):
    """Download the converted file"""
    try:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'completed':
            return jsonify({'error': 'Job not completed'}), 400
        
        if not job.converted_file_path or not os.path.exists(job.converted_file_path):
            return jsonify({'error': 'Converted file not found'}), 404
        
        return send_file(
            job.converted_file_path,
            as_attachment=True,
            download_name=f'converted.{job.to_format}'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
