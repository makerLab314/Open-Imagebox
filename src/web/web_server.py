"""
Web server for photo download.
Provides a simple web UI for browsing and downloading photos.
"""

import os
import socket
import logging
import threading
from typing import Optional, List

try:
    from flask import Flask, render_template_string, send_file, jsonify, url_for
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


logger = logging.getLogger(__name__)


# HTML template for the photo gallery
GALLERY_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📸 Photo Booth - Deine Fotos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header p {
            color: #888;
            font-size: 1.1em;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 20px 0;
        }
        
        .photo-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .photo-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }
        
        .photo-card img {
            width: 100%;
            height: 250px;
            object-fit: cover;
            display: block;
        }
        
        .photo-card .actions {
            padding: 15px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            transition: background 0.3s;
        }
        
        .btn-download {
            background: #4CAF50;
            color: white;
        }
        
        .btn-download:hover {
            background: #45a049;
        }
        
        .btn-view {
            background: #2196F3;
            color: white;
        }
        
        .btn-view:hover {
            background: #1976D2;
        }
        
        .download-all {
            text-align: center;
            padding: 30px;
        }
        
        .btn-all {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px 40px;
            font-size: 1.2em;
            border-radius: 30px;
        }
        
        .btn-all:hover {
            transform: scale(1.05);
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
        
        .empty-state .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
        }
        
        /* Lightbox */
        .lightbox {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .lightbox.active {
            display: flex;
        }
        
        .lightbox img {
            max-width: 95%;
            max-height: 95%;
            object-fit: contain;
        }
        
        .lightbox .close {
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 40px;
            cursor: pointer;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📸 Photo Booth</h1>
            <p>{{ photo_count }} Foto{% if photo_count != 1 %}s{% endif %} aufgenommen</p>
        </header>
        
        {% if photos %}
        <div class="gallery">
            {% for photo in photos %}
            <div class="photo-card">
                <img src="/thumbnail/{{ photo.filename }}" 
                     alt="Foto {{ loop.index }}"
                     onclick="openLightbox('/photo/{{ photo.filename }}')">
                <div class="actions">
                    <a href="/photo/{{ photo.filename }}" 
                       class="btn btn-view" 
                       target="_blank">Ansehen</a>
                    <a href="/download/{{ photo.filename }}" 
                       class="btn btn-download">⬇️ Download</a>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if photo_count > 1 %}
        <div class="download-all">
            <a href="/download-all" class="btn btn-all">
                📦 Alle Fotos herunterladen (ZIP)
            </a>
        </div>
        {% endif %}
        
        {% else %}
        <div class="empty-state">
            <div class="icon">📷</div>
            <h2>Noch keine Fotos</h2>
            <p>Nimm ein paar Fotos in der Photo Booth auf!</p>
        </div>
        {% endif %}
        
        <footer>
            <p>Open-Imagebox Photo Booth</p>
        </footer>
    </div>
    
    <!-- Lightbox -->
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="close">&times;</span>
        <img id="lightbox-img" src="" alt="Vollbild">
    </div>
    
    <script>
        function openLightbox(src) {
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').classList.add('active');
        }
        
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
        }
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeLightbox();
        });
    </script>
</body>
</html>
"""


class PhotoWebServer:
    """
    Web server for photo browsing and download.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize web server.
        
        Args:
            config: Configuration dictionary
        """
        if not FLASK_AVAILABLE:
            logger.error("Flask not available. Install with: pip install flask flask-cors")
            return
        
        self.config = config or {}
        self.sharing_config = self.config.get('sharing', {})
        self.storage_config = self.config.get('storage', {})
        
        self._host = self.sharing_config.get('web_host', '0.0.0.0')
        self._port = self.sharing_config.get('web_port', 8080)
        self._photo_dir = self.storage_config.get('session_directory', '/tmp/sessions')
        
        self._app: Optional[Flask] = None
        self._server_thread: Optional[threading.Thread] = None
        self._current_session_id: Optional[str] = None
        
        self._setup_app()
    
    def _setup_app(self):
        """Setup Flask application."""
        self._app = Flask(__name__)
        CORS(self._app)
        
        # Disable Flask logging in production
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
        
        @self._app.route('/')
        def index():
            """Main gallery page."""
            photos = self._get_session_photos()
            return render_template_string(
                GALLERY_TEMPLATE,
                photos=photos,
                photo_count=len(photos)
            )
        
        @self._app.route('/api/photos')
        def api_photos():
            """API endpoint for photo list."""
            photos = self._get_session_photos()
            return jsonify({
                'photos': photos,
                'count': len(photos)
            })
        
        @self._app.route('/photo/<filename>')
        def serve_photo(filename):
            """Serve a photo file."""
            photo_path = self._find_photo(filename)
            if photo_path and os.path.exists(photo_path):
                return send_file(photo_path)
            return 'Photo not found', 404
        
        @self._app.route('/thumbnail/<filename>')
        def serve_thumbnail(filename):
            """Serve a thumbnail (for now, same as full photo)."""
            # In production, you'd generate actual thumbnails
            return serve_photo(filename)
        
        @self._app.route('/download/<filename>')
        def download_photo(filename):
            """Download a photo file."""
            photo_path = self._find_photo(filename)
            if photo_path and os.path.exists(photo_path):
                return send_file(
                    photo_path,
                    as_attachment=True,
                    download_name=filename
                )
            return 'Photo not found', 404
        
        @self._app.route('/download-all')
        def download_all():
            """Download all photos as ZIP."""
            import zipfile
            import io
            
            photos = self._get_session_photos()
            if not photos:
                return 'No photos available', 404
            
            # Create ZIP in memory
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for photo in photos:
                    photo_path = self._find_photo(photo['filename'])
                    if photo_path and os.path.exists(photo_path):
                        zf.write(photo_path, photo['filename'])
            
            memory_file.seek(0)
            
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name='photobooth_photos.zip'
            )
    
    def start(self) -> bool:
        """
        Start the web server.
        
        Returns:
            True if server started successfully
        """
        if self._app is None:
            return False
        
        try:
            self._server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self._server_thread.start()
            
            logger.info(f"Web server started on http://{self._host}:{self._port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
            return False
    
    def _run_server(self):
        """Run the Flask server."""
        self._app.run(
            host=self._host,
            port=self._port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    
    def stop(self):
        """Stop the web server."""
        # Flask doesn't have a clean shutdown mechanism in this setup
        # Server will stop when the application exits
        pass
    
    def set_current_session(self, session_id: str) -> None:
        """
        Set the current session to serve photos from.
        
        Args:
            session_id: Session identifier
        """
        self._current_session_id = session_id
    
    def get_host_ip(self) -> str:
        """
        Get the server's IP address.
        
        Returns:
            IP address string
        """
        try:
            # Get local IP by connecting to external address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "192.168.4.1"  # Default hotspot IP
    
    def get_url(self) -> str:
        """
        Get the full URL to access the web server.
        
        Returns:
            URL string
        """
        return f"http://{self.get_host_ip()}:{self._port}"
    
    def _get_session_photos(self) -> List[dict]:
        """
        Get photos for the current session, or all photos from the latest session.
        
        Returns:
            List of photo info dictionaries
        """
        photos = []
        
        if self._current_session_id:
            session_path = os.path.join(self._photo_dir, self._current_session_id)
        else:
            # Find most recent session
            session_path = self._get_latest_session_path()
        
        if session_path and os.path.isdir(session_path):
            for filename in sorted(os.listdir(session_path)):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    photos.append({
                        'filename': filename,
                        'path': os.path.join(session_path, filename),
                        'session': os.path.basename(session_path)
                    })
        
        # If no session photos found, also check the photo directory directly
        if not photos and os.path.isdir(self._photo_dir):
            for filename in sorted(os.listdir(self._photo_dir)):
                filepath = os.path.join(self._photo_dir, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(
                        ('.jpg', '.jpeg', '.png')):
                    photos.append({
                        'filename': filename,
                        'path': filepath,
                        'session': ''
                    })
        
        return photos
    
    def _get_latest_session_path(self) -> Optional[str]:
        """Get the path to the most recent session."""
        if not os.path.isdir(self._photo_dir):
            return None
        
        sessions = [
            d for d in os.listdir(self._photo_dir)
            if os.path.isdir(os.path.join(self._photo_dir, d))
        ]
        
        if not sessions:
            return None
        
        # Sort by name (timestamp-based naming)
        sessions.sort(reverse=True)
        return os.path.join(self._photo_dir, sessions[0])
    
    def _find_photo(self, filename: str) -> Optional[str]:
        """
        Find a photo file.
        
        Args:
            filename: Photo filename
        
        Returns:
            Full path to photo, or None if not found
        """
        # First check current session
        if self._current_session_id:
            path = os.path.join(self._photo_dir, self._current_session_id, filename)
            if os.path.exists(path):
                return path
        
        # Then check latest session
        session_path = self._get_latest_session_path()
        if session_path:
            path = os.path.join(session_path, filename)
            if os.path.exists(path):
                return path
        
        return None
