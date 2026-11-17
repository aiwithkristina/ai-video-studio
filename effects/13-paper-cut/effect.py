"""Collage look: you become a paper cut-out on a scribbled paper background, with cut-out letters."""
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw

from kfx import as_float, paste

NAME = "Paper cut"
ABOUT = "You turn into a paper cut-out on a collage background, cut-out letters pop in."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--text", default="AI!", help="1 to 5 letters that pop in as cut-out squares (default AI!)")
    p.add_argument("--at", type=float, default=0.3, help="second the collage switches on (default 0.3)")
    p.add_argument("--seed", type=int, default=5)


def paper(W, H, brand, rnd, rs):
    bg = Image.new("RGB", (W, H), brand.rgb("background"))
    d = ImageDraw.Draw(bg)
    line = brand.tint("background", -0.07)
    for y in range(0, H, 54):
        d.line((0, y, W, y), fill=line, width=2)
    pts, x = [(560, 720)], 560                                     # torn paper patch
    while x < W:
        x += rnd.randint(18, 40)
        pts.append((x, 720 + rnd.randint(-14, 14)))
    pts += [(W, 1250)]
    while x > 560:
        x -= rnd.randint(18, 40)
        pts.append((x, 1250 + rnd.randint(-14, 14)))
    d.polygon(pts, fill=brand.rgb("secondary"))
    scribble = brand.tint("primary", 0.1)
    for bx, by, bw, bh in [(60, 330, 620, 330), (600, 820, 420, 260), (520, 1300, 520, 160)]:   # marker hatching
        for k in range(42):
            x0 = bx + k * bw / 42 + rs.randint(-6, 6)
            d.line((x0, by + rs.randint(0, 30), x0 + rs.randint(20, 60), by + bh - rs.randint(0, 30)), fill=scribble, width=7)
    for x, y in [(90, 880), (150, 940), (960, 720)]:
        d.line((x - 22, y - 22, x + 22, y + 22), fill=brand.rgb("primary"), width=8)
        d.line((x - 22, y + 22, x + 22, y - 22), fill=brand.rgb("primary"), width=8)
    return as_float(bg)


def letter(ch, bg, fg, ang, brand):
    im = Image.new("RGBA", (150, 170), bg + (255,))
    ImageDraw.Draw(im).text((75, 85), ch, font=brand.font("display", 130, 900, 110), fill=fg, anchor="mm")
    return np.asarray(im.rotate(ang, expand=True, resample=Image.BICUBIC))


def render(clip, out, brand, args):
    W, H = clip.size
    rnd, rs = random.Random(args.seed), np.random.RandomState(args.seed)
    BG = paper(W, H, brand, rnd, rs)
    palette = [(brand.rgb("text"), (255, 255, 255)), (brand.rgb("primary"), (255, 255, 255)), ((255, 255, 255), brand.rgb("text"))]
    chars = list(args.text[:5])
    letters = [letter(c, *palette[k % 3], rs.uniform(-8, 8), brand) for k, c in enumerate(chars)]
    step = 170
    x_first = 160 if len(chars) <= 3 else W / 2 - step * (len(chars) - 1) / 2
    ring = brand.rgb("primary")
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))
    for i in range(clip.n):
        t = clip.t(i)
        f = as_float(clip.rgb(i))
        a = clip.alpha(i)
        k = min(1, max(0, (t - args.at) / 0.1))
        border = cv2.GaussianBlur(cv2.dilate((a > 0.5).astype(np.uint8), kernel).astype(np.float32), (0, 0), 1.5)
        sh = cv2.GaussianBlur(np.roll(np.roll(border, 14, 0), 10, 1), (0, 0), 10) * 0.35
        comp = BG * (1 - sh[..., None])
        comp = comp * (1 - border[..., None]) + 255 * border[..., None]       # white paper edge around you
        comp = comp * (1 - a[..., None]) + f * a[..., None]
        fr = f * (1 - k) + comp * k
        for j, li in enumerate(letters):
            t0 = args.at + 0.5 + j * 0.25
            if t >= t0:
                paste(fr, li, x_first + j * step, 230, min(1, (t - t0) / 0.1) + 0.0001)
        t_ring = args.at + 0.5 + len(letters) * 0.25 + 0.25
        if t > t_ring and len(chars) <= 4:
            p = min(1, (t - t_ring) / 0.4)
            I = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
            x_end = x_first + (len(chars) - 1) * step
            ImageDraw.Draw(I).arc((x_first - 100, 120, x_end + 130, 340), start=200, end=200 + 340 * p, fill=ring, width=9)
            fr = as_float(I)
        out.write(fr)
