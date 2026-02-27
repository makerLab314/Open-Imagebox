# Hardware-Aufbau

## Benötigte Komponenten

### Grundausstattung

| Komponente | Beschreibung | Beispiel |
|------------|--------------|----------|
| Raspberry Pi | 3B+ oder neuer empfohlen | Raspberry Pi 4 (2GB+) |
| DSLR Kamera | Canon über USB | Canon EOS 600D, 5D Mark III |
| Touchscreen | HDMI Display | 7" oder 10" Touch-Display |
| USB-Kabel | Kamera zu Pi | Mini-USB oder Micro-USB |
| Netzteil | 5V 3A für Pi | Offizielles Pi-Netzteil |

### Controller (Optional, empfohlen)

| Komponente | Beschreibung |
|------------|--------------|
| Arduino Nano | Oder kompatibles Board |
| WS2812B LED-Ring | 24 LEDs empfohlen |
| Arcade-Button | Großer Taster für Auslösung |
| Kabel | Für Verbindungen |

## Verkabelung

### Kamera

```
Kamera USB → Raspberry Pi USB-Port
```

### Display

```
Display HDMI → Raspberry Pi HDMI-Port
Display Touch (USB) → Raspberry Pi USB-Port
Display Stromversorgung → 5V
```

### Arduino Controller

```
Arduino         Raspberry Pi
-------         ------------
TX/RX      →    USB-Port
GND        →    GND
5V         →    5V (oder externe Versorgung)

Arduino         LED-Ring
-------         --------
D6         →    Data In
5V         →    VCC
GND        →    GND

Arduino         Button
-------         ------
D2         →    Button Pin 1
GND        →    Button Pin 2
```

## Schaltplan

```
                    +5V
                     │
                     │
    ┌────────────────┴───────────────┐
    │                                │
    │  ┌──────────────────────┐     │
    │  │    Arduino Nano      │     │
    │  │                      │     │
    │  │ D2 ───┬─────────────┼──── Button ──── GND
    │  │       │             │     │
    │  │       └─ 10kΩ ───── 5V    │
    │  │                      │     │
    │  │ D6 ──────────────────┼──── LED Ring Data
    │  │                      │     │
    │  │ TX/RX ────────────────────── USB to Raspberry Pi
    │  │                      │     │
    │  │ GND ─────────────────┼──── GND
    │  │                      │     │
    │  └──────────────────────┘     │
    │                                │
    │      ┌───────────────┐        │
    │      │   LED Ring    │────────┘
    │      │   WS2812B     │
    │      │    24 LEDs    │
    │      └───────────────┘
    │
    └── LED Ring VCC
```

## Gehäuse-Ideen

### Einfaches Stativ-Setup

1. Kamera auf Stativ
2. Display vor der Kamera montiert
3. LED-Ring um Objektiv
4. Raspberry Pi im Stativfuß

### Fotobox-Gehäuse

1. Holz- oder Kartonbox
2. Öffnung für Kameraobjektiv
3. Display an Vorderseite
4. Button oben oder seitlich
5. LED-Ring um Display oder Objektiv

## Stromversorgung

- Raspberry Pi: 5V 3A Netzteil
- LED-Ring (24 LEDs): Max. 1.5A bei voller Helligkeit
- Arduino: Über USB vom Pi oder separates Netzteil

**Empfehlung:** 5V 4A Netzteil für Pi + LED-Ring
