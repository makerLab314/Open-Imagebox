"""
Serial communication with Arduino controller.
Based on self-o-mat's controller protocol.
"""

import threading
import logging
import time
from typing import Callable, Optional
from queue import Queue, Empty

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


logger = logging.getLogger(__name__)


class SerialController:
    """
    Handles serial communication with Arduino controller.
    
    Protocol:
    - Commands from Arduino: TRIGGER, READY
    - Commands to Arduino: LED:COUNTDOWN:n, LED:FLASH, LED:OFF, LED:IDLE
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize serial controller.
        
        Args:
            config: Configuration dictionary with controller settings.
        """
        self.config = config or {}
        self._port = self.config.get('serial_port', '/dev/ttyUSB0')
        self._baud_rate = self.config.get('baud_rate', 115200)
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._read_thread: Optional[threading.Thread] = None
        self._command_queue: Queue = Queue()
        self._callbacks: dict = {}
        
        if not SERIAL_AVAILABLE:
            logger.warning("pyserial not available. Install with: pip install pyserial")
    
    def connect(self) -> bool:
        """Connect to the Arduino controller."""
        if not SERIAL_AVAILABLE:
            logger.error("Serial not available")
            return False
        
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                timeout=1.0
            )
            
            # Wait for Arduino to reset
            time.sleep(2.0)
            
            # Clear any pending data
            self._serial.reset_input_buffer()
            
            logger.info(f"Connected to controller on {self._port}")
            
            # Start read thread
            self._running = True
            self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._read_thread.start()
            
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to controller: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the controller."""
        self._running = False
        
        if self._read_thread is not None:
            self._read_thread.join(timeout=2.0)
            self._read_thread = None
        
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception as e:
                logger.warning(f"Error closing serial: {e}")
            self._serial = None
        
        logger.info("Controller disconnected")
    
    def is_connected(self) -> bool:
        """Check if controller is connected."""
        return self._serial is not None and self._serial.is_open
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register a callback for controller events.
        
        Args:
            event: Event name ('trigger', 'ready')
            callback: Function to call when event occurs
        """
        self._callbacks[event.lower()] = callback
    
    def send_command(self, command: str) -> bool:
        """
        Send a command to the controller.
        
        Args:
            command: Command string to send
        
        Returns:
            True if command sent successfully
        """
        if not self.is_connected():
            return False
        
        try:
            cmd = command.strip() + '\n'
            self._serial.write(cmd.encode('utf-8'))
            self._serial.flush()
            logger.debug(f"Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def start_countdown(self, seconds: int = 3) -> bool:
        """Start LED countdown animation."""
        return self.send_command(f"LED:COUNTDOWN:{seconds}")
    
    def trigger_flash(self) -> bool:
        """Trigger the LED flash."""
        return self.send_command("LED:FLASH")
    
    def led_off(self) -> bool:
        """Turn off LEDs."""
        return self.send_command("LED:OFF")
    
    def led_idle(self) -> bool:
        """Set LED idle animation."""
        return self.send_command("LED:IDLE")
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness (0-255)."""
        brightness = max(0, min(255, brightness))
        return self.send_command(f"LED:BRIGHTNESS:{brightness}")
    
    def _read_loop(self) -> None:
        """Background thread for reading serial data."""
        while self._running and self._serial is not None:
            try:
                if self._serial.in_waiting > 0:
                    line = self._serial.readline().decode('utf-8').strip()
                    if line:
                        self._handle_message(line)
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                if self._running:
                    logger.error(f"Error reading from serial: {e}")
                    time.sleep(0.1)
    
    def _handle_message(self, message: str) -> None:
        """
        Handle incoming message from controller.
        
        Args:
            message: Message string from controller
        """
        logger.debug(f"Received from controller: {message}")
        
        message_upper = message.upper()
        
        if message_upper == 'TRIGGER':
            if 'trigger' in self._callbacks:
                self._callbacks['trigger']()
        
        elif message_upper == 'READY':
            if 'ready' in self._callbacks:
                self._callbacks['ready']()
        
        elif message_upper.startswith('ACK:'):
            # Acknowledgment messages
            logger.debug(f"Controller acknowledged: {message}")
        
        else:
            logger.debug(f"Unknown message from controller: {message}")
