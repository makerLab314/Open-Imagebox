"""
Open-Imagebox - Photo Booth Software for Raspberry Pi
Main application entry point.

Inspired by the self-o-mat project (https://github.com/xtech/self-o-mat)
"""

import sys
import signal
import logging
import argparse

from src.utils import load_config, setup_logging
from src.camera import CameraManager
from src.controller import PhotoBoothController
from src.web import PhotoWebServer
from src.sharing import SharingManager


logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Open-Imagebox Photo Booth Software'
    )
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file',
        default=None
    )
    parser.add_argument(
        '--no-gui',
        action='store_true',
        help='Run without GUI (headless mode)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--windowed',
        action='store_true',
        help='Run in windowed mode (not fullscreen)'
    )
    
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    
    logger.info("=" * 60)
    logger.info("Open-Imagebox Photo Booth")
    logger.info("Inspired by self-o-mat (https://github.com/xtech/self-o-mat)")
    logger.info("=" * 60)
    
    # Load configuration
    config = load_config(args.config)
    
    # Override fullscreen if windowed mode requested
    if args.windowed:
        config['display']['fullscreen'] = False
    
    # Initialize components
    camera_manager = None
    booth_controller = None
    web_server = None
    sharing_manager = None
    main_window = None
    
    try:
        # Initialize camera
        logger.info("Initializing camera...")
        camera_manager = CameraManager(config)
        if camera_manager.initialize():
            logger.info("Camera connected successfully")
        else:
            logger.warning("Camera not connected - running in demo mode")
        
        # Initialize hardware controller
        logger.info("Initializing hardware controller...")
        booth_controller = PhotoBoothController(config)
        booth_controller.initialize()
        
        # Initialize sharing
        logger.info("Initializing sharing services...")
        sharing_manager = SharingManager(config)
        sharing_manager.initialize()
        
        # Initialize web server
        logger.info("Starting web server...")
        web_server = PhotoWebServer(config)
        web_server.start()
        sharing_manager.set_web_url(web_server.get_url())
        
        # Start UI if not headless
        if not args.no_gui:
            logger.info("Starting GUI...")
            
            try:
                from PyQt6.QtWidgets import QApplication
                from src.ui import MainWindow
                
                app = QApplication(sys.argv)
                app.setApplicationName("Open-Imagebox")
                
                # Create main window
                main_window = MainWindow(config)
                main_window.set_camera_manager(camera_manager)
                main_window.set_controller(booth_controller)
                main_window.set_web_server(web_server)
                main_window.set_sharing_manager(sharing_manager)
                main_window.show()
                
                # Handle signals
                def signal_handler(sig, frame):
                    logger.info("Shutdown signal received")
                    app.quit()
                
                signal.signal(signal.SIGINT, signal_handler)
                signal.signal(signal.SIGTERM, signal_handler)
                
                # Run application
                sys.exit(app.exec())
                
            except ImportError as e:
                logger.error(f"PyQt6 not available: {e}")
                logger.info("Install PyQt6: pip install PyQt6")
                sys.exit(1)
        else:
            # Headless mode - just run the web server
            logger.info("Running in headless mode (no GUI)")
            logger.info(f"Web interface available at: {web_server.get_url()}")
            
            # Keep running until interrupted
            signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
            signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
            
            import time
            while True:
                time.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    
    finally:
        # Cleanup
        logger.info("Shutting down...")
        
        if booth_controller:
            booth_controller.shutdown()
        
        if camera_manager:
            camera_manager.shutdown()
        
        if sharing_manager:
            sharing_manager.shutdown()
        
        logger.info("Goodbye!")


if __name__ == '__main__':
    main()
