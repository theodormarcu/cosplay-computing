# Cosplay Computing - Project Notes

## Toolchain

- **arduino-cli** (installed via Homebrew)
- ESP32 core: `arduino:esp32` (FQBN for Nano ESP32: `arduino:esp32:nano_nora`)
- Libraries: FastLED (main), Adafruit NeoPixel (diagnostics)

## Build Commands

The FQBN **must** include `PinNumbers=byGPIONumber` (see Hardware Notes). Each project's
`sketch.yaml` already sets this, so from a sketch dir the plain commands work:

```bash
# Compile + upload (uses sketch.yaml's FQBN)
arduino-cli compile .
arduino-cli upload -p /dev/cu.usbmodem* .

# If specifying --fqbn explicitly, include the pin-numbering option:
arduino-cli compile --fqbn "arduino:esp32:nano_nora:PinNumbers=byGPIONumber" .
arduino-cli upload  --fqbn "arduino:esp32:nano_nora:PinNumbers=byGPIONumber" -p /dev/cu.usbmodem* .
```

## Project Structure

```
cosplay-computing/
  projects/
    magma-cube/    # 7-LED WS2812B fire animation on Nano ESP32 (data on D3)
    ledtest/       # Diagnostic: static R/G/B/W per-pixel pattern + heartbeat (FastLED)
    neotest/       # Diagnostic: same pattern via Adafruit NeoPixel (library cross-check)
    d2test/        # Diagnostic: slow data-pin toggle to verify the pin w/ multimeter
```

## Hardware Notes (Nano ESP32 + WS2812B)

Learned the hard way wiring the magma-cube ring:

- **PIN NUMBERING IS THE BIG ONE.** Compile with `PinNumbers=byGPIONumber`
  ("By GPIO number (legacy)"). In the default "By Arduino pin" mode, libraries that
  drive pins directly via RMT (**FastLED, Adafruit NeoPixel**) emit the LED data on the
  **wrong physical GPIO**, so the ring stays dark while `digitalWrite()` on the same pin
  works fine. Symptom fingerprint: heartbeat blinks, wiring/power/ground all check out,
  a direct 3V3 tap on DIN lights pixels, but the data pin drives nothing. Cost hours.
- **No 5V pin on the Nano ESP32.** 5V is only on **VBUS** (USB power only). All GPIOs
  are **3.3V logic**. Probing a "5V" pin and seeing ~3.3V means you're on `3V3`.
- **3.3V data into a 5V-powered WS2812B is marginal** (needs ~0.7×VDD ≈ 3.7V high).
  Fix: power the ring from **`3V3`** (reliable, slightly dimmer) OR use `VBUS` + a
  logic-level shifter (74AHCT125) for full 5V brightness.
- **WS2812B needs a mechanically SOLID data connection.** A whole frame must arrive in
  one clean burst; an intermittent joint shows garbage or nothing, never a clean pattern.
  The ring uses **through-holes**: a Dupont pin merely *resting* in the DIN hole beeps on
  a continuity meter but won't carry the 800 kHz data — **solder the data wire in.**
- Data goes to the ring's **DIN** side (follow PCB arrows). A **~330Ω** series resistor
  is optional spike protection (not required, not "too much").
- Sketches blink the **onboard LED ~1 Hz as a heartbeat** to separate board issues from
  ring/wiring issues.

## Flashing

Upload is over USB-C via DFU and is independent of the LED wiring, so you can re-flash
while debugging hardware. Port has been e.g. `/dev/cu.usbmodem206EF13116F02`.
