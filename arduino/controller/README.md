# Open-Imagebox Controller Firmware

Arduino firmware for the photo booth hardware controller.

## Hardware Requirements

- Arduino Nano (or compatible ATmega328 board)
- WS2812B LED Ring (24 LEDs recommended)
- Push button for trigger
- Optional: External flash trigger output

## Wiring

| Component | Arduino Pin |
|-----------|-------------|
| Trigger Button | D2 (with internal pullup) |
| LED Ring Data | D6 |
| Flash Output | D9 |
| Button GND | GND |
| LED Ring VCC | 5V |
| LED Ring GND | GND |

## Dependencies

Install via Arduino Library Manager:

- **Adafruit NeoPixel** (for WS2812B LED control)

## Installation

1. Install the Arduino IDE
2. Install the Adafruit NeoPixel library
3. Open `controller.ino`
4. Select your board (Arduino Nano)
5. Select the correct port
6. Upload the sketch

Or using arduino-cli:

```bash
arduino-cli lib install "Adafruit NeoPixel"
arduino-cli compile -b arduino:avr:nano controller.ino
arduino-cli upload -p /dev/ttyUSB0 -b arduino:avr:nano controller.ino
```

## Serial Protocol

Communication uses 115200 baud serial.

### Commands FROM Raspberry Pi TO Arduino:

| Command | Description |
|---------|-------------|
| `LED:COUNTDOWN:n` | Start n-second countdown animation |
| `LED:FLASH` | Trigger flash effect |
| `LED:OFF` | Turn off all LEDs |
| `LED:IDLE` | Show idle breathing animation |
| `LED:BRIGHTNESS:n` | Set brightness (0-255) |

### Messages FROM Arduino TO Raspberry Pi:

| Message | Description |
|---------|-------------|
| `TRIGGER` | Button was pressed |
| `READY` | Controller is initialized and ready |
| `ACK:*` | Acknowledgment of received command |

## Customization

Edit the following defines in `controller.ino`:

```cpp
#define NUM_PIXELS      24    // Number of LEDs in ring
#define TRIGGER_PIN     2     // Button input pin
#define LED_PIN         6     // NeoPixel data pin
```

## Colors

Default colors can be modified in the `setup()` function:

```cpp
colorCountdown = strip.Color(255, 165, 0);  // Orange
colorFlash = strip.Color(255, 255, 255);     // White
colorIdle = strip.Color(0, 100, 255);        // Blue
```
