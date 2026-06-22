# Magma Cube

Flaming / magma lava animation for a **7-LED WS2812B ring** driven by an **Arduino Nano ESP32**.

## Hardware

| Part | Details |
|------|---------|
| MCU  | Arduino Nano ESP32 (ABX00083) -- ESP32-S3, USB-C |
| LEDs | DIYmall 7-Bit WS2812B RGB LED Ring (7 x WS2812B 5050) |

## Wiring

```
Nano ESP32          WS2812B Ring
──────────          ────────────
D3  ──[330R]──>     DIN
3V3 ──────────>     VCC   (see Power note)
GND ──────────>     GND
```

> The 330R resistor is optional (spike protection); it works without it.
> Add a 100 uF electrolytic capacitor across VCC/GND on the ring to absorb current spikes.
> Connect data to the **DIN** side of the ring (follow the arrows etched on the PCB), not DOUT.
> Solder the data wire into the ring's DIN hole — a Dupont pin merely *resting* in the
> through-hole beeps on a continuity meter but won't reliably carry the 800 kHz data.

### Pin numbering (CRITICAL — read this first)

The Nano ESP32 must be compiled with **Pin Numbering = "By GPIO number (legacy)"**
(`PinNumbers=byGPIONumber`). This is baked into `sketch.yaml`.

In the **default** "By Arduino pin" mode, libraries that drive pins directly via the
RMT peripheral (**FastLED, Adafruit NeoPixel**) send the LED data out the **wrong
physical GPIO** — so the ring stays completely dark even though everything is wired
correctly and `digitalWrite()` on the same pin works fine. This single setting cost
hours of debugging. With legacy mode, the `D3` label resolves to the real GPIO and
the libraries output on the correct pin.

### Power note (important)

The Arduino Nano ESP32 **has no 5V pin** — 5V is only available on **VBUS** (and only
when powered over USB-C). The board's GPIOs are **3.3V logic**.

A WS2812B powered at 5V expects a data "high" of ~0.7 × VDD (~3.7V), so a 3.3V data
signal is **marginal** and the ring may not light reliably. Two options:

- **Simple (used here): power the ring from `3V3`.** This lowers the LED's logic
  threshold so the 3.3V data is read reliably. Slightly dimmer, but rock-solid for 7 LEDs.
- **Full brightness: power from `VBUS` (5V)** and add a **logic-level shifter**
  (e.g. 74AHCT125) to bump the data line from 3.3V → 5V.

## Building & Uploading

Requires `arduino-cli` with the `arduino:esp32` core and `FastLED` library installed.

`sketch.yaml` sets the correct FQBN (including `PinNumbers=byGPIONumber`), so the
plain commands work:

```bash
# Compile
arduino-cli compile .

# Upload (replace PORT with your serial port, e.g. /dev/cu.usbmodem*)
arduino-cli upload -p PORT .
```

If you pass `--fqbn` explicitly, you MUST include the pin-numbering option or the ring
will stay dark:

```bash
arduino-cli compile --fqbn "arduino:esp32:nano_nora:PinNumbers=byGPIONumber" .
arduino-cli upload  --fqbn "arduino:esp32:nano_nora:PinNumbers=byGPIONumber" -p PORT .
```

## Tuning

Edit these `#define` values in `magma-cube.ino`:

| Define | Default | Description |
|--------|---------|-------------|
| `COOLING` | 70 | How fast heat dissipates (higher = more contrast/flicker, more dramatic) |
| `SPARKING` | 70* | Chance of new sparks per frame, 0-255 (higher = busier, fewer dark lulls) |
| `FRAMES_PER_SECOND` | 15 | Overall animation speed (lower = slower motion) |
| `BRIGHTNESS` | 180 | Overall LED brightness (keep under 200 for USB power) |
| `DATA_PIN` | D3 | Pin connected to ring DIN |

The palette is **red-dominant**: most of the heat range glows red, with orange/yellow
only on the hottest spark tips (no white — it reads "cold"). Edit `magma_gp` to retune.

### Ring-size variants

Same effect, different `NUM_LEDS` (and `SPARKING`* scaled to ring size). Flash the one
matching your ring:

| Project | LEDs | `SPARKING` |
|---------|------|------------|
| `magma-cube/` (this) | 7 | 70 |
| `../magma-ring-12/` | 12 | 105 |
| `../magma-ring-16/` | 16 | 140 |

## Troubleshooting

The onboard LED blinks ~1 Hz as a **"sketch is running" heartbeat** — use it to tell
board problems apart from ring/wiring problems.

| Symptom | Likely cause / fix |
|---------|--------------------|
| **Ring dark, everything wired right, heartbeat blinking, libraries compile/upload fine** | **#1 cause: wrong pin numbering.** Compile with `PinNumbers=byGPIONumber` (in `sketch.yaml`). In default mode FastLED/NeoPixel output on the wrong GPIO. *Tell-tale: a direct 3V3 tap on DIN lights pixels, but the data pin drives nothing.* |
| Ring dark, onboard LED **not blinking** | Sketch not running → re-flash, press RESET. |
| Ring measures ~3.3V but stays dark | Loose/intermittent data connection. A Dupont pin *resting* in the ring's DIN through-hole beeps on a meter but won't carry the 800 kHz signal — **solder it**. WS2812B needs a clean full frame in one burst, so a flaky joint shows nothing or garbage, never a clean pattern. |
| One stuck color / random colors | Garbage latched from a marginal/noisy data line — same fix as above. |
| Whole ring dark on 5V power | 3.3V data into 5V LEDs is marginal → power from `3V3` instead (see Power note). |
| Probing reads ~3V on a "5V" pin | There is no 5V pin; you're reading `3V3`. Use `VBUS` for 5V. |

Diagnostic sketches live alongside this project (compile each with the same
`PinNumbers=byGPIONumber` FQBN):
- `../ledtest/` — static R/G/B/W per-pixel pattern + heartbeat (verifies chain & color order).
- `../neotest/` — same pattern via Adafruit NeoPixel (isolates FastLED vs. library-independent issues).
- `../d2test/` — slowly toggles the data pin so you can confirm it with a multimeter.

Quick multimeter checks:
- **Power:** DC volts, black on ring GND, red on ring VCC → expect ~3.3V (on `3V3`).
- **Common ground:** continuity between board GND and ring GND → must beep.
- **Data path:** continuity D3 → DIN → ~0Ω (or ~330Ω if the optional resistor is fitted).
- **"Is the ring alive?":** briefly tap a `3V3` jumper on the ring's DIN hole — a pixel should flash. Confirms the LEDs work independent of the data signal.

## Dependencies

- **Core:** `arduino:esp32` (v2.0.18-arduino.5+)
- **Library:** [FastLED](https://github.com/FastLED/FastLED) (v3.10+)
- **Library (diagnostics only):** [Adafruit NeoPixel](https://github.com/adafruit/Adafruit_NeoPixel) (used by `../neotest/`)
