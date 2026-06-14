#!/usr/bin/env python3
"""
Magma Cube 3D Visualizer
Renders the 7-LED WS2812B ring fire animation in 3D using pygame + OpenGL.

All tuning constants and the colour palette are parsed from magma-cube.ino.

Controls:
  Click+drag   - orbit camera
  Scroll       - zoom in/out
  UP/DOWN      - adjust COOLING
  LEFT/RIGHT   - adjust SPARKING
  B/D          - brightness up/down
  R            - reset fire
  Q/ESC        - quit
"""

import os
import re
import sys
import math
import random

import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# ── Parse the .ino sketch ────────────────────────────────────────────
SKETCH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "magma-cube.ino")


def _parse_defines(path: str) -> dict[str, int]:
    defines: dict[str, int] = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"^\s*#define\s+(\w+)\s+(\d+)", line)
            if m:
                defines[m.group(1)] = int(m.group(2))
    return defines


def _parse_palette(path: str) -> list[tuple[int, tuple[int, int, int]]]:
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

FPS = 60
SMOOTH_FACTOR = 0.15

PALETTE_STOPS = _palette if _palette else [
    (0,   (0,   0,   0)),
    (64,  (180, 0,   0)),
    (128, (255, 80,  0)),
    (200, (255, 200, 40)),
    (255, (255, 255, 180)),
]

# ── Fire sim (same as 2D version) ────────────────────────────────────

def palette_color(index: int) -> tuple[int, int, int]:
    index = max(0, min(255, index))
    for i in range(len(PALETTE_STOPS) - 1):
        pos_a, col_a = PALETTE_STOPS[i]
        pos_b, col_b = PALETTE_STOPS[i + 1]
        if index <= pos_b:
            t = (index - pos_a) / max(1, pos_b - pos_a)
            return tuple(int(a + (b - a) * t) for a, b in zip(col_a, col_b))
    return PALETTE_STOPS[-1][1]


def qadd8(a, b): return min(255, a + b)
def qsub8(a, b): return max(0, a - b)
def scale8(v, s): return (v * s) >> 8


class FireSim:
    def __init__(self):
        self.heat = [0] * NUM_LEDS
        self.cooling = COOLING
        self.sparking = SPARKING
        self.brightness = BRIGHTNESS
        self.display = [(0.0, 0.0, 0.0)] * NUM_LEDS

    def step(self):
        for i in range(NUM_LEDS):
            cool = random.randint(0, ((self.cooling * 10) // NUM_LEDS) + 2)
            self.heat[i] = qsub8(self.heat[i], cool)
        for i in range(NUM_LEDS - 1, 1, -1):
            self.heat[i] = (self.heat[i - 1] + self.heat[i - 2] + self.heat[i - 2]) // 3
        if random.randint(0, 255) < self.sparking:
            pos = random.randint(0, 2)
            self.heat[pos] = qadd8(self.heat[pos], random.randint(100, 180))
        if random.randint(0, 255) < self.sparking // 4:
            pos = random.randint(0, NUM_LEDS - 1)
            self.heat[pos] = qadd8(self.heat[pos], random.randint(60, 140))

    def colors(self) -> list[tuple[float, float, float]]:
        raw = []
        br = self.brightness / 255.0
        for h in self.heat:
            idx = scale8(h, 240)
            r, g, b = palette_color(idx)
            raw.append((r * br / 255.0, g * br / 255.0, b * br / 255.0))
        k = SMOOTH_FACTOR
        smoothed = []
        for i, (tr, tg, tb) in enumerate(raw):
            pr, pg, pb = self.display[i]
            nr = pr + k * (tr - pr)
            ng = pg + k * (tg - pg)
            nb = pb + k * (tb - pb)
            self.display[i] = (nr, ng, nb)
            smoothed.append((nr, ng, nb))
        return smoothed


# ── 3D geometry helpers ──────────────────────────────────────────────

def make_sphere_verts(radius: float, slices: int = 16, stacks: int = 12):
    """Generate vertices and normals for a UV sphere as triangle strips."""
    verts = []
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + i / stacks)
        lat1 = math.pi * (-0.5 + (i + 1) / stacks)
        z0, zr0 = math.sin(lat0), math.cos(lat0)
        z1, zr1 = math.sin(lat1), math.cos(lat1)
        strip = []
        for j in range(slices + 1):
            lng = 2 * math.pi * j / slices
            x, y = math.cos(lng), math.sin(lng)
            strip.append((x * zr1 * radius, y * zr1 * radius, z1 * radius,
                          x * zr1, y * zr1, z1))
            strip.append((x * zr0 * radius, y * zr0 * radius, z0 * radius,
                          x * zr0, y * zr0, z0))
        verts.append(strip)
    return verts


def draw_sphere(sphere_verts):
    for strip in sphere_verts:
        glBegin(GL_TRIANGLE_STRIP)
        for x, y, z, nx, ny, nz in strip:
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()


def make_torus_verts(major_r: float, minor_r: float, rings: int = 48, sides: int = 24):
    """Generate a torus as triangle strips."""
    strips = []
    for i in range(rings):
        theta0 = 2 * math.pi * i / rings
        theta1 = 2 * math.pi * (i + 1) / rings
        strip = []
        for j in range(sides + 1):
            phi = 2 * math.pi * j / sides
            for theta in (theta1, theta0):
                ct, st = math.cos(theta), math.sin(theta)
                cp, sp = math.cos(phi), math.sin(phi)
                x = (major_r + minor_r * cp) * ct
                y = (major_r + minor_r * cp) * st
                z = minor_r * sp
                nx = cp * ct
                ny = cp * st
                nz = sp
                strip.append((x, y, z, nx, ny, nz))
        strips.append(strip)
    return strips


def draw_torus(torus_verts):
    for strip in torus_verts:
        glBegin(GL_TRIANGLE_STRIP)
        for x, y, z, nx, ny, nz in strip:
            glNormal3f(nx, ny, nz)
            glVertex3f(x, y, z)
        glEnd()


# ── Main ─────────────────────────────────────────────────────────────

def main():
    pygame.init()
    W, H = 800, 600
    pygame.display.set_mode((W, H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Magma Cube 3D - 7 LED Fire Visualizer")
    clock = pygame.time.Clock()

    # OpenGL setup
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glShadeModel(GL_SMOOTH)
    glClearColor(0.02, 0.01, 0.01, 1.0)

    # Dim ambient, moderate directional light
    glLightfv(GL_LIGHT0, GL_POSITION, (2.0, 3.0, 5.0, 0.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.15, 0.08, 0.05, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.4, 0.3, 0.25, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.2, 0.15, 0.1, 1.0))

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, W / H, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    # Pre-build geometry
    RING_R = 2.0        # ring major radius
    RING_TUBE = 0.15    # ring tube thickness
    LED_R = 0.28        # LED sphere radius
    GLOW_R = 0.55       # glow sphere radius

    torus_geo = make_torus_verts(RING_R, RING_TUBE)
    led_geo = make_sphere_verts(LED_R, 14, 10)
    glow_geo = make_sphere_verts(GLOW_R, 12, 8)

    # LED positions on the ring
    led_positions = []
    for i in range(NUM_LEDS):
        angle = 2 * math.pi * i / NUM_LEDS
        x = RING_R * math.cos(angle)
        y = RING_R * math.sin(angle)
        led_positions.append((x, y, 0.0))

    # Camera orbit state
    cam_dist = 7.0
    cam_pitch = 25.0   # degrees
    cam_yaw = 0.0
    dragging = False
    last_mouse = (0, 0)

    sim = FireSim()
    sim_acc = 0.0
    sim_dt = 1.0 / SIM_HZ

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key in (K_q, K_ESCAPE):
                    running = False
                elif event.key == K_UP:
                    sim.cooling = min(255, sim.cooling + 5)
                elif event.key == K_DOWN:
                    sim.cooling = max(0, sim.cooling - 5)
                elif event.key == K_RIGHT:
                    sim.sparking = min(255, sim.sparking + 5)
                elif event.key == K_LEFT:
                    sim.sparking = max(0, sim.sparking - 5)
                elif event.key == K_b:
                    sim.brightness = min(255, sim.brightness + 10)
                elif event.key == K_d:
                    sim.brightness = max(0, sim.brightness - 10)
                elif event.key == K_r:
                    sim.__init__()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse = event.pos
                elif event.button == 4:
                    cam_dist = max(3.0, cam_dist - 0.5)
                elif event.button == 5:
                    cam_dist = min(20.0, cam_dist + 0.5)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == MOUSEMOTION and dragging:
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                cam_yaw += dx * 0.4
                cam_pitch = max(-89, min(89, cam_pitch + dy * 0.4))
                last_mouse = event.pos

        # Fire sim tick
        dt = clock.get_time() / 1000.0
        sim_acc += dt
        while sim_acc >= sim_dt:
            sim.step()
            sim_acc -= sim_dt
        colors = sim.colors()

        # ── Render ────────────────────────────────────────────────
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera
        rad_pitch = math.radians(cam_pitch)
        rad_yaw = math.radians(cam_yaw)
        eye_x = cam_dist * math.cos(rad_pitch) * math.sin(rad_yaw)
        eye_y = cam_dist * math.cos(rad_pitch) * math.cos(rad_yaw)
        eye_z = cam_dist * math.sin(rad_pitch)
        gluLookAt(eye_x, eye_y, eye_z, 0, 0, 0, 0, 0, 1)

        # Draw PCB ring (dark green)
        glColor4f(0.05, 0.12, 0.05, 1.0)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (0.05, 0.12, 0.05, 1.0))
        glMaterialfv(GL_FRONT, GL_SPECULAR, (0.1, 0.1, 0.1, 1.0))
        glMaterialf(GL_FRONT, GL_SHININESS, 20.0)
        draw_torus(torus_geo)

        # Draw each LED
        for i, (px, py, pz) in enumerate(led_positions):
            r, g, b = colors[i]

            # Outer glow (additive-ish, semi-transparent)
            glDepthMask(GL_FALSE)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # additive blend for glow
            glow_alpha = max(r, g, b) * 0.6
            glColor4f(r, g, b, glow_alpha)
            glMaterialfv(GL_FRONT, GL_EMISSION, (r * 0.8, g * 0.8, b * 0.8, 1.0))
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (r, g, b, glow_alpha))
            glPushMatrix()
            glTranslatef(px, py, pz + RING_TUBE + 0.01)
            draw_sphere(glow_geo)
            glPopMatrix()
            glDepthMask(GL_TRUE)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Solid LED body
            glColor4f(r, g, b, 1.0)
            glMaterialfv(GL_FRONT, GL_EMISSION, (r * 0.9, g * 0.9, b * 0.9, 1.0))
            glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (r, g, b, 1.0))
            glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
            glMaterialf(GL_FRONT, GL_SHININESS, 60.0)
            glPushMatrix()
            glTranslatef(px, py, pz + RING_TUBE + 0.01)
            draw_sphere(led_geo)
            glPopMatrix()

        # Reset emission for next frame
        glMaterialfv(GL_FRONT, GL_EMISSION, (0, 0, 0, 1))

        # HUD overlay (switch to 2D ortho)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, W, 0, H, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Render HUD text via pygame surface -> texture
        font = pygame.font.SysFont("menlo", 14)
        hud_lines = [
            f"COOLING: {sim.cooling}  (UP/DOWN)",
            f"SPARKING: {sim.sparking}  (LEFT/RIGHT)",
            f"BRIGHTNESS: {sim.brightness}  (B/D)",
            f"Drag=orbit  Scroll=zoom  R=reset  Q=quit",
        ]
        y_offset = H - 20
        for line in hud_lines:
            surf = font.render(line, True, (200, 150, 100))
            text_data = pygame.image.tostring(surf, "RGBA", True)
            tw, th = surf.get_size()

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(10, y_offset)
            glTexCoord2f(1, 0); glVertex2f(10 + tw, y_offset)
            glTexCoord2f(1, 1); glVertex2f(10 + tw, y_offset + th)
            glTexCoord2f(0, 1); glVertex2f(10, y_offset + th)
            glEnd()
            glDisable(GL_TEXTURE_2D)
            glDeleteTextures([tex_id])
            y_offset -= 20

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
