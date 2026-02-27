# Dokumentation

Detaillierte Dokumentation für Open-Imagebox.

## Inhaltsverzeichnis

1. [Hardware-Aufbau](hardware.md)
2. [Software-Installation](installation.md)
3. [Konfiguration](configuration.md)
4. [Fehlerbehebung](troubleshooting.md)

## Schnellstart

### Voraussetzungen

- Raspberry Pi 3B+ oder neuer
- Canon DSLR Kamera (getestet mit EOS 600D, 5D Mark III)
- HDMI Touchscreen Display
- Optional: Arduino Nano + LED-Ring für Controller

### Installation

```bash
git clone https://github.com/makerLab314/Open-Imagebox.git
cd Open-Imagebox
./scripts/install.sh
```

### Kamera verbinden

1. Kamera per USB an den Raspberry Pi anschließen
2. Kamera einschalten
3. Software starten: `python -m src.main`

### Fotos aufnehmen

1. Touchscreen berühren oder Button drücken
2. Countdown-Animation auf LED-Ring
3. Foto wird aufgenommen
4. Weitere Fotos aufnehmen oder "Fertig" klicken
5. QR-Code scannen zum Herunterladen

## Architektur

```
Open-Imagebox
├── src/
│   ├── camera/         # Kamera-Kommunikation (gPhoto2)
│   ├── controller/     # Hardware-Controller (Arduino)
│   ├── ui/             # Touchscreen-Oberfläche (PyQt5)
│   ├── web/            # Web-Server für Download
│   └── sharing/        # QR-Codes, Hotspot, OneDrive
├── arduino/            # Arduino-Firmware
└── scripts/            # Installations-Skripte
```

## Danksagung

Inspiriert vom [self-o-mat Projekt](https://github.com/xtech/self-o-mat).
