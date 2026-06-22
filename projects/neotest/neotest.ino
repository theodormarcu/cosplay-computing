// neotest.ino
// Decisive test: drive the 7-LED ring with Adafruit NeoPixel instead of
// FastLED. Different library + code path (no FastLED RMT driver).
//
// If THIS shows the static R/G/B/W pattern but FastLED didn't, the problem
// was FastLED's ESP32-S3 driver, not the hardware.
//
// Wiring: ring DIN -> D3, VCC -> 3V3, GND -> GND.

#include <Adafruit_NeoPixel.h>

#define PIN        D3
#define NUM_LEDS   7
#define BRIGHTNESS 40

Adafruit_NeoPixel strip(NUM_LEDS, PIN, NEO_GRB + NEO_KHZ800);

void setup() {
  delay(1000);
  pinMode(LED_BUILTIN, OUTPUT);

  strip.begin();
  strip.setBrightness(BRIGHTNESS);

  strip.setPixelColor(0, strip.Color(255, 0, 0));     // red
  strip.setPixelColor(1, strip.Color(0, 255, 0));     // green
  strip.setPixelColor(2, strip.Color(0, 0, 255));     // blue
  strip.setPixelColor(3, strip.Color(255, 255, 255)); // white
  strip.setPixelColor(4, strip.Color(255, 0, 0));     // red
  strip.setPixelColor(5, strip.Color(0, 255, 0));     // green
  strip.setPixelColor(6, strip.Color(0, 0, 255));     // blue
  strip.show();
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  strip.show();
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  strip.show();
  delay(500);
}
