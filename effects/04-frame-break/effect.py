"""The video shrinks into a social-post frame and you step out of it."""
import cv2
from PIL import Image, ImageDraw

import numpy as np

from kfx import as_float, round_mask

NAME = "Frame break"
ABOUT = "Your video shrinks into a post frame and you step out of it."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--handle", help="name shown on the post (default: handle from brand.json)")
    p.add_argument("--at", type=float, default=0.15, help="second the frame starts to shrink (default 0.15)")


def frame_mask(W, H, x0, y0, x1, y1, r):
    m = np.zeros((H, W), np.float32)
    x0, y0, x1, y1 = (int(v) for v in (x0, y0, x1, y1))
    rm = round_mask(x1 - x0, y1 - y0, r)
    ys, xs = max(0, y0), max(0, x0)
    ye, xe = min(H, y1), min(W, x1)
    m[ys:ye, xs:xe] = rm[ys - y0:ye - y0, xs - x0:xe - x0]
    return cv2.GaussianBlur(m, (0, 0), 1.2)


def post_overlay(W, H, x0, y0, x1, y1, alpha, handle, brand):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    a = int(255 * alpha)
    white = (255, 255, 255, a)
    rx = x1 - 48
    for yy in (y1 - 420, y1 - 330, y1 - 240):
        d.ellipse((rx - 20, yy - 20, rx + 20, yy + 20), outline=white, width=5)
    d.ellipse((x0 + 30, y1 - 120, x0 + 80, y1 - 70), fill=white)
    if handle:
        d.text((x0 + 95, y1 - 95), handle.lstrip("@"), font=brand.font("body", 28, 700), fill=white, anchor="lm")
        d.rounded_rectangle((x0 + 330, y1 - 115, x0 + 430, y1 - 75), 10, outline=white, width=3)
        d.text((x0 + 380, y1 - 95), "Follow", font=brand.font("body", 22, 700), fill=white, anchor="mm")
    return as_float(L)


def render(clip, out, brand, args):
    W, H = clip.size
    handle = args.handle if args.handle is not None else brand.handle
    cx, cy = W // 2, int(H * 0.51)
    for i in range(clip.n):
        t = clip.t(i)
        f = as_float(clip.rgb(i))
        a = clip.alpha(i)
        p = min(1, max(0, (t - args.at) / 0.35))
        e = 1 - (1 - p) ** 3
        s = 1 - 0.2 * e
        M = np.float32([[s, 0, cx - s * W / 2], [0, s, cy - s * H / 2]])
        fs = cv2.warpAffine(f, M, (W, H))
        as_ = cv2.warpAffine(a, M, (W, H))
        bg = cv2.GaussianBlur(f, (0, 0), 30) * (1 - 0.6 * e)
        hw = W / 2 * s * (1 - 0.30 * e)
        top = cy - H / 2 * s * (1 - 0.30 * e)
        bot = cy + H / 2 * s * (1 - 0.12 * e)
        m = frame_mask(W, H, cx - hw, top, cx + hw, bot, int(30 + 20 * e))
        fr = bg * (1 - m[..., None]) + fs * m[..., None]
        outside = as_ * (1 - m) * e          # the parts of you that leave the frame
        fr = fr * (1 - outside[..., None]) + fs * outside[..., None]
        if e > 0.6:
            u = post_overlay(W, H, cx - hw, top, cx + hw, bot, (e - 0.6) / 0.4, handle, brand)
            ua = u[..., 3:4] / 255
            fr = fr * (1 - ua) + u[..., :3] * ua
        out.write(fr)
