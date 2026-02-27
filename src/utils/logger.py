"""
Logging configuration for Open-Imagebox.
"""

import logging
import os
from datetime import datetime


def setup_logging(level: int = logging.INFO,
                  log_file: bool = True,
                  log_dir: str = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Whether to log to file
        log_dir: Directory for log files
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        if log_dir is None:
            log_dir = os.path.expanduser('~/.local/share/open-imagebox/logs')
        
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = datetime.now().strftime("photobooth_%Y%m%d_%H%M%S.log")
        log_path = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        logging.info(f"Logging to file: {log_path}")
    
    # Suppress noisy loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
