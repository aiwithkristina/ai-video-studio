"""A wall of screens fills in behind you, tile by tile."""
import random

import cv2

from kfx import as_float, images_or_placeholders

NAME = "Screen wall"
ABOUT = "A wall of your screenshots fills in behind you, tile by tile."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--images", nargs="+", help="screenshots or photos for the tiles (they repeat to fill the wall)")
    p.add_argument("--bottom", type=float, default=0.73, help="where the wall stops, as a fraction of the frame height (default 0.73)")
    p.add_argument("--seed", type=int, default=3)


def render(clip, out, brand, args):
    rnd = random.Random(args.seed)
    W, H = clip.size
    cols, rows, g = 4, 9, 10
    TW = (W - g * (cols + 1)) // cols
    TH = int(TW * 0.62)
    srcs = images_or_placeholders(args.images, brand, 8, size=(800, 500))
    wall_bottom = int(args.bottom * H)
    tiles = []
    for r in range(rows):
        for c in range(cols):
            im = rnd.choice(srcs)
            ih, iw = im.shape[:2]
            s = max(TW / iw, TH / ih)
            im = cv2.resize(im, (int(iw * s) + 1, int(ih * s) + 1), interpolation=cv2.INTER_AREA)
            oy = rnd.randint(0, max(0, im.shape[0] - TH))
            ox = (im.shape[1] - TW) // 2
            tiles.append((g + c * (TW + g), 40 + r * (TH + g), im[oy:oy + TH, ox:ox + TW], 0.6 + rnd.random() * 0.35))
    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        fr = base.copy()
        for x, y, im, t0 in tiles:
            if t < t0 or y > wall_bottom:
                continue
            k = min(1, (t - t0) / 0.12)
            s = 0.85 + 0.15 * k
            h, w = im.shape[:2]
            sh, sw = int(h * s), int(w * s)
            tim = as_float(cv2.resize(im, (sw, sh)))
            cx, cy = x + w // 2, y + h // 2
            x0, y0 = cx - sw // 2, cy - sh // 2
            y1 = min(y0 + sh, wall_bottom)
            if y1 <= y0:
                continue
            fr[y0:y1, x0:x0 + sw] = fr[y0:y1, x0:x0 + sw] * (1 - k) + tim[:y1 - y0] * k
        out.write(fr * (1 - a) + base * a)
