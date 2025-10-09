import os
import hashlib
import tempfile
from werkzeug.datastructures import FileStorage
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

class LargeFileHandler:
    def __init__(self, upload_dir, chunk_size=8192):
        self.upload_dir = upload_dir
        self.chunk_size = chunk_size
        os.makedirs(upload_dir, exist_ok=True)
    
    def save_large_file(self, file_storage: FileStorage, filename: str) -> str:
        """
        Save a large file efficiently using streaming
        Returns the path to the saved file
        """
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            # Use a temporary file first, then move to final location
            with tempfile.NamedTemporaryFile(delete=False, dir=self.upload_dir) as temp_file:
                temp_path = temp_file.name
                
                # Stream the file in chunks to avoid memory issues
                total_size = 0
                while True:
                    chunk = file_storage.read(self.chunk_size)
                    if not chunk:
                        break
                    temp_file.write(chunk)
                    total_size += len(chunk)
                
                # Move temp file to final location
                os.rename(temp_path, file_path)
                
                logger.info(f"Successfully saved large file: {filename} ({total_size} bytes)")
                return file_path
                
        except Exception as e:
            logger.error(f"Failed to save large file {filename}: {str(e)}")
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def validate_large_file(self, file_storage: FileStorage, max_size: int) -> bool:
        """
        Validate file size without loading entire file into memory
        """
        try:
            # Get file size from Content-Length header if available
            content_length = request.headers.get('Content-Length')
            if content_length:
                file_size = int(content_length)
                if file_size > max_size:
                    return False
            
            # If no Content-Length, we'll have to read the file to check size
            # This is less efficient but necessary for some uploads
            current_pos = file_storage.tell()
            file_storage.seek(0, os.SEEK_END)
            file_size = file_storage.tell()
            file_storage.seek(current_pos)
            
            return file_size <= max_size
            
        except Exception as e:
            logger.error(f"Failed to validate file size: {str(e)}")
            return False
    
    def get_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a large file efficiently
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate file hash: {str(e)}")
            return None
    
    def cleanup_file(self, file_path: str):
        """
        Safely remove a file
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {str(e)}")

class ChunkedUploadManager:
    """
    Manages chunked uploads for very large files
    """
    def __init__(self, upload_dir):
        self.upload_dir = upload_dir
        self.chunks_dir = os.path.join(upload_dir, 'chunks')
        os.makedirs(self.chunks_dir, exist_ok=True)
    
    def handle_chunk(self, chunk_data, chunk_number, total_chunks, upload_id):
        """
        Handle a single chunk of a large file upload
        """
        try:
            chunk_filename = f"{upload_id}_chunk_{chunk_number}"
            chunk_path = os.path.join(self.chunks_dir, chunk_filename)
            
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)
            
            # Check if all chunks are uploaded
            if self._all_chunks_uploaded(upload_id, total_chunks):
                return self._assemble_chunks(upload_id, total_chunks)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to handle chunk {chunk_number}: {str(e)}")
            raise
    
    def _all_chunks_uploaded(self, upload_id, total_chunks):
        """
        Check if all chunks for an upload are present
        """
        for i in range(total_chunks):
            chunk_filename = f"{upload_id}_chunk_{i}"
            chunk_path = os.path.join(self.chunks_dir, chunk_filename)
            if not os.path.exists(chunk_path):
                return False
        return True
    
    def _assemble_chunks(self, upload_id, total_chunks):
        """
        Assemble all chunks into a single file
        """
        try:
            final_filename = f"{upload_id}_assembled"
            final_path = os.path.join(self.upload_dir, final_filename)
            
            with open(final_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_filename = f"{upload_id}_chunk_{i}"
                    chunk_path = os.path.join(self.chunks_dir, chunk_filename)
                    
                    with open(chunk_path, 'rb') as chunk_file:
                        final_file.write(chunk_file.read())
                    
                    # Clean up chunk file
                    os.unlink(chunk_path)
            
            logger.info(f"Successfully assembled file: {final_filename}")
            return final_path
            
        except Exception as e:
            logger.error(f"Failed to assemble chunks for {upload_id}: {str(e)}")
            # Clean up partial chunks
            self._cleanup_chunks(upload_id, total_chunks)
            raise
    
    def _cleanup_chunks(self, upload_id, total_chunks):
        """
        Clean up chunk files
        """
        for i in range(total_chunks):
            chunk_filename = f"{upload_id}_chunk_{i}"
            chunk_path = os.path.join(self.chunks_dir, chunk_filename)
            if os.path.exists(chunk_path):
                try:
                    os.unlink(chunk_path)
                except Exception as e:
                    logger.error(f"Failed to cleanup chunk {chunk_path}: {str(e)}")
