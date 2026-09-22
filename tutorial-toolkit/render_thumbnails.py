#!/usr/bin/env python3
"""Build the tutorial thumbnails.

    python3 render_thumbnails.py <frames-dir> [output-dir]

`frames-dir` holds one still per video, named like the video —
`create_request_en.png`, `create_request_ar.png`. Pull them straight out of the
recordings, picking a frame that shows a real screen rather than a modal:

    ffmpeg -ss 25 -i create_request_en.mp4 -frames:v 1 frames/create_request_en.png

Edit HEADLINES below to add or reword a topic. The app draws the full title
under the card, so the artwork carries a SHORT headline, not the sentence.
"""
import os
import sys

from PIL import Image, ImageDraw
from thumbs import build, fit, LAT, ARA, TEXT_L, TEXT_R

# slug -> (english headline, arabic headline)
HEADLINES = {
    "create_request":    ("PLACE AN ORDER",      "تقديم طلب شراء"),
    "create_hp_request": ("HIGH PRIORITY ORDER", "طلب بأولوية عالية"),
    "book_traveler":     ("BOOK A TRAVELER",     "حجز متسوق شخصي"),
    "accept_offer":      ("ACCEPT AN OFFER",     "قبول العرض"),
    "join_as_traveler":  ("JOIN AS A TRAVELER",  "الانضمام كمتسوق"),
    "plan_trip":         ("POST YOUR TRIP",      "تسجيل خطط سفرك"),
    "discover_request":  ("FIND REQUESTS",       "اكتشف الطلبات"),
}
EYEBROW = {"en": "HOW TO", "ar": "كيفية"}
MAX_LINES = 3


def pinned_sizes():
    """One type size per language, so the set looks like a set.

    Pinning to the largest that fits in TWO lines shrank every headline to suit
    the longest one (66px). Allowing three lines keeps them at 96px and lets the
    long ones wrap instead.
    """
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    col = TEXT_R - TEXT_L
    sizes = {}
    for lang, path, idx in (("en", LAT, 0), ("ar", ARA, 1)):
        best = 132
        for pair in HEADLINES.values():
            f, _ = fit(probe, pair[idx].split(), path, col, 132, 60, MAX_LINES)
            best = min(best, f.size)
        sizes[lang] = best
    return sizes


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    frames = os.path.expanduser(sys.argv[1])
    out = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(frames, "thumbnails")
    os.makedirs(out, exist_ok=True)

    sizes = pinned_sizes()
    print(f"headline size — en {sizes['en']}px, ar {sizes['ar']}px\nout: {out}\n")
    missing = []
    for slug, (en, ar) in HEADLINES.items():
        for lang, headline in (("en", en), ("ar", ar)):
            shot = os.path.join(frames, f"{slug}_{lang}.png")
            if not os.path.exists(shot):
                missing.append(os.path.basename(shot))
                continue
            dst = os.path.join(out, f"{slug}_{lang}.png")
            build(shot, EYEBROW[lang], headline, lang == "ar", dst, force_size=sizes[lang])
            print(f"  {slug}_{lang:2}  {os.path.getsize(dst)/1024:6.0f} KB")
    if missing:
        print("\n  no frame for: " + ", ".join(missing))

    print("\n  Check them the way the app draws them — 605x413, BoxFit.cover,")
    print("  and a play button dead centre. If a headline touches that circle,")
    print("  narrow TEXT_R in thumbs.py.")


if __name__ == "__main__":
    main()
