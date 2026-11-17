"""Your room switches to a new background (a website, a place, a slide) without a green screen."""
import cv2
import numpy as np

from kfx import as_float, crop, images_or_placeholders

NAME = "Green screen"
ABOUT = "Your room switches to any background, no green screen needed."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--background", help="image to put behind you (a website screenshot, a photo, a slide)")
    p.add_argument("--crop", help="use only part of the image: x0,y0,x1,y1 as fractions")
    p.add_argument("--at", type=float, default=0.4, help="second the background switches (default 0.4)")
    p.add_argument("--keep-bottom", type=float,
                   help="keep the real video below this height (fraction, e.g. 0.77 keeps your desk)")


def render(clip, out, brand, args):
    W, H = clip.size
    src = images_or_placeholders([args.background] if args.background else None, brand, 1, size=(1080, 1920), label="YOUR BACKGROUND")[0]
    src = crop(src, args.crop)
    s = W / src.shape[1]
    src = cv2.resize(src, (W, int(src.shape[0] * s)), interpolation=cv2.INTER_AREA)
    bg = np.zeros((H, W, 3), np.float32) + as_float(src[-1, W // 2])
    bg[:min(H, src.shape[0])] = src[:H]
    keep = int(args.keep_bottom * H) if args.keep_bottom else None
    for i in range(clip.n):
        t = clip.t(i)
        f = as_float(clip.rgb(i))
        a = clip.alpha(i).copy()
        k = min(1, max(0, (t - args.at) / 0.12))
        if keep:
            a[keep:] = 1
            a[keep - 40:keep] = np.maximum(a[keep - 40:keep], np.linspace(0, 1, 40)[:, None])
        a = a[..., None]
        out.write(f * (1 - k) + (bg * (1 - a) + f * a) * k)
