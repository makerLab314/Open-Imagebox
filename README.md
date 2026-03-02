# Open-Imagebox

A fully-featured photo booth software for Raspberry Pi 3B+, inspired by the [self-o-mat project](https://github.com/xtech/self-o-mat).

## Features

- **Live Preview** - Real-time camera preview on HDMI touchscreen
- **DSLR Camera Support** - Canon cameras via USB using gPhoto2
- **Hardware Controller** - Arduino-based trigger button, countdown LED ring light, flash synchronization
- **Multi-Photo Session** - Take multiple photos per session
- **Export Options**:
  - WiFi Hotspot with QR code for mobile photo download
  - Web UI for browsing and downloading photos
  - OneDrive cloud upload with shareable QR code

## Hardware Requirements

- Raspberry Pi 3B+ (or newer)
- Canon DSLR Camera (USB connected)
- HDMI Touchscreen Display
- Arduino Nano (for controller)
- LED Ring Light (WS2812B/NeoPixel compatible)
- Push Button for trigger
- Optional: External Flash

## Software Requirements

- Python 3.8+
- gPhoto2
- Qt5 (PyQt5)
- Additional Python packages (see requirements.txt)

## Installation

### Quick Install (Raspberry Pi OS)

```bash
# Clone the repository
git clone https://github.com/makerLab314/Open-Imagebox.git
cd Open-Imagebox

# Run the install script
./scripts/install.sh
```

### Manual Installation

1. Install system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    gphoto2 libgphoto2-dev \
    libqt5gui5 python3-pyqt5 \
    hostapd dnsmasq \
    qrencode \
    libzbar0
```

2. Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

3. Configure the software:

```bash
cp settings/config.example.json settings/config.json
# Edit settings/config.json to match your setup
```

4. Upload Arduino firmware (optional, for hardware controller):

```bash
# Using Arduino IDE or arduino-cli
arduino-cli upload -p /dev/ttyUSB0 -b arduino:avr:nano arduino/controller/controller.ino
```

5. Run the photo booth:

```bash
python3 -m src.main
```

## Configuration

Edit `settings/config.json` to customize:

```json
{
    "camera": {
        "type": "gphoto2",
        "preview_fps": 15
    },
    "display": {
        "fullscreen": true,
        "resolution": [1024, 600]
    },
    "controller": {
        "serial_port": "/dev/ttyUSB0",
        "baud_rate": 115200,
        "countdown_seconds": 3
    },
    "led": {
        "num_pixels": 24,
        "brightness": 255
    },
    "sharing": {
        "hotspot_enabled": false,
        "hotspot_ssid": "PhotoBooth",
        "hotspot_password": "photos123",
        "web_port": 8080,
        "onedrive_enabled": false
    },
    "storage": {
        "photo_directory": "/home/pi/photos",
        "session_directory": "/home/pi/sessions"
    }
}
```

## Usage

1. Start the photo booth software
2. The live preview will be displayed on the touchscreen
3. Press the trigger button or touch the screen to start a session
4. The LED ring will show a countdown before each photo
5. Take multiple photos as desired
6. Press "Done" or "Export" when finished
7. Scan the QR code with your phone to:
   - Connect to the WiFi hotspot
   - Download photos via the web interface
   - Or access photos via OneDrive link

### Manual Trigger (Development Mode)

If you don't have the hardware trigger button and countdown LEDs yet, you can use the manual trigger script:

```bash
# Activate virtual environment first
source venv/bin/activate

# Single capture with countdown
python3 scripts/trigger_capture.py

# Loop mode - keep capturing on Enter key press
python3 scripts/trigger_capture.py --loop

# Demo mode (no actual camera required)
python3 scripts/trigger_capture.py --demo

# Custom output directory and countdown
python3 scripts/trigger_capture.py --output ~/my_photos --countdown 5

# Debug mode for troubleshooting
python3 scripts/trigger_capture.py --debug
```

The manual trigger provides:
- Terminal-based countdown display
- Support for both single and loop (continuous) capture modes
- Demo mode for testing without camera hardware
- Custom output directory and countdown settings

## Hardware Controller Protocol

The Arduino controller communicates via serial (115200 baud):

### Commands from Arduino to Raspberry Pi:
- `TRIGGER` - Button pressed, start capture sequence
- `READY` - Controller is ready

### Commands from Raspberry Pi to Arduino:
- `LED:COUNTDOWN:n` - Start countdown animation (n seconds)
- `LED:FLASH` - Trigger flash
- `LED:OFF` - Turn off LEDs
- `LED:IDLE` - Idle animation

## Project Structure

```
Open-Imagebox/
├── src/
│   ├── main.py              # Main application entry
│   ├── camera/              # Camera communication (gPhoto2)
│   ├── controller/          # Arduino serial controller
│   ├── ui/                  # PyQt5 touchscreen UI
│   ├── web/                 # Web server for photo download
│   ├── sharing/             # QR code, hotspot, OneDrive
│   └── utils/               # Utility functions
├── arduino/
│   └── controller/          # Arduino firmware
├── settings/
│   ├── config.example.json  # Example configuration
│   └── config.json          # User configuration
├── scripts/
│   ├── install.sh           # Installation script
│   ├── setup_hotspot.sh     # WiFi hotspot setup
│   └── trigger_capture.py   # Manual capture trigger (development)
├── docs/                    # Documentation
└── requirements.txt         # Python dependencies
```

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE)

## Credits

Inspired by the [self-o-mat project](https://github.com/xtech/self-o-mat).
