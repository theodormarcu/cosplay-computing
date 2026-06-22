// d2test.ino
// Pin-mapping proof for the Arduino Nano ESP32.
// Slowly toggles the physical data pin (0.5s HIGH / 0.5s LOW) so it can be
// verified with a multimeter on DC volts (pin -> GND).
//
// Expected: the pin swings 0V <-> ~3.3V once per second.
// The onboard LED blinks in the OPPOSITE phase as a visual reference.
//
// NOTE: digitalWrite() works regardless of pin-numbering mode, so this test
// passing does NOT prove FastLED/NeoPixel will work — those need
// PinNumbers=byGPIONumber to hit the right GPIO. (That was the real bug.)
// Compile with the same FQBN as the other sketches (see sketch.yaml).

#define DATA_PIN D3

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
