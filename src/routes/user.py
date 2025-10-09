from flask import Blueprint

user_bp = Blueprint('user', __name__)

@user_bp.route('/formats', methods=['GET'])
def get_formats():
    """Get supported conversion formats"""
    from flask import jsonify
    
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
    
    return jsonify(conversion_map)
