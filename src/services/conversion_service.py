import os
import subprocess
import threading
import time
from src.models.job import Job, db
from src.utils.validators import validate_youtube_url

class ConversionService:
    def __init__(self, app):
        if app is None:
            raise ValueError("Flask app instance is required for ConversionService")
        self.app = app
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def queue_conversion(self, job_id):
        """Queue a conversion job for background processing"""
        # For now, we'll use threading. In production, use Celery or similar
        thread = threading.Thread(target=self._process_conversion, args=(job_id,))
        thread.daemon = True
        thread.start()
    
    def _process_conversion(self, job_id):
        """Process a conversion job"""
        # Run within Flask application context
        with self.app.app_context():
            try:
                job = Job.query.get(job_id)
                if not job:
                    return
                
                job.update_status('processing', 10)
                
                # Handle different source types
                if job.from_format == 'youtube':
                    source_file = self._download_youtube(job)
                else:
                    source_file = job.source_file_path
                
                if not source_file:
                    job.update_status('failed', error_message='Failed to prepare source file')
                    return
                
                job.update_status('processing', 30)
                
                # Perform conversion
                output_file = self._convert_file(source_file, job.from_format, job.to_format, job_id)
                
                if output_file:
                    job.converted_file_path = output_file
                    job.update_status('completed', 100)
                else:
                    job.update_status('failed', error_message='Conversion failed')
                    
            except Exception as e:
                job = Job.query.get(job_id)
                if job:
                    job.update_status('failed', error_message=str(e))
    
    def _download_youtube(self, job):
        """Download video/audio from YouTube"""
        try:
            if not validate_youtube_url(job.source_url):
                raise ValueError('Invalid YouTube URL')
            
            output_path = os.path.join(self.output_dir, f"{job.job_id}_youtube.%(ext)s")
            
            # Use yt-dlp to download
            cmd = ['yt-dlp']
            
            # Add audio extraction options for audio formats
            if job.to_format in ['mp3', 'wav', 'flac', 'aiff']:
                cmd.extend(['--extract-audio', '--audio-format', job.to_format])
            
            # Add output path and URL
            cmd.extend(['--output', output_path, job.source_url])
            
            # Log the command for debugging
            print(f"Running yt-dlp command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            # Log output for debugging
            print(f"yt-dlp stdout: {result.stdout}")
            print(f"yt-dlp stderr: {result.stderr}")
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown yt-dlp error"
                raise Exception(f"yt-dlp failed with code {result.returncode}: {error_msg}")
            
            # Find the downloaded file
            downloaded_files = []
            for file in os.listdir(self.output_dir):
                if file.startswith(f"{job.job_id}_youtube"):
                    downloaded_files.append(file)
            
            if not downloaded_files:
                raise Exception(f"Downloaded file not found. Output directory contents: {os.listdir(self.output_dir)}")
            
            # Return the first matching file
            return os.path.join(self.output_dir, downloaded_files[0])
            
        except subprocess.TimeoutExpired:
            raise Exception("YouTube download timed out after 1 hour")
        except Exception as e:
            raise Exception(f"YouTube download failed: {str(e)}")
    
    def _convert_file(self, source_file, from_format, to_format, job_id):
        """Convert file using appropriate tool"""
        try:
            output_file = os.path.join(self.output_dir, f"{job_id}_converted.{to_format}")
            
            # Audio/Video conversions using FFmpeg
            if self._is_media_conversion(from_format, to_format):
                return self._convert_with_ffmpeg(source_file, output_file, from_format, to_format)
            
            # Image conversions using Pillow
            elif self._is_image_conversion(from_format, to_format):
                return self._convert_image(source_file, output_file, from_format, to_format)
            
            # Archive conversions
            elif self._is_archive_conversion(from_format, to_format):
                return self._convert_archive(source_file, output_file, from_format, to_format)
            
            else:
                raise Exception(f"Unsupported conversion: {from_format} to {to_format}")
                
        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")
    
    def _is_media_conversion(self, from_format, to_format):
        """Check if this is a media (audio/video) conversion"""
        media_formats = ['mp3', 'wav', 'flac', 'ogg', 'aiff', 'mp4', 'mov']
        return from_format in media_formats and to_format in media_formats
    
    def _is_image_conversion(self, from_format, to_format):
        """Check if this is an image conversion"""
        image_formats = ['png', 'jpg', 'jpeg']
        return from_format in image_formats and to_format in image_formats
    
    def _is_archive_conversion(self, from_format, to_format):
        """Check if this is an archive conversion"""
        archive_formats = ['rar', 'zip', 'iso']
        return from_format in archive_formats and to_format in archive_formats
    
    def _convert_with_ffmpeg(self, source_file, output_file, from_format, to_format):
        """Convert media files using FFmpeg with optimizations for large files"""
        try:
            cmd = ['ffmpeg', '-i', source_file, '-y']
            
            # Add specific options for different formats
            if to_format == 'mp3':
                cmd.extend(['-acodec', 'libmp3lame', '-b:a', '192k'])
            elif to_format == 'flac':
                cmd.extend(['-acodec', 'flac', '-compression_level', '5'])
            elif to_format == 'wav':
                cmd.extend(['-acodec', 'pcm_s16le'])
            elif to_format == 'mp4':
                cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])
            elif to_format == 'mov':
                cmd.extend(['-c:v', 'libx264', '-preset', 'medium', '-crf', '23'])
            
            # Add progress reporting and optimization flags for large files
            cmd.extend([
                '-progress', 'pipe:1',  # Progress to stdout
                '-nostats',  # Reduce output
                '-loglevel', 'error',  # Only show errors
                '-threads', '0',  # Use all available CPU cores
                output_file
            ])
            
            # Use Popen for better control over long-running processes
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor progress (simplified - in production you'd parse FFmpeg progress)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"FFmpeg failed: {stderr}")
            
            return output_file if os.path.exists(output_file) else None
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise Exception("FFmpeg conversion timed out")
        except Exception as e:
            raise Exception(f"FFmpeg conversion failed: {str(e)}")
    
    def _convert_image(self, source_file, output_file, from_format, to_format):
        """Convert image files using Pillow"""
        try:
            from PIL import Image
            
            with Image.open(source_file) as img:
                # Convert RGBA to RGB for JPEG
                if to_format.lower() in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA']:
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                img.save(output_file, format=to_format.upper())
            
            return output_file if os.path.exists(output_file) else None
            
        except Exception as e:
            raise Exception(f"Image conversion failed: {str(e)}")
    
    def _convert_archive(self, source_file, output_file, from_format, to_format):
        """Convert archive files"""
        try:
            # This is a simplified implementation
            # In production, you'd use proper archive libraries
            
            if from_format == 'zip' and to_format == 'rar':
                # Extract zip and create rar
                import zipfile
                import tempfile
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    with zipfile.ZipFile(source_file, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Use rar command to create archive
                    cmd = ['rar', 'a', output_file, f"{temp_dir}/*"]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise Exception("RAR creation failed")
            
            elif from_format == 'rar' and to_format == 'zip':
                # Extract rar and create zip
                import tempfile
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    cmd = ['unrar', 'x', source_file, temp_dir]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise Exception("RAR extraction failed")
                    
                    # Create zip
                    import zipfile
                    with zipfile.ZipFile(output_file, 'w') as zip_ref:
                        for root, dirs, files in os.walk(temp_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = os.path.relpath(file_path, temp_dir)
                                zip_ref.write(file_path, arc_path)
            
            else:
                raise Exception(f"Unsupported archive conversion: {from_format} to {to_format}")
            
            return output_file if os.path.exists(output_file) else None
            
        except Exception as e:
            raise Exception(f"Archive conversion failed: {str(e)}")
