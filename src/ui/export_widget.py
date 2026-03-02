"""
Export widget with QR code for photo sharing.
"""

import logging
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QFrame, QSizePolicy
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QPixmap, QImage
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QWidget = object

try:
    import qrcode
    from PIL import Image
    import io
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


logger = logging.getLogger(__name__)


class ExportWidget(QWidget):
    """
    Widget for exporting/sharing photos via QR code.
    Shows QR codes for WiFi hotspot connection and photo download.
    """
    
    # Signal when user wants to start new session
    new_session_requested = pyqtSignal() if PYQT5_AVAILABLE else None
    
    def __init__(self, parent=None):
        if not PYQT5_AVAILABLE:
            logger.error("PyQt5 not available")
            return
        
        super().__init__(parent)
        self._wifi_qr_data: Optional[str] = None
        self._download_url: Optional[str] = None
        self._onedrive_url: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup export UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📤 Fotos herunterladen")
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: white;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Scanne den QR-Code mit deinem Handy um die Fotos herunterzuladen"
        )
        instructions.setStyleSheet("font-size: 20px; color: #AAA;")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # QR codes container
        qr_layout = QHBoxLayout()
        qr_layout.setSpacing(40)
        
        # WiFi QR code
        self._wifi_frame = self._create_qr_frame("📶 WiFi verbinden")
        self._wifi_qr_label = self._wifi_frame.findChild(QLabel, "qr_image")
        qr_layout.addWidget(self._wifi_frame)
        
        # Download QR code
        self._download_frame = self._create_qr_frame("📱 Fotos öffnen")
        self._download_qr_label = self._download_frame.findChild(QLabel, "qr_image")
        qr_layout.addWidget(self._download_frame)
        
        layout.addLayout(qr_layout)
        
        # OneDrive option (if enabled)
        self._onedrive_frame = QFrame()
        self._onedrive_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        onedrive_layout = QHBoxLayout(self._onedrive_frame)
        
        onedrive_icon = QLabel("☁️")
        onedrive_icon.setStyleSheet("font-size: 40px;")
        onedrive_layout.addWidget(onedrive_icon)
        
        onedrive_text = QLabel("OneDrive: Fotos werden hochgeladen...")
        onedrive_text.setStyleSheet("font-size: 18px; color: #AAA;")
        self._onedrive_status_label = onedrive_text
        onedrive_layout.addWidget(onedrive_text, 1)
        
        self._onedrive_qr_label = QLabel()
        self._onedrive_qr_label.setFixedSize(100, 100)
        onedrive_layout.addWidget(self._onedrive_qr_label)
        
        self._onedrive_frame.setVisible(False)
        layout.addWidget(self._onedrive_frame)
        
        layout.addStretch()
        
        # New session button
        self._new_session_button = QPushButton("🔄 Neue Session starten")
        self._new_session_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 20px 40px;
                border-radius: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self._new_session_button.clicked.connect(self._on_new_session)
        layout.addWidget(self._new_session_button, alignment=Qt.AlignCenter)
    
    def _create_qr_frame(self, title: str) -> QFrame:
        """Create a QR code display frame."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                padding: 20px;
            }
        """)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.setMaximumSize(350, 400)
        
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #333;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # QR image
        qr_label = QLabel()
        qr_label.setObjectName("qr_image")
        qr_label.setFixedSize(250, 250)
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet("background-color: #EEE; border-radius: 10px;")
        layout.addWidget(qr_label)
        
        return frame
    
    def set_wifi_qr(self, ssid: str, password: str, security: str = "WPA") -> None:
        """
        Set WiFi QR code data.
        
        Args:
            ssid: WiFi network name
            password: WiFi password
            security: Security type (WPA, WEP, or empty for open)
        """
        # WiFi QR code format
        wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
        self._wifi_qr_data = wifi_string
        
        qr_pixmap = self._generate_qr_pixmap(wifi_string)
        if qr_pixmap and self._wifi_qr_label:
            self._wifi_qr_label.setPixmap(qr_pixmap)
    
    def set_download_url(self, url: str) -> None:
        """
        Set download URL QR code.
        
        Args:
            url: URL to access photos
        """
        self._download_url = url
        
        qr_pixmap = self._generate_qr_pixmap(url)
        if qr_pixmap and self._download_qr_label:
            self._download_qr_label.setPixmap(qr_pixmap)
    
    def set_onedrive_url(self, url: str) -> None:
        """
        Set OneDrive share URL.
        
        Args:
            url: OneDrive share URL
        """
        self._onedrive_url = url
        self._onedrive_frame.setVisible(True)
        self._onedrive_status_label.setText("OneDrive: Fotos verfügbar!")
        
        qr_pixmap = self._generate_qr_pixmap(url, size=100)
        if qr_pixmap:
            self._onedrive_qr_label.setPixmap(qr_pixmap)
    
    def show_onedrive_uploading(self) -> None:
        """Show OneDrive uploading status."""
        self._onedrive_frame.setVisible(True)
        self._onedrive_status_label.setText("OneDrive: Fotos werden hochgeladen...")
        self._onedrive_qr_label.clear()
    
    def hide_onedrive(self) -> None:
        """Hide OneDrive section."""
        self._onedrive_frame.setVisible(False)
    
    def _generate_qr_pixmap(self, data: str, size: int = 250) -> Optional[QPixmap]:
        """
        Generate a QR code as QPixmap.
        
        Args:
            data: Data to encode
            size: Target size in pixels
        
        Returns:
            QPixmap of QR code, or None on failure
        """
        if not QRCODE_AVAILABLE:
            logger.warning("qrcode library not available")
            return None
        
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create PIL image
            pil_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to QPixmap
            buffer = io.BytesIO()
            pil_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            qimage = QImage()
            qimage.loadFromData(buffer.read())
            
            pixmap = QPixmap.fromImage(qimage)
            return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return None
    
    def _on_new_session(self) -> None:
        """Handle new session button click."""
        if self.new_session_requested:
            self.new_session_requested.emit()
