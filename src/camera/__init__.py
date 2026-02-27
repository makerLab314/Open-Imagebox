"""
Camera module for Open-Imagebox.
Provides camera communication using gPhoto2 (inspired by self-o-mat).
"""

from .camera_base import CameraBase
from .gphoto2_camera import GPhoto2Camera
from .camera_manager import CameraManager

__all__ = ['CameraBase', 'GPhoto2Camera', 'CameraManager']
