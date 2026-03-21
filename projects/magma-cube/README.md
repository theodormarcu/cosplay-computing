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
5V  ──────────>     VCC
GND ──────────>     GND
```

> Add a 100 uF electrolytic capacitor across VCC/GND on the ring to absorb current spikes.

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

## Dependencies

- **Core:** `arduino:esp32` (v2.0.18-arduino.5+)
- **Library:** [FastLED](https://github.com/FastLED/FastLED) (v3.10+)
