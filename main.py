import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from src.models.user import db
from src.models.job import Job
from src.routes.user import user_bp
from src.routes.conversion import conversion_bp
from src.routes.health import health_bp
from src.utils.logging import log_request, log_response, health_monitor

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for frontend integration - restrict to production domain
# In development, REPLIT_DEPLOYMENT will not be set, so we allow all origins for testing
if os.environ.get('REPLIT_DEPLOYMENT'):
    # Production: Only allow gigovert.net
    CORS(app, origins=['https://gigovert.net', 'http://gigovert.net'])
else:
    # Development: Allow all origins for testing
    CORS(app, origins=['*'])

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(conversion_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')

# Add request/response logging middleware
@app.before_request
def before_request():
    log_request()
    health_monitor.increment_requests()

@app.after_request
def after_request(response):
    return log_response(response)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'check_same_thread': False}}
db.init_app(app)
with app.app_context():
    db.create_all()

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - return JSON for API calls, HTML for others"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return serve_static_file('')

def serve_static_file(path):
    """Serve static files with proper error handling"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({'error': 'Static folder not configured'}), 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({'error': 'index.html not found'}), 404

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Don't serve static files for API routes
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    return serve_static_file(path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
