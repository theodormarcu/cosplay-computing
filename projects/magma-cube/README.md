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
D2  ──[330R]──>     DIN
3V3 ──────────>     VCC   (see Power note)
GND ──────────>     GND
```

> Add a 100 uF electrolytic capacitor across VCC/GND on the ring to absorb current spikes.
> Connect data to the **DIN** side of the ring (follow the arrows etched on the PCB), not DOUT.

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

```bash
# Compile
arduino-cli compile --fqbn arduino:esp32:nano_nora .

# Upload (replace PORT with your serial port, e.g. /dev/cu.usbmodem*)
arduino-cli upload --fqbn arduino:esp32:nano_nora -p PORT .
```

## Tuning

Edit these `#define` values in `magma-cube.ino`:

| Define | Default | Description |
|--------|---------|-------------|
| `COOLING` | 80 | How fast heat dissipates (higher = faster cool) |
| `SPARKING` | 160 | Chance of new sparks per frame (0-255) |
| `BRIGHTNESS` | 180 | Overall LED brightness (keep under 200 for USB power) |
| `DATA_PIN` | D2 | GPIO pin connected to ring DIN |

## Troubleshooting

The onboard LED blinks ~1 Hz as a **"sketch is running" heartbeat** — use it to tell
board problems apart from ring/wiring problems.

| Symptom | Likely cause / fix |
|---------|--------------------|
| Ring dark, onboard LED **blinking** | Sketch is fine → it's the data/power/wiring. Check below. |
| Ring dark, onboard LED **not blinking** | Sketch not running → re-flash, press RESET. |
| Ring measures ~3.3V but stays dark | Almost always a **loose/intermittent data connection at D2**. WS2812B needs a *solid* connection — a clean full frame must arrive in one burst, so a flaky joint shows nothing or garbage, never a clean pattern. Use Dupont jumpers on the headers or solder. |
| One stuck color / random colors | Garbage latched from a marginal/noisy data line — same fix as above. |
| Whole ring dark on 5V power | 3.3V data into 5V LEDs is marginal → power from `3V3` instead (see Power note). |
| Probing reads ~3V on a "5V" pin | There is no 5V pin; you're reading `3V3`. Use `VBUS` for 5V. |

Diagnostic sketches live alongside this project:
- `../ledtest/` — static R/G/B/W per-pixel pattern + heartbeat (verifies chain & color order).
- `../d2test/` — slowly toggles D2 so you can confirm the data pin with a multimeter.

Quick multimeter checks:
- **Power:** DC volts, black on ring GND, red on ring VCC → expect ~3.3V (on `3V3`).
- **Common ground:** continuity between board GND and ring GND → must beep.
- **Data path:** continuity D2 → DIN → ~330Ω (through the resistor).

## Dependencies

- **Core:** `arduino:esp32` (v2.0.18-arduino.5+)
- **Library:** [FastLED](https://github.com/FastLED/FastLED) (v3.10+)
