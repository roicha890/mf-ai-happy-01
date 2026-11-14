#!/usr/bin/env python3
"""make.fun ai-happy-01 entry: cheerful scene (sun, rainbow, puppies) to /output/entry.png.

Pure Python standard library only (no Pillow): a small framebuffer renders the
scene and writes the PNG bytes directly with zlib + struct. Deterministic.
"""
import math
import os
import struct
import zlib

W = H = 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


class FB:
    """A tiny RGB framebuffer with primitive shape fills and PNG export."""

    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w = w
        self.h = h
        self.px = [list(bg) for _ in range(w * h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = list(c)

    def fill_rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, int(y0)), min(self.h, int(y1))):
            for x in range(max(0, int(x0)), min(self.w, int(x1))):
                self.set(x, y, c)

    def fill_ellipse(self, cx, cy, rx, ry, c):
        cx = int(cx)
        cy = int(cy)
        rx = max(1, int(rx))
        ry = max(1, int(ry))
        for y in range(cy - ry, cy + ry + 1):
            if not (0 <= y < self.h):
                continue
            dy = (y - cy) / ry
            span = rx * math.sqrt(max(0.0, 1.0 - dy * dy))
            x0 = max(0, int(cx - span))
            x1 = min(self.w, int(cx + span) + 1)
            base = y * self.w
            for x in range(x0, x1):
                self.px[base + x] = list(c)

    def thick_line(self, x0, y0, x1, y1, width, c):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(1, width // 2)
        for i in range(steps + 1):
            t = i / steps
            self.fill_ellipse(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), r, r, c)

    def arc(self, cx, cy, r, a0deg, a1deg, width, c, steps=None):
        steps = steps or max(int(abs(a1deg - a0deg) * r / 2), 24)
        rr = max(1, width // 2)
        a0 = math.radians(a0deg)
        a1 = math.radians(a1deg)
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.fill_ellipse(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), rr, rr, c)

    def arc_band(self, cx, cy, r_out, r_in, a0deg, a1deg, c):
        """Filled annular band between two radii over an angle range (rainbow)."""
        a0 = math.radians(a0deg)
        a1 = math.radians(a1deg)
        y0 = int(cy - r_out if a0deg <= 270 else cy)
        for y in range(max(0, cy - r_out), min(self.h, cy + 1)):
            dy = y - cy
            row = y * self.w
            half = math.sqrt(max(0.0, r_out * r_out - dy * dy))
            for x in range(max(0, int(cx - half)), min(self.w, int(cx + half) + 1)):
                dx = x - cx
                d = math.sqrt(dx * dx + dy * dy)
                if r_in <= d <= r_out:
                    ang = math.degrees(math.atan2(dy, dx)) % 360
                    if 180 <= ang <= 360:
                        self.px[row + x] = list(c)

    def polygon(self, pts, c):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(max(0, int(min(ys))), min(self.h, int(max(ys)) + 1)):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if y1 == y2:
                    continue
                if min(y1, y2) <= y + 0.5 < max(y1, y2):
                    xs.append(x1 + (y + 0.5 - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(max(0, int(xs[i])), min(self.w, int(xs[i + 1]) + 1)):
                    self.set(x, y, c)

    def radial_glow(self, cx, cy, r, color, strength):
        """Alpha-blended glow disc fading with distance."""
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dy2 = (y - cy) * (y - cy)
            row = y * self.w
            for x in range(max(0, cx - r), min(self.w, cx + r + 1)):
                d2 = (x - cx) * (x - cx) + dy2
                if d2 > r * r:
                    continue
                a = strength * (1.0 - math.sqrt(d2) / r)
                if a <= 0:
                    continue
                base = self.px[row + x]
                self.px[row + x] = [
                    min(255, int(base[k] + (color[k] - base[k]) * a)) for k in range(3)
                ]

    def save_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)  # filter type 0
            for (r, g, b) in self.px[y * self.w:(y + 1) * self.w]:
                raw += bytes((r, g, b))
        comp = zlib.compress(bytes(raw), 9)

        def chunk(tag, data):
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", comp)
        png += chunk(b"IEND", b"")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(png)


def build():
    fb = FB(W, H, (120, 200, 250))

    # smooth sky gradient (vertical interpolation, no banding)
    top, bot = (96, 170, 245), (170, 222, 252)
    for y in range(0, 900):
        t = y / 900
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        row = y * fb.w
        for x in range(fb.w):
            fb.px[row + x] = list(c)

    # sun with layered glow
    for (r, s) in [(200, 0.20), (150, 0.30), (110, 0.35)]:
        fb.radial_glow(870, 150, r, (255, 240, 160), s)
    fb.fill_ellipse(870, 150, 92, 92, (255, 220, 90))
    fb.fill_ellipse(870, 150, 78, 78, (255, 236, 130))

    # rainbow: 6 colour bands as annular sectors over the top half
    colors = [(255, 80, 80), (255, 170, 60), (255, 240, 80),
              (110, 220, 110), (90, 160, 255), (150, 90, 230)]
    for i, c in enumerate(colors):
        r_out = 470 - i * 24
        fb.arc_band(512, 470, r_out, r_out - 24, 180, 360, c)

    # clouds: clusters of soft white ellipses with a pale under-shade
    def cloud(cx, cy, s):
        for (ox, oy, rr, col) in [
            (0, 0, 62, (255, 255, 255)), (52, -8, 46, (255, 255, 255)),
            (-52, -8, 46, (255, 255, 255)), (24, -30, 42, (250, 252, 255)),
            (0, 26, 48, (226, 234, 246)),
        ]:
            fb.fill_ellipse(cx + ox * s, cy + oy * s, rr * s, rr * s * 0.8, col)
    cloud(160, 300, 1.0)
    cloud(430, 190, 0.8)
    cloud(770, 380, 0.9)

    # grass: two big ground ellipses, light over dark
    fb.fill_ellipse(512, 1180, 700, 260, (108, 196, 108))
    fb.fill_ellipse(512, 1200, 700, 260, (132, 216, 122))

    # puppies: simple happy dogs
    def puppy(px, py, s, body=(200, 140, 80)):
        fb.fill_ellipse(px + 10 * s, py + 20 * s, 84 * s, 52 * s, body)          # body
        fb.fill_ellipse(px - 42 * s, py - 46 * s, 56 * s, 50 * s, body)          # head
        fb.fill_ellipse(px - 92 * s, py - 74 * s, 22 * s, 34 * s, (150, 95, 50))  # ears
        fb.fill_ellipse(px - 18 * s, py - 82 * s, 22 * s, 34 * s, (150, 95, 50))
        fb.arc(int(px - 62 * s), int(py - 66 * s), int(12 * s), 200, 340, max(4, int(5 * s)), (40, 25, 15))  # happy eyes
        fb.arc(int(px - 30 * s), int(py - 68 * s), int(12 * s), 200, 340, max(4, int(5 * s)), (40, 25, 15))
        fb.fill_ellipse(px - 50 * s, py - 50 * s, 8 * s, 6 * s, (50, 30, 20))    # nose
        fb.arc(int(px - 50 * s), int(py - 40 * s), int(18 * s), 20, 160, max(4, int(5 * s)), (50, 30, 20))   # smile
        fb.fill_ellipse(px - 52 * s, py - 26 * s, 9 * s, 14 * s, (240, 110, 120))  # tongue
        fb.arc(int(px + 86 * s), int(py + 8 * s), int(30 * s), 220, 340, max(6, int(12 * s)), body)          # tail
        fb.fill_ellipse(px + 10 * s, py + 66 * s, 30 * s, 12 * s, (160, 106, 58))  # paw shade
    puppy(370, 890, 1.2)
    puppy(710, 910, 0.9, body=(235, 225, 215))

    # hearts: two circles + triangle, layered highlight
    def heart(hx, hy, s, c=(255, 90, 120)):
        fb.polygon([(hx, hy + 22 * s), (hx - 24 * s, hy - 2 * s), (hx + 24 * s, hy - 2 * s)], c)
        fb.fill_ellipse(hx - 12 * s, hy - 8 * s, 13 * s, 12 * s, c)
        fb.fill_ellipse(hx + 12 * s, hy - 8 * s, 13 * s, 12 * s, c)
        fb.fill_ellipse(hx - 8 * s, hy - 12 * s, 5 * s, 4 * s, (255, 160, 180))
    heart(240, 480, 1.6)
    heart(560, 420, 1.0)
    heart(660, 530, 0.8)

    # flowers on grass: 6 petals + centre, with tiny stem
    for (fx, fy, fc) in [(120, 950, (255, 150, 200)), (300, 968, (255, 240, 120)),
                         (820, 958, (200, 150, 255)), (940, 938, (255, 150, 200))]:
        fb.thick_line(fx, fy, fx, fy + 26, 4, (90, 160, 90))
        for a in range(6):
            ang = a * math.pi / 3
            fb.fill_ellipse(fx + 15 * math.cos(ang), fy + 15 * math.sin(ang), 9, 9, fc)
        fb.fill_ellipse(fx, fy, 8, 8, (255, 220, 100))

    return fb


def main():
    out = os.path.join(OUT, "entry.png")
    fb = build()
    fb.save_png(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
