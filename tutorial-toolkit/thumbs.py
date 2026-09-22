"""Tutorial thumbnails, v2 — sized to what the app actually renders.

Measured off a live screenshot: the image area is 605x413 = 1.465:1, so the
canvas is built at that ratio and nothing is cropped. v1 assumed 1.517, and the
67px cover took off each side sliced the phone in half.

Also fixed from v1: the headline is bigger and vertically CENTRED rather than
hanging off the top, which is what left the dead space at the bottom-left.
The play button still owns the middle — x 636-964 here — so the text column
stops short of it and the phone starts after it.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1600, 1092                      # 1.465:1, the app's real image box
NAVY, DEEP, SKY, YELLOW, WHITE = (26,42,60), (10,16,24), (82,167,204), (250,214,0), (255,255,255)
TEXT_L, TEXT_R = 90, 610               # text column, clear of the play circle
PH_W = 455
LAT = "/System/Library/Fonts/SFCompact.ttf"
ARA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansArabic-Bold.ttf")

def fit(d, words, path, box_w, hi, lo, max_lines):
    for size in range(hi, lo, -4):
        f = ImageFont.truetype(path, size)
        lines, cur = [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= box_w or not cur: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= max_lines and all(d.textlength(l, font=f) <= box_w for l in lines):
            return f, lines
    return ImageFont.truetype(path, lo), [" ".join(words)]

def background(rtl):
    img = Image.new("RGB", (W, H), NAVY)
    # a bright pool of brand blue behind the phone, falling away to near-black
    gx = W - 430 if not rtl else 430
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([gx-620, H//2-760, gx+620, H//2+760], fill=190)
    img = Image.composite(Image.new("RGB",(W,H),SKY), img,
                          glow.filter(ImageFilter.GaussianBlur(230)).point(lambda v:int(v*0.55)))
    far = Image.new("L", (W, H), 0)
    ImageDraw.Draw(far).rectangle([0,0,W,H], fill=255)
    ImageDraw.Draw(far).ellipse([gx-900, H//2-1000, gx+900, H//2+1000], fill=0)
    img = Image.composite(Image.new("RGB",(W,H),DEEP), img,
                          far.filter(ImageFilter.GaussianBlur(260)).point(lambda v:int(v*0.92)))
    return img

def phone(shot, h):
    src = Image.open(shot).convert("RGB")
    w = int(h * src.width / src.height)
    src = src.resize((w, h), Image.LANCZOS)
    bez, r = 10, 46
    body = Image.new("RGBA", (w+bez*2, h+bez*2), (0,0,0,0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0,0,w+bez*2,h+bez*2], radius=r+bez, fill=(52,57,64,255))
    d.rounded_rectangle([0,0,w+bez*2,h+bez*2], radius=r+bez, outline=(138,145,155,255), width=3)
    m = Image.new("L",(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w,h],radius=r,fill=255)
    body.paste(src,(bez,bez),m)
    return body

def build(shot, eyebrow, headline, rtl, out, force_size=None):
    img = background(rtl)
    ph = phone(shot, H - 96)
    px = W - 74 - ph.width if not rtl else 74
    py = (H - ph.height)//2
    sh = Image.new("L",(W,H),0)
    ImageDraw.Draw(sh).rounded_rectangle([px+16,py+20,px+ph.width+16,py+ph.height+20],radius=64,fill=185)
    img = Image.composite(Image.new("RGB",(W,H),(3,7,12)), img, sh.filter(ImageFilter.GaussianBlur(42)))
    img.paste(ph,(px,py),ph)

    d = ImageDraw.Draw(img)
    col = TEXT_R - TEXT_L
    tx = TEXT_L if not rtl else W - TEXT_L
    fp = ARA if rtl else LAT
    anc = "l" if not rtl else "r"

    # A set where every headline is a different size looks accidental. The
    # caller measures all of them first and pins the smallest that works.
    hi = force_size or 150
    f, lines = fit(d, headline.split(), fp, col, hi, 60, 3)
    lh = int(f.size * (1.02 if not rtl else 1.38))
    block = lh*len(lines)
    ey_h, gap = 76, 34
    top = (H - (ey_h + gap + block + 46)) // 2          # whole stack centred

    ef = ImageFont.truetype(fp, 48)
    ew = d.textlength(eyebrow, font=ef)
    ex = tx if not rtl else tx - ew
    d.rounded_rectangle([ex-20, top, ex+ew+20, top+ey_h], radius=12, fill=YELLOW)
    d.text((tx, top+ey_h//2), eyebrow, font=ef, fill=(20,32,46), anchor=f"{anc}m",
           direction="rtl" if rtl else "ltr", language="ar" if rtl else "en")

    y = top + ey_h + gap
    for ln in lines:
        d.text((tx, y), ln, font=f, fill=WHITE, anchor=f"{anc}a",
               direction="rtl" if rtl else "ltr", language="ar" if rtl else "en")
        y += lh
    # Arabic descends well below the Latin baseline, so the rule has to sit
    # lower or it strikes through words like شراء and العرض.
    gy = 22 if not rtl else 54
    bar = [tx-2, y+gy, tx+118, y+gy+12] if not rtl else [tx-118, y+gy, tx+2, y+gy+12]
    d.rounded_rectangle(bar, radius=6, fill=YELLOW)
    img.save(out, "PNG", optimize=True)
