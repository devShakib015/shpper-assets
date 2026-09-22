"""Find the stretches where nothing happens — the pauses worth cutting."""
import subprocess, sys
from PIL import Image, ImageChops, ImageStat
W,H,FPS = 132,287,15
def idles(path, quiet=0.55, min_len=1.2):
    p=subprocess.Popen(["ffmpeg","-v","error","-i",path,"-vf",f"fps={FPS},scale={W}:{H}",
                        "-pix_fmt","gray","-f","rawvideo","-"],stdout=subprocess.PIPE)
    prev=None; still=[]; n=W*H; i=0
    while True:
        b=p.stdout.read(n)
        if len(b)<n: break
        f=Image.frombytes("L",(W,H),b)
        if prev is not None:
            still.append(ImageStat.Stat(ImageChops.difference(f,prev)).mean[0] < quiet)
        prev=f; i+=1
    runs=[]; s=None
    for j,q in enumerate(still):
        if q and s is None: s=j
        elif not q and s is not None:
            if (j-s)/FPS >= min_len: runs.append((s/FPS,j/FPS))
            s=None
    if s is not None and (len(still)-s)/FPS >= min_len: runs.append((s/FPS,len(still)/FPS))
    return runs, len(still)/FPS
if __name__=="__main__":
    for path in sys.argv[1:]:
        runs,dur = idles(path)
        dead = sum(b-a for a,b in runs)
        name = path.split("/")[-1]
        print(f"\n  {name}  ({dur:.1f}s, {dead:.1f}s idle = {dead/dur*100:.0f}%)")
        for a,b in runs:
            print(f"      {a:6.1f}s -> {b:6.1f}s   ({b-a:.1f}s still)")
