# Open-Imagebox

Eine vollwertige Photo-Booth-Software für Raspberry Pi, inspiriert vom [self-o-mat Projekt](https://github.com/xtech/self-o-mat).

A fully-featured photo booth software for Raspberry Pi, inspired by the [self-o-mat project](https://github.com/xtech/self-o-mat).

## Features

- **Live Preview** – Echtzeit-Kameravorschau auf HDMI-Display / Real-time camera preview on HDMI display
- **DSLR-Kamerasteuerung** – Canon-Kameras per USB via gPhoto2 / Canon cameras via USB using gPhoto2
- **Hardware-Controller** – Arduino-basierter Trigger-Button, LED-Countdown-Ring, Blitz-Synchronisation
- **Multi-Foto-Sessions** – Mehrere Fotos pro Session aufnehmen
- **QR-Code Export** – Fotos per WiFi-Hotspot und QR-Code aufs Handy laden
- **Web-Galerie** – Fotos im Browser ansehen und als ZIP herunterladen
- **OneDrive-Upload** – Optionaler Cloud-Upload mit teilbarem QR-Code

## Hardware

### Benötigt / Required
- Raspberry Pi 3B+ (oder neuer / or newer)
- Canon DSLR Kamera (USB-Verbindung / USB connected)
- HDMI Display (Touchscreen empfohlen / recommended)

### Optional
- Arduino Nano (für Hardware-Controller / for hardware controller)
- LED Ring Light (WS2812B/NeoPixel)
- Taster / Push Button
- Externer Blitz / External Flash

## Installation

### Schnellinstallation / Quick Install (Raspberry Pi OS)

```bash
# Repository klonen / Clone repository
git clone https://github.com/makerLab314/Open-Imagebox.git
cd Open-Imagebox

# Installationsskript ausführen / Run install script
bash scripts/install.sh
```

Das Installationsskript:
- Installiert alle Systemabhängigkeiten
- Erstellt eine Python Virtual Environment
- Stoppt gPhoto2-Hintergrundprozesse (die die Kamera blockieren)
- Richtet den systemd-Service ein (Auto-Start beim Booten)
- Konfiguriert optional den WiFi-Hotspot (auf Raspberry Pi)

The installation script:
- Installs all system dependencies
- Creates a Python virtual environment
- Kills gPhoto2 background processes (that block camera access)
- Sets up the systemd service (auto-start on boot)
- Optionally configures WiFi hotspot (on Raspberry Pi)

### Nach der Installation / After Installation

1. **Kamera anschließen** – DSLR per USB an den Raspberry Pi anschließen und einschalten
2. **Konfiguration anpassen** – `nano settings/config.json` (wird automatisch erstellt)
3. **Starten**:

```bash
# Manuell starten / Start manually
cd Open-Imagebox
source venv/bin/activate
python -m src.main

# Oder als Service / Or as a service
sudo systemctl start open-imagebox

# Status prüfen / Check status
sudo systemctl status open-imagebox

# Logs ansehen / View logs
journalctl -u open-imagebox -f
```

### Manuelle Installation / Manual Installation

Falls das Installationsskript nicht funktioniert:

```bash
# 1. Systemabhängigkeiten
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-pyqt5 \
    gphoto2 libgphoto2-dev \
    hostapd dnsmasq qrencode libzbar0 \
    libjpeg-dev libopenjp2-7 libtiff-dev libatlas-base-dev

# 2. WICHTIG: gPhoto2-Hintergrundprozesse stoppen
sudo pkill -f gvfs-gphoto2-volume-monitor
sudo pkill -f gvfsd-gphoto2

# 3. Virtual Environment erstellen
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Konfiguration
cp settings/config.example.json settings/config.json

# 5. Starten
python -m src.main
```

## Benutzung / Usage

### Ablauf / Workflow
1. **Live-Vorschau** wird auf dem Display angezeigt
2. **Auslösen** – Display berühren, Button drücken, oder Leertaste/Enter
3. **Countdown** – LED-Ring zeigt Countdown, dann wird das Foto aufgenommen
4. **Galerie** – Aufgenommene Fotos ansehen, weitere aufnehmen oder „Fertig"
5. **QR-Code** – Zwei QR-Codes werden angezeigt:
   - **Schritt 1**: WiFi-QR-Code scannen → Handy verbindet sich mit dem Hotspot
   - **Schritt 2**: Download-QR-Code scannen → Fotos im Browser öffnen und herunterladen

### Tastaturkürzel / Keyboard Shortcuts
| Taste / Key | Funktion / Function |
|---|---|
| Leertaste / Space | Foto aufnehmen / Capture photo |
| Enter | Foto aufnehmen / Capture photo |
| Escape | Vollbild verlassen / Exit fullscreen |
| F11 | Vollbild umschalten / Toggle fullscreen |

### Kommandozeilenoptionen / Command Line Options
```bash
python -m src.main              # Normal starten
python -m src.main --windowed   # Im Fenster starten
python -m src.main --debug      # Debug-Modus
python -m src.main --demo       # Demo-Modus (ohne Kamera)
python -m src.main --no-gui     # Headless (nur Web-Server)
python -m src.main -c /pfad/config.json  # Eigene Konfiguration
```

## Konfiguration / Configuration

Bearbeite `settings/config.json`:

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
        "enabled": true,
        "serial_port": "/dev/ttyUSB0",
        "countdown_seconds": 3
    },
    "sharing": {
        "hotspot_enabled": true,
        "hotspot_ssid": "PhotoBooth",
        "hotspot_password": "photos123",
        "web_port": 8080
    },
    "storage": {
        "photo_directory": "~/photos",
        "session_directory": "~/sessions"
    }
}
```

## Fehlerbehebung / Troubleshooting

### Kamera wird nicht erkannt / Camera not detected
```bash
# gPhoto2-Prozesse stoppen
sudo pkill -f gvfs-gphoto2-volume-monitor
sudo pkill -f gvfsd-gphoto2

# Kamera testen
gphoto2 --auto-detect
gphoto2 --summary
```

### Display zeigt kein UI / Display shows no UI
```bash
# Status prüfen
sudo systemctl status open-imagebox

# Manuell starten für Fehlerausgabe
cd Open-Imagebox
source venv/bin/activate
python -m src.main --debug
```

### Service startet nicht / Service won't start
```bash
# Logs prüfen
journalctl -u open-imagebox -n 50

# Service neu laden
sudo systemctl daemon-reload
sudo systemctl restart open-imagebox
```

## Hardware-Controller Protokoll / Protocol

Arduino-Kommunikation über Serial (115200 Baud):

| Richtung / Direction | Befehl / Command | Beschreibung / Description |
|---|---|---|
| Arduino → Pi | `TRIGGER` | Button gedrückt / Button pressed |
| Arduino → Pi | `READY` | Controller bereit / Controller ready |
| Pi → Arduino | `LED:COUNTDOWN:n` | Countdown-Animation (n Sekunden) |
| Pi → Arduino | `LED:FLASH` | Blitz auslösen / Trigger flash |
| Pi → Arduino | `LED:OFF` | LEDs aus / LEDs off |
| Pi → Arduino | `LED:IDLE` | Idle-Animation |

## Projektstruktur / Project Structure

```
Open-Imagebox/
├── src/
│   ├── main.py              # Hauptprogramm / Main entry point
│   ├── camera/              # Kamera-Steuerung / Camera control (gPhoto2)
│   ├── controller/          # Hardware-Controller (Arduino)
│   ├── ui/                  # PyQt5 Display-UI
│   ├── web/                 # Web-Server für Foto-Download
│   ├── sharing/             # QR-Code, Hotspot, OneDrive
│   └── utils/               # Konfiguration, Logging
├── scripts/
│   ├── install.sh           # Installationsskript
│   ├── setup_hotspot.sh     # WiFi-Hotspot-Setup
│   └── trigger_capture.py   # Manueller Auslöser (Entwicklung)
├── settings/
│   ├── config.example.json  # Beispiel-Konfiguration
│   └── config.json          # Benutzerkonfiguration (erstellt bei Installation)
├── docs/                    # Dokumentation
└── requirements.txt         # Python-Abhängigkeiten
```

## Lizenz / License

GNU General Public License v3.0 – siehe [LICENSE](LICENSE)

## Credits

Inspiriert vom [self-o-mat Projekt](https://github.com/xtech/self-o-mat) von [xtech](https://github.com/xtech).
