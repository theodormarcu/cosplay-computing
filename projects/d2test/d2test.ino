// d2test.ino
// Pin-mapping proof for the Arduino Nano ESP32.
// Slowly toggles the physical D2 pin (0.5s HIGH / 0.5s LOW) so it can be
// verified with a multimeter on DC volts (D2 -> GND).
//
// Expected: D2 swings 0V <-> ~3.3V once per second.
// The onboard LED blinks in the OPPOSITE phase as a visual reference.
//
// Since FastLED's magma sketch drives the LEDs via the same `D2` macro,
// if this pin toggles correctly, the data path uses the correct pin.

#define DATA_PIN D2

void setup() {
  pinMode(DATA_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(DATA_PIN, HIGH);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);
  digitalWrite(DATA_PIN, LOW);
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
}
