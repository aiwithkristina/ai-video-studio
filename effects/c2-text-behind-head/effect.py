"""Huge words pop up BEHIND you, the moment you say them. You stay in front of the text."""
import numpy as np
from PIL import Image, ImageDraw

from kfx import as_float, back_out

NAME = "Text behind head"
ABOUT = "Huge words pop up behind you the moment you say them."
NEEDS_CUTOUT = True
NEEDS_WORDS = True


def add_args(p):
    p.add_argument("--words", nargs="+", required=True, help="spoken words that pop up, in order (each appears when you say it)")
    p.add_argument("--show", nargs="+", help="optional: text to show instead of each word (same count as --words)")
    p.add_argument("--hide-at", type=float, help="second the words leave (default: end of the clip)")
    p.add_argument("--color", default="primary", help="brand color for the words (default primary)")
    p.add_argument("--top", type=float, default=0.07, help="top of the first line as a fraction of the frame (default 0.07)")


def render(clip, out, brand, args):
    W, H = clip.size
    shows = args.show if args.show and len(args.show) == len(args.words) else [w.upper() for w in args.words]
    events, used = [], set()
    for word, show in zip(args.words, shows):
        hits = [h for h in clip.find(word) if id(h) not in used]
        if not hits:
            print(f"  note: '{word}' is not spoken in this clip, skipped")
            continue
        used.add(id(hits[0]))
        events.append((hits[0].start, show.upper()))
    hide = args.hide_at if args.hide_at is not None else clip.duration
    color = brand.rgb(args.color)
    # one size for all lines: the largest that keeps the longest line inside the frame
    size = 250
    while size > 60 and max((brand.font("display", size, 900, 125).getlength(s) for _, s in events), default=0) > W - 80:
        size -= 6
    font = brand.font("display", size, 900, 125)
    line_h = int(size * 0.92)
    y_top = int(args.top * H) + line_h // 2
    sprites = []
    for _, s in events:
        tw = int(font.getlength(s)) + 40
        im = Image.new("RGBA", (tw, line_h + 60), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((tw / 2, (line_h + 60) / 2), s, font=font, anchor="mm", fill=color + (255,))
        sprites.append(im)
    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out_k = min(1, max(0, (t - (hide - 0.25)) / 0.25))
        for j, ((t0, _), sp) in enumerate(zip(events, sprites)):
            if t < t0:
                continue
            k = back_out(min(1, (t - t0) / 0.35))
            sc = max(0.05, 0.55 + 0.45 * k)
            alpha = min(1, (t - t0) / 0.1) * (1 - out_k)
            if alpha <= 0:
                continue
            im = sp.resize((max(1, int(sp.width * sc)), max(1, int(sp.height * sc))), Image.BICUBIC)
            if alpha < 1:
                im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
            cy = y_top + j * line_h + int(40 * (1 - k)) - int(40 * out_k)
            L.alpha_composite(im, (int(W / 2 - im.width / 2), int(cy - im.height / 2)))
        la = np.asarray(L).astype(np.float32)
        al = la[..., 3:4] / 255
        fr = base * (1 - al) + la[..., :3] * al
        out.write(fr * (1 - a) + base * a)            # you in front of the words
