"""A glowing growth chart draws itself behind you."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from kfx import as_float

NAME = "Growth chart"
ABOUT = "A glowing chart draws itself behind you, ending on a label."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--labels", default="M,T,W,T,F,S,S", help="x-axis labels, comma separated (default M,T,W,T,F,S,S)")
    p.add_argument("--values", default="0.08,0.12,0.15,0.22,0.35,0.6,0.95",
                   help="one value per label between 0 and 1 (default: slow start, steep growth)")
    p.add_argument("--scale", default="10K,5K,1K,0", help="y-axis labels top to bottom (default 10K,5K,1K,0)")
    p.add_argument("--tag", default="GROWTH", help="word at the tip of the line (default GROWTH)")


def render(clip, out, brand, args):
    W, H = clip.size
    days = [s.strip() for s in args.labels.split(",")]
    vals = [float(v) for v in args.values.split(",")][:len(days)]
    scale = [s.strip() for s in args.scale.split(",")]
    n = len(vals)
    X0, X1, Y0, Y1 = 70, W - 70, 150, 860
    xs = [X0 + 40 + k * (X1 - X0 - 80) / max(1, n - 1) for k in range(n)]
    label = brand.font("label", 30)
    small = brand.font("label", 22)
    tag = brand.font("display", 30, 800)
    fill_rgb = brand.tint("primary", 0.35)
    glow_rgb = brand.tint("primary", 0.6)
    yy, xx = np.mgrid[0:H, 0:W]
    vig = np.clip(((xx - W / 2) / 700) ** 2 + ((yy - 700) / 1100) ** 2, 0, 1)[..., None]
    grad = np.clip(((Y1 - 40) - np.arange(H)) / ((Y1 - 40) - Y0), 0, 1)[:, None] ** 1.3 * np.ones((1, W))

    def curve(p):
        pts, N = [], 200
        for j in range(int(N * p) + 1):
            u = j / N * (n - 1)
            k = min(n - 2, int(u))
            f = u - k
            f = f * f * (3 - 2 * f)
            x = xs[k] + (xs[k + 1] - xs[k]) * (u - k)
            v = vals[k] + (vals[k + 1] - vals[k]) * f
            pts.append((x, Y1 - 60 - v * (Y1 - Y0 - 140)))
        return pts

    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        ap = min(1, max(0, (t - 0.15) / 0.3))
        fr = base * (1 - ap * (0.40 + 0.25 * vig))          # darken the room so the chart glows
        L = Image.fromarray(fr.astype(np.uint8)).convert("RGBA")
        ov = Image.new("RGBA", L.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for k, x in enumerate(xs):
            d.line((x, Y0 + 50, x, Y1 - 40), fill=(255, 255, 255, int(50 * ap)), width=2)
            d.text((x, Y0 + 15), days[k], font=label, fill=(255, 255, 255, int(200 * ap)), anchor="mm")
        for j, lab in enumerate(scale):
            y = Y0 + 90 + j * (Y1 - Y0 - 150) / max(1, len(scale) - 1)
            d.line((X0 + 20, y, X1 - 20, y), fill=(255, 255, 255, int(28 * ap)), width=2)
            d.text((X0 + 24, y - 18), lab, font=small, fill=(255, 255, 255, int(150 * ap)), anchor="lm")
        p = min(1, max(0, (t - 0.45) / 2.2))
        p = 1 - (1 - p) ** 2
        pts = curve(p)
        if len(pts) > 1:
            area = Image.new("RGBA", L.size, (0, 0, 0, 0))
            ImageDraw.Draw(area).polygon(pts + [(pts[-1][0], Y1 - 40), (pts[0][0], Y1 - 40)], fill=fill_rgb + (110,))
            aa = np.asarray(area).copy()
            aa[..., 3] = (aa[..., 3] * grad).astype(np.uint8)
            ov.alpha_composite(Image.fromarray(aa))
            gl = Image.new("RGBA", L.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).line(pts, fill=glow_rgb + (200,), width=30, joint="curve")
            ov.alpha_composite(gl.filter(ImageFilter.GaussianBlur(14)))
            d.line(pts, fill=(255, 255, 255, 255), width=7, joint="curve")
            x, y = pts[-1]
            d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, 255, 255, 255))
            r = 14 + (t * 60) % 40
            d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 255, 255, int(255 * (1 - (r - 14) / 40))), width=3)
            if p > 0.97 and args.tag:
                tw = tag.getlength(args.tag)
                d.text((x - 60 - tw / 2 - 10, y), args.tag, font=tag, fill=(255, 255, 255), anchor="mm")
                d.line((x - 80, y + 10, x - 60, y - 10), fill=(255, 255, 255), width=5)
                d.line((x - 74, y - 10, x - 60, y - 10, x - 60, y + 4), fill=(255, 255, 255), width=5)
        L.alpha_composite(ov)
        fr2 = as_float(L.convert("RGB"))
        out.write(fr2 * (1 - a) + base * a)
