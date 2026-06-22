// ledtest.ino
// Diagnostic sketch for the 7-LED WS2812B ring on Arduino Nano ESP32.
// Lights each LED a known, distinct color at low brightness so we can
// verify: data chain integrity, color order, and per-pixel health.
//
// Expected (if COLOR_ORDER is correct):
//   LED0 = RED, LED1 = GREEN, LED2 = BLUE, LED3 = WHITE,
//   LED4 = RED, LED5 = GREEN, LED6 = BLUE
//
// Wiring (same as magma-cube):
//   Ring DIN -> D3, VCC -> 3V3, GND -> GND
//   Compile with PinNumbers=byGPIONumber (see sketch.yaml) or the ring stays dark.

#include <FastLED.h>

#define DATA_PIN    D3
#define NUM_LEDS    7
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  40        // low: easy on eyes + low current at 3V3

CRGB leds[NUM_LEDS];

void setup() {
  delay(1000);
  pinMode(LED_BUILTIN, OUTPUT);   // onboard LED = "sketch is running" heartbeat

  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS)
         .setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(BRIGHTNESS);

  leds[0] = CRGB::Red;
  leds[1] = CRGB::Green;
  leds[2] = CRGB::Blue;
  leds[3] = CRGB::White;
  leds[4] = CRGB::Red;
  leds[5] = CRGB::Green;
  leds[6] = CRGB::Blue;
  FastLED.show();
}

void loop() {
  // Heartbeat: if the onboard LED blinks ~1 Hz, the sketch is definitely
  // running and driving D2. Then any ring problem is data/pixel-side.
  digitalWrite(LED_BUILTIN, HIGH);
  FastLED.show();
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  FastLED.show();
  delay(500);
}
