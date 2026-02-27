#!/usr/bin/env python3
"""
Manual image capture trigger for development purposes.

This script allows triggering image capture manually when hardware
trigger buttons and countdown LEDs are not yet available.

Usage:
    python3 scripts/trigger_capture.py [options]

Options:
    --config, -c    Path to configuration file
    --demo          Run in demo mode (no actual camera)
    --countdown     Seconds for countdown (default: 3)
    --output, -o    Output directory for photos
"""

import sys
import os
import argparse
import logging
import time
from datetime import datetime

# Add project root to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

try:
    from src.utils import load_config, setup_logging
    from src.camera import CameraManager
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Make sure you are running this script from the project root directory")
    print("and that all dependencies are installed.")
    print("\nTry:")
    print("  cd /path/to/Open-Imagebox")
    print("  source venv/bin/activate")
    print("  python3 scripts/trigger_capture.py")
    sys.exit(1)


logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Manual image capture trigger for development'
    )
    parser.add_argument(
        '-c', '--config',
        help='Path to configuration file',
        default=None
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (no actual camera capture)'
    )
    parser.add_argument(
        '--countdown',
        type=int,
        default=3,
        help='Countdown seconds before capture (default: 3)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory for photos',
        default=None
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--loop',
        action='store_true',
        help='Loop mode - keep running and capture on Enter key'
    )
    return parser.parse_args()


def countdown_display(seconds: int):
    """Display a countdown in the terminal."""
    print("\n" + "=" * 50)
    print("  MANUAL CAPTURE TRIGGER")
    print("=" * 50 + "\n")
    
    for i in range(seconds, 0, -1):
        print(f"  >>> {i} <<<", end='\r')
        time.sleep(1)
    
    print("  >>> CAPTURE! <<<")
    print()


def capture_photo(camera_manager, output_dir: str, demo_mode: bool = False) -> str:
    """
    Capture a photo.
    
    Args:
        camera_manager: CameraManager instance
        output_dir: Directory to save photo
        demo_mode: If True, don't actually capture
    
    Returns:
        Path to captured image or demo message
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"photo_{timestamp}.jpg")
    
    if demo_mode:
        logger.info(f"[DEMO MODE] Would capture to: {filename}")
        return f"[DEMO] {filename}"
    
    result = camera_manager.capture_image(filename)
    
    if result:
        logger.info(f"Photo captured: {result}")
        return result
    else:
        logger.error("Failed to capture photo")
        return None


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    
    print("\n" + "=" * 60)
    print("  Open-Imagebox Manual Capture Trigger")
    print("  (Development Tool - No Hardware Required)")
    print("=" * 60 + "\n")
    
    # Load configuration
    config = load_config(args.config)
    
    # Determine output directory
    output_dir = args.output
    if output_dir is None:
        # Use config value or fall back to temp directory
        default_dir = os.path.join(os.path.expanduser('~'), 'photos')
        output_dir = config.get('storage', {}).get('photo_directory', default_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Initialize camera (unless demo mode)
    camera_manager = None
    if not args.demo:
        logger.info("Initializing camera...")
        camera_manager = CameraManager(config)
        
        if camera_manager.initialize():
            logger.info("Camera connected successfully")
            print(f"Camera: {camera_manager.get_camera_info().get('model', 'Unknown')}")
        else:
            logger.warning("Camera not connected - switching to demo mode")
            args.demo = True
            print("WARNING: No camera detected, running in demo mode")
    else:
        print("Running in DEMO mode (no actual camera)")
    
    print(f"Output: {output_dir}")
    print(f"Countdown: {args.countdown} seconds")
    print()
    
    try:
        if args.loop:
            # Loop mode - keep capturing
            print("=" * 50)
            print("LOOP MODE: Press Enter to capture, Ctrl+C to exit")
            print("=" * 50)
            
            capture_count = 0
            while True:
                try:
                    input("\n>>> Press ENTER to trigger capture...")
                    
                    countdown_display(args.countdown)
                    result = capture_photo(camera_manager, output_dir, args.demo)
                    
                    if result:
                        capture_count += 1
                        print(f"Captured: {result}")
                        print(f"Total captures this session: {capture_count}")
                    else:
                        print("Capture failed!")
                    
                except EOFError:
                    break
        else:
            # Single capture mode
            print("Starting single capture...")
            input("Press ENTER when ready to start countdown...")
            
            countdown_display(args.countdown)
            result = capture_photo(camera_manager, output_dir, args.demo)
            
            if result:
                print(f"\n✓ Photo saved: {result}")
            else:
                print("\n✗ Capture failed!")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        if camera_manager:
            logger.info("Shutting down camera...")
            camera_manager.shutdown()
        
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
