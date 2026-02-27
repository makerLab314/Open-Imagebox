/*
 * Open-Imagebox Controller Firmware
 * 
 * Arduino-based controller for photo booth hardware.
 * Based on self-o-mat controller design.
 * 
 * Features:
 * - Trigger button input
 * - NeoPixel LED ring for countdown and flash
 * - Serial communication with Raspberry Pi
 * 
 * Hardware:
 * - Arduino Nano or compatible
 * - Push button (connected to TRIGGER_PIN)
 * - WS2812B LED ring (connected to LED_PIN)
 * 
 * Serial Protocol (115200 baud):
 * Commands from Pi:
 *   LED:COUNTDOWN:n  - Start n-second countdown animation
 *   LED:FLASH        - Trigger flash
 *   LED:OFF          - Turn off LEDs
 *   LED:IDLE         - Show idle animation
 *   LED:BRIGHTNESS:n - Set brightness (0-255)
 * 
 * Commands to Pi:
 *   TRIGGER          - Button was pressed
 *   READY            - Controller is ready
 */

#include <Adafruit_NeoPixel.h>

// Pin definitions
#define TRIGGER_PIN     2     // Button input (with internal pullup)
#define LED_PIN         6     // NeoPixel data pin
#define FLASH_PIN       9     // External flash trigger (optional)

// LED ring configuration
#define NUM_PIXELS      24    // Number of LEDs in ring
#define DEFAULT_BRIGHTNESS 255

// Timing
#define DEBOUNCE_MS     50    // Button debounce time
#define SERIAL_BAUD     115200

// Create NeoPixel object
Adafruit_NeoPixel strip(NUM_PIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

// State variables
bool buttonState = HIGH;
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long countdownStartTime = 0;
int countdownSeconds = 0;
bool countdownActive = false;
bool idleActive = false;
int idlePhase = 0;
unsigned long lastIdleUpdate = 0;

// Colors
uint32_t colorOff;
uint32_t colorCountdown;
uint32_t colorFlash;
uint32_t colorIdle;
uint32_t colorReady;

// Serial buffer
String serialBuffer = "";

void setup() {
  // Initialize serial
  Serial.begin(SERIAL_BAUD);
  
  // Initialize pins
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  pinMode(FLASH_PIN, OUTPUT);
  digitalWrite(FLASH_PIN, LOW);
  
  // Initialize NeoPixel strip
  strip.begin();
  strip.setBrightness(DEFAULT_BRIGHTNESS);
  strip.show();
  
  // Define colors
  colorOff = strip.Color(0, 0, 0);
  colorCountdown = strip.Color(255, 165, 0);    // Orange
  colorFlash = strip.Color(255, 255, 255);      // White
  colorIdle = strip.Color(0, 100, 255);         // Blue
  colorReady = strip.Color(0, 255, 0);          // Green
  
  // Show ready state
  showReady();
  
  // Send ready message
  Serial.println("READY");
}

void loop() {
  // Check for serial commands
  handleSerial();
  
  // Handle button input
  handleButton();
  
  // Update animations
  if (countdownActive) {
    updateCountdown();
  } else if (idleActive) {
    updateIdle();
  }
}

void handleSerial() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }
}

void processCommand(String command) {
  command.trim();
  command.toUpperCase();
  
  if (command.startsWith("LED:COUNTDOWN:")) {
    // Extract countdown seconds
    String value = command.substring(14);
    countdownSeconds = value.toInt();
    if (countdownSeconds > 0) {
      startCountdown(countdownSeconds);
      Serial.println("ACK:COUNTDOWN");
    }
  }
  else if (command == "LED:FLASH") {
    triggerFlash();
    Serial.println("ACK:FLASH");
  }
  else if (command == "LED:OFF") {
    ledOff();
    Serial.println("ACK:OFF");
  }
  else if (command == "LED:IDLE") {
    startIdle();
    Serial.println("ACK:IDLE");
  }
  else if (command.startsWith("LED:BRIGHTNESS:")) {
    String value = command.substring(15);
    int brightness = value.toInt();
    brightness = constrain(brightness, 0, 255);
    strip.setBrightness(brightness);
    strip.show();
    Serial.println("ACK:BRIGHTNESS");
  }
}

void handleButton() {
  int reading = digitalRead(TRIGGER_PIN);
  
  // Check for state change
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  // Debounce
  if ((millis() - lastDebounceTime) > DEBOUNCE_MS) {
    if (reading != buttonState) {
      buttonState = reading;
      
      // Trigger on button press (LOW because of pullup)
      if (buttonState == LOW) {
        Serial.println("TRIGGER");
      }
    }
  }
  
  lastButtonState = reading;
}

void startCountdown(int seconds) {
  countdownSeconds = seconds;
  countdownStartTime = millis();
  countdownActive = true;
  idleActive = false;
}

void updateCountdown() {
  unsigned long elapsed = millis() - countdownStartTime;
  unsigned long totalMs = countdownSeconds * 1000UL;
  
  if (elapsed >= totalMs) {
    // Countdown complete
    countdownActive = false;
    return;
  }
  
  // Calculate how many LEDs should be on
  float progress = (float)elapsed / totalMs;
  int ledsOff = (int)(progress * NUM_PIXELS);
  int currentSecond = countdownSeconds - (elapsed / 1000);
  
  // Calculate brightness pulse within each second
  int msInSecond = elapsed % 1000;
  int pulse = 255;
  if (msInSecond < 100) {
    pulse = 255;  // Bright at start of each second
  } else {
    pulse = 150;  // Dimmer during countdown
  }
  
  // Update LEDs
  for (int i = 0; i < NUM_PIXELS; i++) {
    if (i < ledsOff) {
      strip.setPixelColor(i, colorOff);
    } else {
      // Apply pulse brightness
      uint8_t r = (uint8_t)((255 * pulse) / 255);
      uint8_t g = (uint8_t)((165 * pulse) / 255);
      uint8_t b = 0;
      strip.setPixelColor(i, strip.Color(r, g, b));
    }
  }
  strip.show();
}

void triggerFlash() {
  countdownActive = false;
  idleActive = false;
  
  // Full white flash
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.setPixelColor(i, colorFlash);
  }
  strip.show();
  
  // Trigger external flash
  digitalWrite(FLASH_PIN, HIGH);
  delay(100);
  digitalWrite(FLASH_PIN, LOW);
  
  // Keep LEDs on briefly
  delay(100);
  
  // Turn off
  ledOff();
}

void ledOff() {
  countdownActive = false;
  idleActive = false;
  
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.setPixelColor(i, colorOff);
  }
  strip.show();
}

void startIdle() {
  idleActive = true;
  countdownActive = false;
  idlePhase = 0;
  lastIdleUpdate = millis();
}

void updateIdle() {
  // Gentle breathing animation
  unsigned long now = millis();
  
  if (now - lastIdleUpdate < 30) {
    return;  // Update every 30ms
  }
  lastIdleUpdate = now;
  
  idlePhase = (idlePhase + 1) % 256;
  
  // Calculate breathing brightness
  int brightness;
  if (idlePhase < 128) {
    brightness = idlePhase;
  } else {
    brightness = 255 - idlePhase;
  }
  brightness = brightness / 4 + 20;  // Scale to 20-83 range
  
  // Apply to all LEDs with blue color
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.setPixelColor(i, strip.Color(0, brightness / 2, brightness));
  }
  strip.show();
}

void showReady() {
  // Quick green flash to show ready
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.setPixelColor(i, colorReady);
  }
  strip.show();
  delay(500);
  
  // Start idle animation
  startIdle();
}
