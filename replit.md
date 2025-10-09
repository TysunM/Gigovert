# Universal File Converter

## Overview

This is a Flask-based web application that provides universal file conversion capabilities.

**Production URL**: gigovert.net

The system supports converting between multiple media formats including audio (MP3, WAV, FLAC, etc.), video (MP4, MOV), images (PNG, JPG), and archives (ZIP, RAR, ISO). It also includes YouTube video/audio download and conversion functionality. The application is designed to handle large files up to 40GB with streaming upload support and background job processing.

## Recent Changes

### October 9, 2025 - Production Security & Server Hardening
- **Fixed critical security vulnerability**: File upload validation now properly checks dangerous extensions (.exe, .bat, .cmd, etc.) for ALL files, not just those over 40GB
- **Added Gunicorn production server**: Replaced Flask development server with Gunicorn (4 workers, 300s timeout) for both local workflow and production deployment
- **Implemented environment-aware CORS policy**: 
  - Production (when REPLIT_DEPLOYMENT is set): Restricted to gigovert.net only (https and http)
  - Development: Allows all origins for testing
- **Enhanced ConversionService**: Added Flask app requirement validation to prevent threading context errors

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Tailwind CSS for styling
- **Design Pattern**: Single-page application with progressive enhancement
- **File Upload**: Custom large file uploader class with chunked streaming (8MB chunks)
- **UI/UX**: Dark-themed interface with real-time progress tracking, speed calculation, and remaining time estimation
- **Rationale**: Lightweight frontend without framework dependencies for faster load times and simpler deployment

### Backend Architecture
- **Framework**: Flask 3.0.0 with Blueprint-based modular routing
- **API Structure**: RESTful endpoints organized by domain:
  - `/api/convert` - File conversion operations
  - `/api/health` - Health checks and metrics
  - `/api/formats` - Supported format information
- **Background Processing**: Threading-based job queue (daemon threads) with Flask app context management
- **Error Handling**: Global error handlers for 404 and 500 errors with JSON responses
- **Middleware**: Request/response logging and health monitoring on all requests
- **CORS**: Environment-aware CORS policy
  - Production (REPLIT_DEPLOYMENT set): Restricted to gigovert.net (https/http)
  - Development: Allows all origins for testing
- **Production Server**: Gunicorn WSGI server (4 workers, 300s timeout, sync worker class)

**Design Rationale**: Blueprint organization provides clean separation of concerns and makes the codebase maintainable. Threading was chosen over Celery for simplicity in deployment, though the architecture allows for future migration to a proper task queue.

### Data Storage Solutions
- **Primary Database**: SQLite with SQLAlchemy ORM
- **Schema Design**:
  - Jobs table: Tracks conversion jobs with status, progress, file paths, error messages, and timestamps
  - UUID-based job IDs for uniqueness and security
- **File Storage**: Local filesystem with separate directories:
  - `/uploads` - Temporary uploaded files
  - `/outputs` - Converted output files
  - `/src/database` - SQLite database file
- **Configuration**: 
  - `check_same_thread=False` for SQLite to allow multi-threaded access
  - Track modifications disabled for performance

**Design Rationale**: SQLite chosen for simplicity and zero-configuration deployment. The file-based approach works well for the use case, though the architecture supports migration to PostgreSQL or other databases via SQLAlchemy's abstraction layer.

### Job Processing Architecture
- **Job Lifecycle**: queued → processing → completed/failed
- **Progress Tracking**: Percentage-based progress updates (0-100)
- **Source Types**: Supports both file uploads and YouTube URLs
- **Conversion Pipeline**:
  1. Validation of conversion compatibility
  2. Job creation and queueing
  3. Source preparation (upload handling or YouTube download)
  4. Format conversion using external tools
  5. Output storage and status update

**Design Rationale**: Asynchronous job processing prevents request timeouts for large files. Status tracking enables real-time frontend updates.

### Large File Handling
- **Maximum Size**: 40GB per file
- **Upload Strategy**: Streaming with 8MB chunks to prevent memory overflow
- **Temporary File Management**: Uses Python's tempfile for atomic file operations
- **Memory Protection**: Configurable limits (2GB max per process)
- **Disk Space Monitoring**: Minimum 50GB free space requirement with periodic checks
- **Timeouts**: 
  - Upload: 1 hour
  - Conversion: 2 hours
  - YouTube download: 1 hour

**Design Rationale**: Chunked streaming prevents memory exhaustion on large uploads. Temporary file usage ensures atomic operations and easier cleanup. Configurable limits allow adaptation to different deployment environments.

### Security & Rate Limiting
- **Rate Limiting**: Custom implementation with IP-based tracking
  - Default: 10 requests per minute per IP
  - Temporary blocking: 5 minutes for violators
- **Input Validation**:
  - Filename sanitization to prevent path traversal
  - YouTube URL pattern matching
  - **File Upload Security**: Validates all uploads for dangerous extensions (.exe, .bat, .cmd, .scr, .pif, .com, .jar)
  - **File Size Limit**: 40GB maximum per file with proper validation
- **Secret Key**: Environment-based configuration with development fallback
- **CORS Security**: Environment-aware policy restricts production access to gigovert.net domain only

**Design Rationale**: Built-in rate limiting avoids external dependencies. IP-based tracking is simple but effective for basic protection. The system is designed to add more sophisticated security layers (API keys, user authentication) without architectural changes.

### Monitoring & Logging
- **Log Types**:
  - Application logs: General system events
  - Conversion logs: Job-specific tracking
  - Error logs: Failure tracking
  - Security logs: Security-related events
- **Health Monitoring**: 
  - Database connection status
  - Job statistics (total, completed, failed, processing, queued)
  - Request counting
  - System metrics endpoint
- **Log Format**: JSON structured logging for conversions, standard format for application logs

**Design Rationale**: Separate log files enable targeted debugging and monitoring. JSON format for conversion logs allows easy parsing and analysis. Health endpoints support integration with monitoring tools.

## External Dependencies

### Third-Party Libraries
- **Flask Ecosystem**:
  - `Flask==3.0.0` - Web framework
  - `flask-cors==4.0.0` - CORS support for API access
  - `flask-sqlalchemy==3.1.1` - Database ORM
  - `Werkzeug==3.0.1` - WSGI utilities
  - `gunicorn==23.0.0` - Production WSGI server

- **Media Processing**:
  - `Pillow==10.1.0` - Image conversion and manipulation
  - `yt-dlp==2024.8.6` - YouTube video/audio download

### External Tools (Expected)
- **FFmpeg**: Required for audio/video conversions (MP3, WAV, FLAC, MP4, MOV, etc.)
  - Used via subprocess for format conversion
  - Configured with thread count optimization and quality presets
  - CRF settings for video quality control

- **Archive Tools**: For RAR/ISO/ZIP conversions
  - Likely uses system utilities via subprocess

### Database
- **SQLite**: Embedded database (no external service required)
- **Location**: `src/database/app.db`
- **Note**: Architecture supports migration to PostgreSQL or other databases via SQLAlchemy

### Frontend CDN Dependencies
- **Tailwind CSS**: Loaded via CDN for styling
- **Google Fonts**: Inter font family for typography

### Environment Variables
- `SECRET_KEY` - Flask secret key for session management (optional, has fallback)
- `REPLIT_DEPLOYMENT` - Automatically set in production deployments to trigger strict CORS policy

## Production Deployment

### Server Configuration
- **WSGI Server**: Gunicorn 23.0.0
- **Worker Configuration**: 
  - 4 sync workers for concurrent request handling
  - 300 second timeout for long-running operations
  - Bound to 0.0.0.0:5000 for external access
- **Logging**: Access and error logs streamed to stdout/stderr
- **Deployment Target**: Autoscale (stateless, scales based on traffic)

### Deployment Command
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 --access-logfile - --error-logfile - main:app
```

### Security Notes
- CORS automatically restricts to gigovert.net in production (when REPLIT_DEPLOYMENT env var is set)
- File upload validation enforces dangerous extension checks for all files
- Flask development server (`python main.py`) should not be used in production

### Known Limitations & Future Improvements
- **Tailwind CSS**: Currently loaded via CDN; should migrate to PostCSS for production optimization
- **Task Queue**: Currently uses threading; recommend migrating to Celery + Redis for better scalability
- **Rate Limiting**: In-memory implementation; should migrate to Redis for multi-instance support
- **Database Migrations**: Uses db.create_all(); should implement Flask-Migrate for schema management

### File System Requirements
- **Writable Directories**: 
  - `/uploads` - Temporary file storage
  - `/outputs` - Converted file storage  
  - `/src/database` - Database file location
  - `/src/logs` - Application logs
- **Disk Space**: Minimum 50GB free space recommended for large file operations