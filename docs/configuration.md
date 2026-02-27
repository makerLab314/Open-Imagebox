# Konfiguration

## Konfigurationsdatei

Die Konfiguration erfolgt über `settings/config.json`.

### Beispiel-Konfiguration

```json
{
    "camera": {
        "type": "gphoto2",
        "preview_fps": 15,
        "auto_focus": true
    },
    "display": {
        "fullscreen": true,
        "resolution": [1024, 600]
    },
    "controller": {
        "enabled": true,
        "serial_port": "/dev/ttyUSB0",
        "baud_rate": 115200,
        "countdown_seconds": 3
    },
    "led": {
        "num_pixels": 24,
        "brightness": 255
    },
    "sharing": {
        "hotspot_enabled": true,
        "hotspot_ssid": "PhotoBooth",
        "hotspot_password": "photos123",
        "web_port": 8080,
        "onedrive_enabled": false
    },
    "storage": {
        "session_directory": "/home/pi/sessions"
    }
}
```

## Konfigurationsoptionen

### Kamera

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `type` | Kameratyp (`gphoto2`) | `gphoto2` |
| `preview_fps` | Vorschau-Bildrate | `15` |
| `auto_focus` | Autofokus aktivieren | `true` |

### Display

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `fullscreen` | Vollbildmodus | `true` |
| `resolution` | Auflösung [Breite, Höhe] | `[1024, 600]` |

### Controller

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `enabled` | Controller aktivieren | `true` |
| `serial_port` | Serieller Port | `/dev/ttyUSB0` |
| `baud_rate` | Baudrate | `115200` |
| `countdown_seconds` | Countdown-Dauer | `3` |

### LED

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `num_pixels` | Anzahl LEDs | `24` |
| `brightness` | Helligkeit (0-255) | `255` |
| `countdown_color` | Countdown-Farbe [R,G,B] | `[255,165,0]` |
| `flash_color` | Blitz-Farbe [R,G,B] | `[255,255,255]` |

### Sharing

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `hotspot_enabled` | Hotspot aktivieren | `true` |
| `hotspot_ssid` | WLAN-Name | `PhotoBooth` |
| `hotspot_password` | WLAN-Passwort | `photos123` |
| `web_port` | Web-Server Port | `8080` |
| `onedrive_enabled` | OneDrive-Upload | `false` |
| `onedrive_client_id` | OneDrive App-ID | `""` |

### Speicher

| Option | Beschreibung | Standard |
|--------|--------------|----------|
| `photo_directory` | Foto-Verzeichnis | `/home/pi/photos` |
| `session_directory` | Session-Verzeichnis | `/home/pi/sessions` |
| `jpeg_quality` | JPEG-Qualität | `95` |

## OneDrive-Konfiguration

1. Azure App registrieren unter https://portal.azure.com
2. App-ID in `onedrive_client_id` eintragen
3. `onedrive_enabled` auf `true` setzen
4. Beim ersten Start wird eine Authentifizierung durchgeführt

## Kommandozeilen-Optionen

```bash
python -m src.main [Optionen]

Optionen:
  -c, --config PATH   Konfigurationsdatei
  --no-gui            Headless-Modus
  --debug             Debug-Logging
  --windowed          Fenster-Modus
```
