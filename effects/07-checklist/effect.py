"""A glass checklist at the top: each item types in, then gets checked off."""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from kfx import as_float, fit_font, round_mask

NAME = "Checklist"
ABOUT = "A glass checklist: items type in and get checked off as you talk."
NEEDS_CUTOUT = False
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--items", nargs="+", default=["Pick one task", "Ask AI to do it", "Check the result"],
                   help="2 to 5 short items")
    p.add_argument("--title", default="ALL YOU NEED TO DO")
    p.add_argument("--times", nargs="+", type=float,
                   help="second each item appears (default: spread over the clip); each is checked 0.8 s later")


def render(clip, out, brand, args):
    W, H = clip.size
    items = args.items[:5]
    n = len(items)
    if args.times:
        starts = args.times[:n]
    else:
        gap = max(0.6, (clip.duration - 1.4) / max(1, n))
        starts = [0.5 + k * gap for k in range(n)]
    checks = [s + 0.8 for s in starts]
    X0, Y0, X1 = int(W * 0.14), 30, int(W * 0.86)
    Y1 = Y0 + 92 + n * 56
    M = round_mask(X1 - X0, Y1 - Y0, 28)
    label = brand.font("label", 20)
    body = fit_font(brand, "body", 32, max(items, key=len), X1 - X0 - 130, weight=700)
    accent = brand.rgb("primary")
    bar = brand.tint("primary", 0.45)
    for i in range(clip.n):
        t = clip.t(i)
        f = clip.rgb(i)
        fr = as_float(f)
        ap = min(1, max(0, (t - 0.1) / 0.2))
        if ap > 0:
            reg = as_float(cv2.GaussianBlur(f, (0, 0), 20)[Y0:Y1, X0:X1]) * 0.30 + np.float32((18, 18, 20)) * 0.70
            m = M[..., None] * ap
            fr[Y0:Y1, X0:X1] = fr[Y0:Y1, X0:X1] * (1 - m) + reg * m
            L = Image.fromarray(fr.astype(np.uint8))
            d = ImageDraw.Draw(L)
            d.rounded_rectangle((X0, Y0, X1, Y1), 28, outline=(255, 255, 255), width=2)
            done = sum(1 for tc in checks if t >= tc)
            d.text((X0 + 34, Y0 + 30), args.title.upper(), font=label, fill=(200, 200, 200), anchor="lm")
            d.text((X1 - 34, Y0 + 30), f"{done} of {n}", font=label, fill=(200, 200, 200), anchor="rm")
            d.rectangle((X0 + 34, Y0 + 50, X1 - 34, Y0 + 53), fill=(70, 70, 74))
            d.rectangle((X0 + 34, Y0 + 50, X0 + 34 + int((X1 - X0 - 68) * done / n), Y0 + 53), fill=bar)
            for k, s in enumerate(items):
                y = Y0 + 92 + k * 56
                if t >= checks[k]:
                    d.ellipse((X0 + 34, y - 17, X0 + 68, y + 17), fill=accent)
                    d.line([(X0 + 43, y), (X0 + 50, y + 8), (X0 + 61, y - 7)], fill=(255, 255, 255), width=4)
                else:
                    d.ellipse((X0 + 34, y - 17, X0 + 68, y + 17), outline=(150, 150, 155), width=3)
                if t >= starts[k]:
                    kk = min(1, (t - starts[k]) / 0.35)
                    d.text((X0 + 90, y), s[:max(1, int(len(s) * kk))], font=body, fill=(255, 255, 255), anchor="lm")
                else:
                    d.rounded_rectangle((X0 + 90, y - 7, X0 + 90 + 280 - k * 40, y + 7), 7, fill=(70, 70, 74))
            fr = as_float(L)
        out.write(fr)
