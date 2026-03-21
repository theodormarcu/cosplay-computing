#!/usr/bin/env python3
"""
Magma Cube Visualizer
Simulates the WS2812B 7-LED ring fire animation from magma-cube.ino
using pygame so you can preview the effect without hardware.

All tuning constants and the colour palette are parsed directly from
the .ino file at startup so there is a single source of truth.

Controls:
  UP/DOWN   - adjust COOLING
  LEFT/RIGHT- adjust SPARKING
  B/D       - brightness up/down
  R         - reset
  Q/ESC     - quit
"""

import os
import re
import sys
import math
import random

import pygame

# ── Parse the .ino sketch for defines & palette ──────────────────────
SKETCH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magma-cube.ino")


def _parse_defines(path: str) -> dict[str, int]:
    """Extract all #define NAME <integer> from the sketch."""
    defines: dict[str, int] = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^\s*#define\s+(\w+)\s+(\d+)", line)
            if m:
                defines[m.group(1)] = int(m.group(2))
    return defines


def _parse_palette(path: str) -> list[tuple[int, tuple[int, int, int]]]:
    """Extract DEFINE_GRADIENT_PALETTE stops from the sketch.

    Expects rows like:  <pos>, <r>, <g>, <b>,  // comment
    inside a DEFINE_GRADIENT_PALETTE block.
    """
    stops: list[tuple[int, tuple[int, int, int]]] = []
    in_palette = False
    with open(path) as f:
        for line in f:
            if "DEFINE_GRADIENT_PALETTE" in line:
                in_palette = True
                continue
            if in_palette:
                if "};" in line:
                    break
                nums = re.findall(r"\d+", line)
                if len(nums) >= 4:
                    pos, r, g, b = (int(x) for x in nums[:4])
                    stops.append((pos, (r, g, b)))
    return stops


_defs = _parse_defines(SKETCH_PATH)
_palette = _parse_palette(SKETCH_PATH)

NUM_LEDS   = _defs.get("NUM_LEDS", 7)
COOLING    = _defs.get("COOLING", 35)
SPARKING   = _defs.get("SPARKING", 80)
BRIGHTNESS = _defs.get("BRIGHTNESS", 180)
SIM_HZ     = _defs.get("FRAMES_PER_SECOND", 40)

# Visualizer-only settings (not in .ino)
FPS = 60
SMOOTH_FACTOR = 0.15  # exponential smoothing (0 = frozen, 1 = no smoothing)

# ── Window ────────────────────────────────────────────────────────────
WIN_SIZE = 500
RING_RADIUS = 130
LED_RADIUS = 28
CENTER = (WIN_SIZE // 2, WIN_SIZE // 2)

PALETTE_STOPS = _palette if _palette else [
    (0,   (0,   0,   0)),
    (64,  (180, 0,   0)),
    (128, (255, 80,  0)),
    (200, (255, 200, 40)),
    (255, (255, 255, 180)),
]


def palette_color(index: int) -> tuple[int, int, int]:
    """Interpolate the magma gradient palette at 0-255 index."""
    index = max(0, min(255, index))
    for i in range(len(PALETTE_STOPS) - 1):
        pos_a, col_a = PALETTE_STOPS[i]
        pos_b, col_b = PALETTE_STOPS[i + 1]
        if index <= pos_b:
            t = (index - pos_a) / max(1, pos_b - pos_a)
            return tuple(int(a + (b - a) * t) for a, b in zip(col_a, col_b))
    return PALETTE_STOPS[-1][1]


def qadd8(a: int, b: int) -> int:
    return min(255, a + b)


def qsub8(a: int, b: int) -> int:
    return max(0, a - b)


def scale8(val: int, scale: int) -> int:
    return (val * scale) >> 8


class FireSim:
    def __init__(self):
        self.heat = [0] * NUM_LEDS
        self.cooling = COOLING
        self.sparking = SPARKING
        self.brightness = BRIGHTNESS
        self.display = [(0.0, 0.0, 0.0)] * NUM_LEDS  # smoothed RGB floats

    def step(self):
        # 1) Cool each cell
        for i in range(NUM_LEDS):
            cool = random.randint(0, ((self.cooling * 10) // NUM_LEDS) + 2)
            self.heat[i] = qsub8(self.heat[i], cool)

        # 2) Heat drifts inward
        for i in range(NUM_LEDS - 1, 1, -1):
            self.heat[i] = (self.heat[i - 1] + self.heat[i - 2] + self.heat[i - 2]) // 3

        # 3) Random sparks near bottom
        if random.randint(0, 255) < self.sparking:
            pos = random.randint(0, 2)
            self.heat[pos] = qadd8(self.heat[pos], random.randint(100, 180))

        # Extra bubbling spark (rarer)
        if random.randint(0, 255) < self.sparking // 4:
            pos = random.randint(0, NUM_LEDS - 1)
            self.heat[pos] = qadd8(self.heat[pos], random.randint(60, 140))

    def colors(self) -> list[tuple[int, int, int]]:
        raw = []
        br = self.brightness / 255.0
        for h in self.heat:
            idx = scale8(h, 240)
            r, g, b = palette_color(idx)
            raw.append((r * br, g * br, b * br))

        # Exponential smoothing toward raw target
        k = SMOOTH_FACTOR
        smoothed = []
        for i, (tr, tg, tb) in enumerate(raw):
            pr, pg, pb = self.display[i]
            nr = pr + k * (tr - pr)
            ng = pg + k * (tg - pg)
            nb = pb + k * (tb - pb)
            self.display[i] = (nr, ng, nb)
            smoothed.append((int(nr), int(ng), int(nb)))
        return smoothed


def led_positions(n: int, cx: int, cy: int, radius: int) -> list[tuple[int, int]]:
    """Evenly space n LEDs in a circle."""
    return [
        (int(cx + radius * math.cos(2 * math.pi * i / n - math.pi / 2)),
         int(cy + radius * math.sin(2 * math.pi * i / n - math.pi / 2)))
        for i in range(n)
    ]


def draw_glow(surface: pygame.Surface, cx: int, cy: int, color: tuple, radius: int):
    """Draw a soft glowing circle for one LED."""
    for r in range(radius * 3, 0, -1):
        alpha = max(0, min(255, int(255 * (1 - (r / (radius * 3))) ** 1.5)))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        c = (*[min(255, int(ch * 1.1)) for ch in color], alpha)
        pygame.draw.circle(s, c, (r, r), r)
        surface.blit(s, (cx - r, cy - r))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_SIZE, WIN_SIZE))
    pygame.display.set_caption("Magma Cube - 7 LED Fire Visualizer")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("menlo", 14)

    sim = FireSim()
    positions = led_positions(NUM_LEDS, *CENTER, RING_RADIUS)
    sim_accumulator = 0.0
    sim_interval = 1.0 / SIM_HZ

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_UP:
                    sim.cooling = min(255, sim.cooling + 5)
                elif event.key == pygame.K_DOWN:
                    sim.cooling = max(0, sim.cooling - 5)
                elif event.key == pygame.K_RIGHT:
                    sim.sparking = min(255, sim.sparking + 5)
                elif event.key == pygame.K_LEFT:
                    sim.sparking = max(0, sim.sparking - 5)
                elif event.key == pygame.K_b:
                    sim.brightness = min(255, sim.brightness + 10)
                elif event.key == pygame.K_d:
                    sim.brightness = max(0, sim.brightness - 10)
                elif event.key == pygame.K_r:
                    sim.__init__()

        # Tick the fire sim at SIM_HZ, render smoothed colors every frame
        dt = clock.get_time() / 1000.0
        sim_accumulator += dt
        while sim_accumulator >= sim_interval:
            sim.step()
            sim_accumulator -= sim_interval
        colors = sim.colors()

        # Dark background
        screen.fill((10, 5, 5))

        # Draw ring outline
        pygame.draw.circle(screen, (30, 15, 10), CENTER, RING_RADIUS, 2)

        # Draw each LED with glow
        for (px, py), color in zip(positions, colors):
            draw_glow(screen, px, py, color, LED_RADIUS)
            pygame.draw.circle(screen, color, (px, py), LED_RADIUS)
            pygame.draw.circle(screen, tuple(min(255, c + 40) for c in color), (px, py), LED_RADIUS, 1)

        # HUD
        hud_lines = [
            f"COOLING: {sim.cooling}  (UP/DOWN)",
            f"SPARKING: {sim.sparking}  (LEFT/RIGHT)",
            f"BRIGHTNESS: {sim.brightness}  (B/D)",
            f"R=reset  Q=quit",
        ]
        for i, line in enumerate(hud_lines):
            txt = font.render(line, True, (160, 120, 80))
            screen.blit(txt, (12, 10 + i * 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
