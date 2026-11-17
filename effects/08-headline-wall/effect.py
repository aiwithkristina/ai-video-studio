"""Headline cards pile up on the wall behind you while the camera slowly pushes in."""
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw

from kfx import as_float, paste

NAME = "Headline wall"
ABOUT = "Headline cards pile up behind you while the camera pushes in."
NEEDS_CUTOUT = True
NEEDS_WORDS = False

DEFAULT_HEADLINES = [
    "AI can now|write your emails", "Why ChatGPT|makes things up", "Stop googling.|Ask AI instead",
    "AI explained|in plain English", "Your phone|has AI now", "5 prompts that|save an hour", "Is AI|listening?",
    "Claude vs|ChatGPT", "No tech|background needed", "AI won't take|your job", "What is|a prompt?",
    "Learn AI in|10 minutes",
]


def add_args(p):
    p.add_argument("--headlines", nargs="+", default=DEFAULT_HEADLINES,
                   help="up to 14 headlines; use | for a line break, e.g. 'Why ChatGPT|makes things up'")
    p.add_argument("--seed", type=int, default=7)


def headline_card(s, dark, brand):
    f = brand.font("body", 26, 800)
    s = s.replace("|", "\n")
    bb = ImageDraw.Draw(Image.new("L", (1, 1))).multiline_textbbox((0, 0), s, font=f, spacing=4)
    w, h = bb[2] + 40, bb[3] + 40
    bg = (30, 30, 32, 255) if dark else brand.rgb("background") + (255,)
    im = Image.new("RGBA", (w, h), bg)
    ImageDraw.Draw(im).multiline_text((20, 18), s, font=f, fill=(255, 255, 255) if dark else brand.rgb("text"), spacing=4)
    return np.asarray(im)


def render(clip, out, brand, args):
    W, H = clip.size
    rnd = random.Random(args.seed)
    heads = args.headlines[:14]
    slots, k = [], 0
    for y in [200, 330, 470, 600, 730, 860, 990, 1120]:
        for x in ([230, 540, 850] if y < 400 else [215, 865]):
            if k >= len(heads):
                break
            slots.append((headline_card(heads[k], k % 4 == 1, brand), x + rnd.randint(-15, 15), y + rnd.randint(-30, 30),
                          rnd.uniform(-5, 5), 0.3 + k * 0.11))
            k += 1
    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        fr = base.copy()
        for c, x, y, r, t0 in slots:
            if t < t0:
                continue
            kk = min(1, (t - t0) / 0.12)
            paste(fr, c, x, y, 0.8 + 0.2 * kk, r, alpha=kk)
        fr = fr * (1 - a) + base * a
        z = 1 + 0.10 * min(1, t / max(clip.duration, 0.1))     # slow push-in over the whole clip
        M = np.float32([[z, 0, W / 2 - z * W / 2], [0, z, 700 - z * 700]])
        out.write(cv2.warpAffine(fr, M, (W, H)))
