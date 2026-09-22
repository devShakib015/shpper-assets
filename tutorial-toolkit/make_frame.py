#!/usr/bin/env python3
"""Build overlay.png — the dark background and iPhone bezel the videos sit in.

    python3 make_frame.py           # rebuild overlay.png
    python3 make_frame.py --check   # print the screen hole's real position

The overlay is one image: opaque everywhere except a transparent screen-shaped
hole. The video goes underneath and the frame on top, so the recording's square
corners cannot poke past the phone's rounded ones.

⚠️ If you change the geometry here, change SCREEN_* in render_videos.py to
match. `--check` reads the hole's real position back out of the PNG's alpha
channel — trust that over the arithmetic.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay.png")
W, H = 1080, 1920
SRC_W, SRC_H = 1320, 2868          # iPhone Pro Max simulator capture
SCREEN_H = 1740
SCREEN_W = int(round(SCREEN_H * (SRC_W / SRC_H) / 2) * 2)
BEZEL = 14
BODY_W, BODY_H = SCREEN_W + BEZEL * 2, SCREEN_H + BEZEL * 2
BODY_X, BODY_Y = (W - BODY_W) // 2, (H - BODY_H) // 2
SX, SY = BODY_X + BEZEL, BODY_Y + BEZEL
R_BODY, R_SCREEN = 96, 84
NAVY, DEEP, SKY = (31, 48, 67), (12, 19, 27), (82, 167, 204)
TITANIUM, EDGE = (58, 62, 68), (120, 126, 134)


def check():
    a = Image.open(OUT).convert("RGBA").getchannel("A")
    box = a.point(lambda v: 255 if v < 8 else 0).getbbox()
    print(f"  hole: x={box[0]} y={box[1]}  {box[2]-box[0]}x{box[3]-box[1]}")
    print(f"  render_videos.py must use SCREEN_X={box[0]} SCREEN_Y={box[1]} "
          f"SCREEN_W={box[2]-box[0]} SCREEN_H={box[3]-box[1]}")


def build():
    img = Image.new("RGB", (W, H), NAVY)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([W // 2 - 620, H // 2 - 820, W // 2 + 620, H // 2 + 820], fill=120)
    img = Image.composite(Image.new("RGB", (W, H), SKY), img,
                          glow.filter(ImageFilter.GaussianBlur(220)).point(lambda v: int(v * 0.40)))
    vig = Image.new("L", (W, H), 255)
    ImageDraw.Draw(vig).rounded_rectangle([-260, -260, W + 260, H + 260], radius=600, fill=0)
    img = Image.composite(Image.new("RGB", (W, H), DEEP), img,
                          vig.filter(ImageFilter.GaussianBlur(180)).point(lambda v: int(v * 0.85)))

    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle(
        [BODY_X, BODY_Y + 18, BODY_X + BODY_W, BODY_Y + BODY_H + 18], radius=R_BODY, fill=170)
    img = Image.composite(Image.new("RGB", (W, H), (6, 11, 17)), img,
                          shadow.filter(ImageFilter.GaussianBlur(44)))

    d = ImageDraw.Draw(img)
    d.rounded_rectangle([BODY_X, BODY_Y, BODY_X + BODY_W, BODY_Y + BODY_H], radius=R_BODY, fill=TITANIUM)
    d.rounded_rectangle([BODY_X, BODY_Y, BODY_X + BODY_W, BODY_Y + BODY_H], radius=R_BODY,
                        outline=EDGE, width=3)

    overlay = img.convert("RGBA")
    hole = Image.new("L", (W, H), 255)
    # -1 on each far edge: PIL's rectangle includes BOTH endpoints, so
    # [SX, SX+SCREEN_W] is SCREEN_W+1 pixels wide and leaves a 1px seam of
    # background down the side of the video. `--check` reads the truth back.
    ImageDraw.Draw(hole).rounded_rectangle(
        [SX, SY, SX + SCREEN_W - 1, SY + SCREEN_H - 1], radius=R_SCREEN, fill=0)
    overlay.putalpha(hole)
    overlay.save(OUT)
    print(f"  wrote {OUT}")
    check()


if __name__ == "__main__":
    check() if "--check" in sys.argv else build()
