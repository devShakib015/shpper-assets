# Tutorial toolkit

Everything needed to make another set of Shpper how-to videos. Built
2026-09-23 while producing `tutorials_v2/`.

```
brew install ffmpeg            # the only dependency beyond Python + Pillow

python3 render_videos.py     ~/Desktop/cuts        # frame + music
python3 render_thumbnails.py ~/Desktop/frames      # thumbnails
```

---

## The whole run, in order

**1. Record against staging, never production.** `shpper_app/staging/staging.sh`
brings up a fake backend with a made-up cast, so no real customer appears in a
video. `staging/reset-data.sh` puts the data back between takes in about a
second, without signing the app out.

Record on the **iPhone Pro Max simulator** at 1320x2868.

> **Turn on QuickTime's _Show Mouse Clicks in Recording_ if you ever want hand
> or tap indicators.** The simulator's own recorder captures the screen only —
> no pointer, no touch marker — so taps cannot be recovered afterwards. Four
> different detection approaches were tried on the first set and the best got
> three positions right out of nine. Capture it at record time or not at all.

**2. Cut the videos yourself, before anything else.** Music laid over an uncut
timeline jumps at every splice, so trimming has to come first. `find_idle.py`
lists the stretches where nothing moves, if you want to see what is worth
cutting:

```
python3 find_idle.py ~/Desktop/cuts/*.mp4
```

There is an automatic version of this — capping every pause at a fixed length —
but at 0.7s the owner's verdict was *"fast forwarded a lot"*. If you resurrect
it, 2–3s trims only the long freezes and leaves the pacing alone.

**3. Render.** `render_videos.py` composites each cut into the dark iPhone
frame, normalises to a constant 30fps, lays the music from `music/` underneath
with fades, and encodes small. The first set went from 936 MB to 77 MB, which
is the difference between something that streams on mobile data and something
that does not.

**4. Thumbnails.** Pull one still per video, then:

```
ffmpeg -ss 25 -i create_request_en.mp4 -frames:v 1 frames/create_request_en.png
python3 render_thumbnails.py ~/Desktop/frames
```

Pick a frame showing a real screen — a modal dialog makes a poor hero image.

**5. Publish.** Drop the `.mp4` and `.png` files into a new folder here, push,
then point the app at them with
`shpper_app/cloud_functions/ops/set_tutorials.mjs` (dry-run by default;
`--apply` backs up, verifies every URL, writes one field, and reads it back).

---

## Things that cost time the first go

**Every video reported 1:52.** The music file carries a metadata stream, and
even with an explicit `-map`, it rode into the output as a third `bin_data`
stream claiming the *track's* length. Players take the longest stream, so a 31s
video showed 1:52 in QuickTime, VLC and Finder. `ffprobe -show_entries
format=duration` said 31.7s and so did both real streams — the check passed
three times while it was plainly wrong on screen.

> Verify with `mdls -name kMDItemDurationSeconds`, which is what players
> actually read, and list **all** streams, not just video and audio.
> `-dn -sn -map_metadata -1` in `render_videos.py` is what prevents it.

**The frame offset must match the overlay exactly.** `SCREEN_X/Y` in
`render_videos.py` is the position of the transparent hole in `overlay.png`.
Padding to the phone *body's* origin instead put the picture 14px high — the
top hidden under the bezel, a dark strip and a cut-off nav bar at the bottom.
`python3 make_frame.py --check` reads the hole's real position out of the alpha
channel; trust that over arithmetic.

**Measure the thumbnail box, don't infer it.** `childAspectRatio: 1.2` is the
*card*. The image area is what is left above the title strip: **605x413, so
1.465:1**, measured off a screenshot of the running app. Deriving it from the
widget tree gave 1.517, and the 67px `BoxFit.cover` takes off each side sliced
the phone in half.

**The app paints a 40pt play button dead centre, over the artwork.** In the
thumbnail's own pixels that is roughly x 636–964. Anything there gets covered —
the original set read "PLACE ⏵N ORDER" on every card. `thumbs.py` keeps the
text column left of it and the phone right of it.

**Replacing a file at the same URL does not reach devices that cached it.**
`CachedNetworkImage` holds thumbnails for about 30 days. Change the filename or
clear app storage when testing.

**Arabic**: Pillow needs `raqm` for shaping and joining — check with
`python3 -c "from PIL import features; print(features.check('raqm'))"`. Arabic
also descends further than Latin, so the accent rule needs extra clearance or
it strikes through words like شراء.

---

## What's here

| | |
|---|---|
| `render_videos.py` | raw cuts → framed, scored, compressed |
| `render_thumbnails.py` | stills → thumbnails; edit `HEADLINES` to add a topic |
| `thumbs.py` | the thumbnail layout itself |
| `make_frame.py` | rebuilds `overlay.png`; `--check` prints the screen hole |
| `find_idle.py` | lists the dead air in a recording |
| `overlay.png` | the dark background and bezel, 1080x1920 |
| `NotoSansArabic-Bold.ttf` | the app's own Arabic face, so thumbnails match |
| `music/` | the bed used on `tutorials_v2` |

Latin type is `SF Compact Black` from the system. The palette is Shpper's:
navy `#1F3043`, sky `#52A7CC`, yellow `#FAD600`. No green — that is a standing
rule for the whole product.
