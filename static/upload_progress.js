/**
 * Enhanced upload progress handling for large files
 */

class LargeFileUploader {
    constructor() {
        this.xhr = null;
        this.uploadStartTime = null;
        this.onProgress = null;
        this.onComplete = null;
        this.onError = null;
    }

    upload(formData, options = {}) {
        return new Promise((resolve, reject) => {
            this.xhr = new XMLHttpRequest();
            this.uploadStartTime = Date.now();

            // Set up progress tracking
            this.xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    const elapsed = Date.now() - this.uploadStartTime;
                    const speed = e.loaded / (elapsed / 1000); // bytes per second
                    const remaining = (e.total - e.loaded) / speed; // seconds remaining

                    const progressInfo = {
                        percent: Math.round(percentComplete),
                        loaded: e.loaded,
                        total: e.total,
                        speed: this.formatSpeed(speed),
                        remaining: this.formatTime(remaining)
                    };

                    if (this.onProgress) {
                        this.onProgress(progressInfo);
                    }
                }
            });

            // Handle completion
            this.xhr.addEventListener('load', () => {
                if (this.xhr.status >= 200 && this.xhr.status < 300) {
                    try {
                        const response = JSON.parse(this.xhr.responseText);
                        if (this.onComplete) {
                            this.onComplete(response);
                        }
                        resolve(response);
                    } catch (e) {
                        reject(new Error('Invalid JSON response'));
                    }
                } else {
                    const error = new Error(`Upload failed with status ${this.xhr.status}`);
                    if (this.onError) {
                        this.onError(error);
                    }
                    reject(error);
                }
            });

            // Handle errors
            this.xhr.addEventListener('error', () => {
                const error = new Error('Upload failed');
                if (this.onError) {
                    this.onError(error);
                }
                reject(error);
            });

            // Handle timeout
            this.xhr.addEventListener('timeout', () => {
                const error = new Error('Upload timed out');
                if (this.onError) {
                    this.onError(error);
                }
                reject(error);
            });

            // Configure request
            this.xhr.open('POST', '/api/convert');
            this.xhr.timeout = options.timeout || 3600000; // 1 hour default timeout

            // Send the request
            this.xhr.send(formData);
        });
    }

    cancel() {
        if (this.xhr) {
            this.xhr.abort();
        }
    }

    formatSpeed(bytesPerSecond) {
        const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
        let size = bytesPerSecond;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    formatTime(seconds) {
        if (seconds < 60) {
            return `${Math.round(seconds)}s`;
        } else if (seconds < 3600) {
            return `${Math.round(seconds / 60)}m`;
        } else {
            return `${Math.round(seconds / 3600)}h`;
        }
    }

    formatFileSize(bytes) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }
}

// Enhanced progress display for large files
function showUploadProgress(progressInfo) {
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    if (!progressContainer.querySelector('.upload-details')) {
        // Add detailed progress information
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'upload-details mt-2 text-sm text-gray-400';
        detailsDiv.innerHTML = `
            <div class="flex justify-between">
                <span id="upload-speed">Speed: --</span>
                <span id="upload-remaining">Time remaining: --</span>
            </div>
            <div class="mt-1">
                <span id="upload-size">Size: --</span>
            </div>
        `;
        progressContainer.appendChild(detailsDiv);
    }

    // Update progress
    progressBar.style.width = progressInfo.percent + '%';
    progressText.textContent = `Uploading... ${progressInfo.percent}%`;
    
    // Update detailed information
    document.getElementById('upload-speed').textContent = `Speed: ${progressInfo.speed}`;
    document.getElementById('upload-remaining').textContent = `Time remaining: ${progressInfo.remaining}`;
    document.getElementById('upload-size').textContent = `Size: ${new LargeFileUploader().formatFileSize(progressInfo.loaded)} / ${new LargeFileUploader().formatFileSize(progressInfo.total)}`;
}

// Export for use in main application
window.LargeFileUploader = LargeFileUploader;
window.showUploadProgress = showUploadProgress;
