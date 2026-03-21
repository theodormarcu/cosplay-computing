// magma-cube.ino
// Flaming / magma animation for a 7-LED WS2812B ring (DIYmall 7-bit)
// Running on Arduino Nano ESP32 (ABX00083 / arduino:esp32:nano_nora)
//
// Wiring:
//   Ring DIN  -> GPIO D2 (default DATA_PIN below)
//   Ring VCC  -> 5 V
//   Ring GND  -> GND
//   (A 300-470 ohm resistor on DIN and a 100 uF cap across VCC/GND recommended)

#include <FastLED.h>

// ── Hardware config ─────────────────────────────────────────────────
#define DATA_PIN    D2
#define NUM_LEDS    7
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  180       // 0-255, keep under 200 for USB power

// ── Fire tuning ─────────────────────────────────────────────────────
#define COOLING     35        // How quickly the heat cools down (higher = faster)
#define SPARKING    80        // Chance (out of 255) of a new spark each frame
#define FRAMES_PER_SECOND 40

CRGB leds[NUM_LEDS];
byte heat[NUM_LEDS];          // Per-pixel heat value

// Custom lava/magma palette: deep red -> orange -> bright yellow-white
DEFINE_GRADIENT_PALETTE(magma_gp) {
    0,     0,   0,   0,    // black (cool)
   64,   180,   0,   0,    // deep red
  128,   255,  80,   0,    // orange
  200,   255, 200,  40,    // yellow
  255,   255, 255, 180     // near-white (hottest)
};

CRGBPalette16 magmaPalette = magma_gp;

// ─────────────────────────────────────────────────────────────────────
void setup() {
  delay(1000);                // power-on safety delay
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS)
         .setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(BRIGHTNESS);
}

// ─────────────────────────────────────────────────────────────────────
void loop() {
  fire();
  FastLED.show();
  FastLED.delay(1000 / FRAMES_PER_SECOND);
}

// Adapted Fire2012 for a tiny 7-pixel ring
void fire() {
  // 1) Cool each cell a little
  for (int i = 0; i < NUM_LEDS; i++) {
    heat[i] = qsub8(heat[i], random8(0, ((COOLING * 10) / NUM_LEDS) + 2));
  }

  // 2) Heat drifts "inward" toward the center of the ring
  //    On a small ring we just average neighbours so heat spreads outward
  //    from random spark points, giving a molten glow.
  for (int i = NUM_LEDS - 1; i >= 2; i--) {
    heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) / 3;
  }

  // 3) Randomly ignite new sparks near the bottom / random positions
  if (random8() < SPARKING) {
    int pos = random8(3);           // spark in first few pixels
    heat[pos] = qadd8(heat[pos], random8(100, 180));
  }
  // Extra: occasional spark anywhere on the ring for magma bubbling effect
  if (random8() < SPARKING / 4) {
    int pos = random8(NUM_LEDS);
    heat[pos] = qadd8(heat[pos], random8(60, 140));
  }

  // 4) Map heat to palette colours
  for (int i = 0; i < NUM_LEDS; i++) {
    byte colorIndex = scale8(heat[i], 240);
    leds[i] = ColorFromPalette(magmaPalette, colorIndex);
  }
}
