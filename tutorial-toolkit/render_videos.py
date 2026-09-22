#!/usr/bin/env python3
"""Turn raw simulator screen recordings into finished tutorial videos.

    python3 render_videos.py <input-dir> [output-dir]

Each .mp4 in the input directory is composited into the dark iPhone frame,
normalised to a constant 30fps, given the music bed from ./music, and encoded
small enough to stream on mobile data. 936 MB of raw capture became 77 MB the
first time this ran.

Record at 1320x2868 (iPhone Pro Max simulator). CUT THE VIDEOS FIRST — music
laid over an uncut timeline jumps at every splice, so trimming has to happen
before this runs, not after.

Needs ffmpeg:  brew install ffmpeg
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.join(HERE, "overlay.png")

# ⚠️ These must match the transparent hole in overlay.png EXACTLY. Padding to
# the phone body's origin instead of the screen's put the picture 14px high the
# first time — top hidden under the bezel, a dark strip and a cut-off nav bar
# along the bottom. `python3 make_frame.py --check` prints the real numbers.
SCREEN_W, SCREEN_H, SCREEN_X, SCREEN_Y = 800, 1740, 140, 90
CANVAS_W, CANVAS_H = 1080, 1920
MUSIC_VOLUME = 0.16          # sits under a narrator without competing
FADE = 1.2


def music_track():
    d = os.path.join(HERE, "music")
    for f in sorted(os.listdir(d)):
        if f.lower().endswith((".wav", ".mp3", ".m4a")):
            return os.path.join(d, f)
    sys.exit(f"No music file in {d}")


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def render(src, dst, music):
    dur = duration(src)
    fade_out = max(0.0, dur - FADE)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-i", src,
        "-loop", "1", "-i", OVERLAY,
        "-i", music,
        "-filter_complex",
        f"[0:v]fps=30,scale={SCREEN_W}:{SCREEN_H}:flags=lanczos,"
        f"pad={CANVAS_W}:{CANVAS_H}:{SCREEN_X}:{SCREEN_Y}:color=#0C131B[base];"
        f"[base][1:v]overlay=0:0:shortest=1,format=yuv420p[v];"
        f"[2:a]atrim=0:{dur},volume={MUSIC_VOLUME},"
        f"afade=t=in:st=0:d={FADE},afade=t=out:st={fade_out:.2f}:d={FADE},"
        f"alimiter=limit=0.95[a]",
        "-map", "[v]", "-map", "[a]",
        # ⚠️ LOAD-BEARING. The music file carries a metadata stream; without -dn
        # it rides along as bin_data claiming the TRACK's length, and every
        # player takes the longest stream — so a 31s video reports 1:52 in
        # QuickTime, VLC and Finder. ffprobe's format=duration will NOT show
        # this. Verify with `mdls -name kMDItemDurationSeconds`.
        "-dn", "-sn", "-map_metadata", "-1", "-map_chapters", "-1",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-r", "30",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        dst,
    ], check=True)
    return dur


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src_dir = os.path.expanduser(sys.argv[1])
    out_dir = os.path.expanduser(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(src_dir, "rendered")
    os.makedirs(out_dir, exist_ok=True)
    music = music_track()
    print(f"music: {os.path.basename(music)}\nout:   {out_dir}\n")

    files = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(".mp4"))
    if not files:
        sys.exit(f"No .mp4 files in {src_dir}")
    total_in = total_out = 0
    for f in files:
        src, dst = os.path.join(src_dir, f), os.path.join(out_dir, f)
        dur = render(src, dst, music)
        total_in += os.path.getsize(src)
        total_out += os.path.getsize(dst)
        print(f"  {f:30} {dur:6.1f}s  "
              f"{os.path.getsize(src)/1048576:6.1f} MB -> {os.path.getsize(dst)/1048576:5.1f} MB")
    print(f"\n  {total_in/1048576:.0f} MB -> {total_out/1048576:.0f} MB")
    print("\n  Check one with: mdls -name kMDItemDurationSeconds <file>")


if __name__ == "__main__":
    main()
