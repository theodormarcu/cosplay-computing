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
```
