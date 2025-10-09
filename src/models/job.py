from datetime import datetime
import uuid
from .user import db

class Job(db.Model):
    __tablename__ = 'jobs'
    
    job_id = db.Column(db.String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_format = db.Column(db.String(10), nullable=False)
    to_format = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='queued')
    progress = db.Column(db.Integer, default=0)
    source_file_path = db.Column(db.String(255))
    converted_file_path = db.Column(db.String(255))
    source_url = db.Column(db.String(500))  # For YouTube URLs
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'from_format': self.from_format,
            'to_format': self.to_format,
            'status': self.status,
            'progress': self.progress,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_status(self, status, progress=None, error_message=None):
        self.status = status
        if progress is not None:
            self.progress = progress
        if error_message is not None:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
