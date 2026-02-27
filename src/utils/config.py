"""
Configuration loading and management.
"""

import os
import json
import logging
from typing import Optional


logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "camera": {
        "type": "gphoto2",
        "preview_fps": 15,
        "capture_delay_ms": 100,
        "auto_focus": True
    },
    "display": {
        "fullscreen": True,
        "resolution": [1024, 600],
        "show_countdown": True
    },
    "controller": {
        "enabled": True,
        "serial_port": "/dev/ttyUSB0",
        "baud_rate": 115200,
        "countdown_seconds": 3,
        "flash_duration_ms": 100
    },
    "led": {
        "enabled": True,
        "num_pixels": 24,
        "brightness": 255,
        "countdown_color": [255, 165, 0],
        "flash_color": [255, 255, 255],
        "idle_color": [0, 100, 255]
    },
    "sharing": {
        "hotspot_enabled": False,
        "hotspot_ssid": "PhotoBooth",
        "hotspot_password": "photos123",
        "hotspot_interface": "wlan0",
        "web_port": 8080,
        "web_host": "0.0.0.0",
        "onedrive_enabled": False,
        "onedrive_client_id": "",
        "onedrive_folder": "PhotoBooth"
    },
    "storage": {
        "photo_directory": "/home/pi/photos",
        "session_directory": "/home/pi/sessions",
        "keep_originals": True,
        "jpeg_quality": 95
    },
    "ui": {
        "theme": "dark",
        "language": "de",
        "idle_timeout_seconds": 60,
        "show_gallery": True,
        "max_photos_per_session": 10
    }
}


def get_config_path() -> str:
    """
    Get the configuration file path.
    
    Returns:
        Path to configuration file
    """
    # Check for config in common locations
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'settings', 'config.json'),
        os.path.expanduser('~/.config/open-imagebox/config.json'),
        '/etc/open-imagebox/config.json',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Return default path
    return possible_paths[0]


def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file (optional)
    
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = get_config_path()
    
    config = DEFAULT_CONFIG.copy()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
            
            # Deep merge user config into default
            config = _deep_merge(config, user_config)
            logger.info(f"Loaded configuration from: {config_path}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    else:
        logger.info(f"Config file not found: {config_path}, using defaults")
    
    return config


def save_config(config: dict, config_path: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save configuration (optional)
    
    Returns:
        True if saved successfully
    """
    if config_path is None:
        config_path = get_config_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Saved configuration to: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
