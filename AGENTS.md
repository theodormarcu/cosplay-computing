# Cosplay Computing - Project Notes

## Toolchain

- **arduino-cli** (installed via Homebrew)
- ESP32 core: `arduino:esp32` (FQBN for Nano ESP32: `arduino:esp32:nano_nora`)
- Library: FastLED

## Build Commands

```bash
# Compile a project (from its sketch directory)
arduino-cli compile --fqbn arduino:esp32:nano_nora .

# Upload
arduino-cli upload --fqbn arduino:esp32:nano_nora -p /dev/cu.usbmodem* .
```

## Project Structure

```
cosplay-computing/
  projects/
    magma-cube/    # 7-LED WS2812B fire animation on Nano ESP32
    ledtest/       # Diagnostic: static R/G/B/W per-pixel pattern + heartbeat
    d2test/        # Diagnostic: slow D2 toggle to verify data pin w/ multimeter
```

## Hardware Notes (Nano ESP32 + WS2812B)

Learned the hard way wiring the magma-cube ring:

- **No 5V pin on the Nano ESP32.** 5V is only on **VBUS** (USB power only). All GPIOs
  are **3.3V logic**. Probing a "5V" pin and seeing ~3.3V means you're on `3V3`.
- **3.3V data into a 5V-powered WS2812B is marginal** (needs ~0.7×VDD ≈ 3.7V high).
  Fix: power the ring from **`3V3`** (reliable, slightly dimmer) OR use `VBUS` + a
  logic-level shifter (74AHCT125) for full 5V brightness.
- **WS2812B needs a mechanically SOLID data connection.** A whole frame must arrive in
  one clean burst; an intermittent/hand-held joint shows garbage or nothing, never a
  clean pattern that flickers in. Use Dupont jumpers on the headers or solder — don't
  try to hold the data wire by hand.
- Data goes to the ring's **DIN** side (follow PCB arrows), through a **~330Ω** series
  resistor (standard, not "too much").
- Sketches blink the **onboard LED ~1 Hz as a heartbeat** to separate board issues from
  ring/wiring issues.

## Flashing

Upload is over USB-C via DFU and is independent of the LED wiring, so you can re-flash
while debugging hardware. Port has been e.g. `/dev/cu.usbmodem206EF13116F02`.
