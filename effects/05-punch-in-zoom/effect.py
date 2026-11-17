"""A hard punch-in on your face the moment you say a key word, then back out."""
import cv2
import numpy as np

NAME = "Punch-in zoom"
ABOUT = "A hard punch-in on your face when you say a key word."
NEEDS_CUTOUT = False
NEEDS_WORDS = True


def add_args(p):
    p.add_argument("--keyword", nargs="+", required=True, help="the word(s) that trigger the zoom")
    p.add_argument("--zoom", type=float, default=1.45, help="how close the first punch goes (default 1.45)")
    p.add_argument("--hold", type=float, default=0.6, help="seconds to stay close after the word (default 0.6)")


def render(clip, out, brand, args):
    W, H = clip.size
    hits = clip.find(args.keyword)
    if not hits:
        print(f"  note: none of {args.keyword} is spoken in this clip, so the video stays unzoomed")
    cx, cy = args.focus

    def zoom_at(t):
        z = 1.0
        for k, w in enumerate(hits):
            target = args.zoom if k % 2 == 0 else 1 + (args.zoom - 1) * 0.55
            if t < w.start - 0.05:
                continue
            nxt = hits[k + 1].start - 0.05 if k + 1 < len(hits) else float("inf")
            back = w.end + args.hold
            k_in = min(1, (t - w.start + 0.05) / 0.12)
            z = 1 + (target - 1) * k_in
            if t > back and t < nxt:
                z = 1 + (target - 1) * max(0, 1 - (t - back) / 0.12)
        return z

    for i in range(clip.n):
        z = zoom_at(clip.t(i))
        M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
        out.write(cv2.warpAffine(clip.rgb(i), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
