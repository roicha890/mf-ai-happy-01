#!/usr/bin/env python3
"""make.fun ai-happy-01 entry: draws a cheerful scene (sun, rainbow, puppies) to /output/entry.png."""
import os, math
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024

def build():
    img = Image.new("RGB", (W, H), (120, 200, 250))
    d = ImageDraw.Draw(img)
    # sky gradient bands
    for i in range(6):
        d.rectangle([0, i*40, W, i*40+40], fill=(120+i*12, 200+i*4, 250-i*6))
    # sun
    d.ellipse([780, 60, 960, 240], fill=(255, 220, 90))
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([750, 30, 990, 270], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), (255, 240, 160)), img, glow)
    d = ImageDraw.Draw(img)
    # rainbow arc
    colors = [(255,80,80),(255,170,60),(255,240,80),(110,220,110),(90,160,255),(150,90,230)]
    for i, c in enumerate(colors):
        r = 460 - i*22
        d.arc([512-r, 240-r, 512+r, 240+r], 180, 360, fill=c, width=22)
    # clouds
    for (cx, cy, s) in [(160, 300, 1.0), (420, 200, 0.8), (760, 380, 0.9)]:
        for (ox, oy, rr) in [(0,0,60),(50,-10,45),(-50,-10,45),(25,-30,40)]:
            d.ellipse([cx+ox-rr*s, cy+oy-rr*s, cx+ox+rr*s, cy+oy+rr*s], fill=(255,255,255))
    # grass
    d.ellipse([-100, 850, W+100, H+300], fill=(110, 200, 110))
    d.ellipse([-100, 880, W+100, H+300], fill=(130, 214, 120))
    # puppies: simple happy dogs
    def puppy(px, py, s, body=(200,140,80)):
        # body
        d.ellipse([px-70*s, py-30*s, px+70*s, py+60*s], fill=body)
        # head
        d.ellipse([px-90*s, py-95*s, px+10*s, py+5*s], fill=body)
        # ears
        d.ellipse([px-100*s, py-100*s, px-60*s, py-40*s], fill=(150,95,50))
        d.ellipse([px-40*s, py-105*s, px+5*s, py-55*s], fill=(150,95,50))
        # eyes happy arcs
        d.arc([px-72*s, py-78*s, px-52*s, py-58*s], 200, 340, fill=(40,25,15), width=6)
        d.arc([px-44*s, py-80*s, px-24*s, py-60*s], 200, 340, fill=(40,25,15), width=6)
        # nose + smile
        d.ellipse([px-60*s, py-58*s, px-48*s, py-46*s], fill=(50,30,20))
        d.arc([px-70*s, py-60*s, px-38*s, py-30*s], 20, 160, fill=(50,30,20), width=5)
        # tail wag
        d.arc([px+60*s, py-40*s, px+120*s, py+30*s], 220, 340, fill=body, width=int(12*s))
        # tongue
        d.ellipse([px-62*s, py-40*s, px-46*s, py-18*s], fill=(240,110,120))
    puppy(360, 880, 1.2)
    puppy(700, 900, 0.9, body=(235,225,215))
    # hearts
    def heart(hx, hy, s, c=(255,90,120)):
        d.polygon([(hx, hy+18*s), (hx-22*s, hy-4*s), (hx+22*s, hy-4*s)], fill=c)
        d.ellipse([hx-22*s, hy-16*s, hx-2*s, hy+2*s], fill=c)
        d.ellipse([hx+2*s, hy-16*s, hx+22*s, hy+2*s], fill=c)
    heart(240, 480, 1.4); heart(560, 420, 1.0); heart(660, 520, 0.8)
    # flowers on grass
    for (fx, fy, fc) in [(120, 940, (255,150,200)), (300, 960, (255,240,120)), (820, 950, (200,150,255)), (940, 930, (255,150,200))]:
        for a in range(6):
            ang = a * math.pi / 3
            ox, oy = 14*math.cos(ang), 14*math.sin(ang)
            d.ellipse([fx+ox-8, fy+oy-8, fx+ox+8, fy+oy+8], fill=fc)
        d.ellipse([fx-8, fy-8, fx+8, fy+8], fill=(255, 220, 100))
    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def main():
    img = build()
    out = os.environ.get("MF_OUT", "/output/entry.png")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print("wrote", out)

if __name__ == "__main__":
    main()
