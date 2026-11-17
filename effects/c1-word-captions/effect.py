"""Captions one word at a time, big and clean, with a different entrance per sentence."""
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from kfx import as_float, ease_out

NAME = "Word-by-word captions"
ABOUT = "One word at a time, keywords bigger, entrance changes every sentence (pop, rise, drop)."
NEEDS_CUTOUT = False
NEEDS_WORDS = True

MAXW = 900


def add_args(p):
    p.add_argument("--keywords", nargs="*", default=[], help="words shown bigger and bolder")
    p.add_argument("--proper", nargs="*", default=[], help="names to keep capitalized (everything else is lowercase)")
    p.add_argument("--y", type=float, default=0.65, help="caption height as a fraction of the frame (default 0.65)")
    p.add_argument("--color", default="light", help="brand color for the words (default light = white)")
    p.add_argument("--scale", type=float, default=1.0, help="make all captions bigger or smaller (default 1.0)")


def draw_word(layer, xy, s, font, fill, alpha):
    a = int(120 * alpha)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text(xy, s, font=font, anchor="mm", fill=(0, 0, 0, a), stroke_width=2, stroke_fill=(0, 0, 0, a))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(layer).text(xy, s, font=font, anchor="mm", fill=fill + (int(255 * alpha),))


def render(clip, out, brand, args):
    W, H = clip.size
    keys = {k.lower() for k in args.keywords}
    proper = {k.lower(): k for k in args.proper}
    color = brand.rgb(args.color)
    y0 = int(args.y * H)
    words, sentence = [], 0
    for w in clip.words:
        core = w.text.strip('.,!?"')
        punct = w.text.rstrip('"')[len(w.text.rstrip('"').rstrip(".,!?")):]
        shown = proper.get(core.lower(), core if any(ch.isdigit() for ch in core) or core == "I" else core.lower()) + punct
        words.append((w, shown, sentence))
        if re.search(r"[.?!]$", w.text):
            sentence += 1

    def fit(size, s, weight):
        while size > 40:
            f = brand.font("body", size, weight)
            if f.getlength(s) <= MAXW:
                return f
            size -= 4
        return brand.font("body", 40, weight)

    for i in range(clip.n):
        t = clip.t(i)
        fr = clip.rgb(i)
        cur = [x for x in words if x[0].start <= t]
        if cur:
            w, s, sn = cur[-1]
            nxt = words.index(cur[-1]) + 1
            pause = nxt < len(words) and t > w.end + 0.6
            if not pause:
                core = s.rstrip(".,!?").lower()
                is_num = any(ch.isdigit() for ch in s)
                big = core in keys or is_num
                base = int((150 if is_num else 128 if big else 88) * args.scale)
                weight = 800 if big else 700
                k = ease_out(min(1, max(0, (t - w.start) / 0.12)))
                L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                mode = sn % 3
                if mode == 0:      # pop
                    draw_word(L, (W // 2, y0), s, fit(int(fit(base, s, weight).size * (0.7 + 0.3 * k)), s, weight), color, 1.0)
                elif mode == 1:    # rise
                    draw_word(L, (W // 2, y0 + int(40 * (1 - k))), s, fit(base, s, weight), color, k)
                else:              # drop
                    draw_word(L, (W // 2, y0), s, fit(int(fit(base, s, weight).size * (1.25 - 0.25 * k)), s, weight), color, k)
                la = np.asarray(L).astype(np.float32)
                al = la[..., 3:4] / 255
                fr = as_float(fr) * (1 - al) + la[..., :3] * al
        out.write(fr)
