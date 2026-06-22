// magma-cube.ino
// Flaming / magma animation for a 7-LED WS2812B ring (DIYmall 7-bit)
// Running on Arduino Nano ESP32 (ABX00083 / arduino:esp32:nano_nora)
//
// Wiring:
//   Ring DIN  -> GPIO D2 (default DATA_PIN below), through a 330R resistor
//   Ring VCC  -> 3V3   (see power note below)
//   Ring GND  -> GND
//   (A 100 uF cap across the ring's VCC/GND is also recommended)
//
// Power note (Arduino Nano ESP32):
//   This board has NO 5V pin. 5V is only on VBUS (USB power). The GPIOs
//   are 3.3V logic, and a WS2812B powered at 5V wants a data "high" of
//   ~0.7*VDD (~3.7V), so a 3.3V signal is marginal and the ring may not
//   light. Powering the ring from 3V3 drops that threshold so the 3.3V
//   data is read reliably (slightly dimmer). For full 5V brightness use
//   VBUS plus a logic-level shifter (e.g. 74AHCT125) on the data line.
//
//   The onboard LED blinks ~1 Hz as a "sketch is running" heartbeat.

#include <FastLED.h>

// ── Hardware config ─────────────────────────────────────────────────
#define DATA_PIN    D3
#define NUM_LEDS    7
#define LED_TYPE    WS2812B
#define COLOR_ORDER GRB
#define BRIGHTNESS  180       // 0-255, keep under 200 for USB power

// ── Fire tuning ─────────────────────────────────────────────────────
#define COOLING     22        // How quickly the heat cools down (lower = slower, more sustained glow)
#define SPARKING    110       // Chance (out of 255) of a new spark each frame (higher = fewer dark lulls)
#define FRAMES_PER_SECOND 30  // Overall animation speed (lower = slower motion)

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
  pinMode(LED_BUILTIN, OUTPUT);   // onboard LED = "sketch is running" heartbeat
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS)
         .setCorrection(TypicalLEDStrip);
  FastLED.setBrightness(BRIGHTNESS);
}

// ─────────────────────────────────────────────────────────────────────
void loop() {
  fire();
  FastLED.show();

  // Heartbeat: blink the onboard LED ~1 Hz so we can always tell the
  // sketch is running, independent of the ring.
  static uint8_t frame = 0;
  if (++frame >= FRAMES_PER_SECOND / 2) {
    frame = 0;
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

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
