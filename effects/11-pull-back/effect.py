"""The camera pulls back: your video shrinks into a card inside a real app screen."""
import cv2
import numpy as np

from kfx import as_float, crop, images_or_placeholders, round_mask

NAME = "Pull-back reveal"
ABOUT = "Your video shrinks into a card inside a real app screen."
NEEDS_CUTOUT = False
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--screen", help="a real screenshot of the app (it fills the frame behind your card)")
    p.add_argument("--crop", help="show only part of the screenshot: x0,y0,x1,y1 as fractions")
    p.add_argument("--at", type=float, default=0.6, help="second the pull-back starts (default 0.6)")
    p.add_argument("--y", type=float, default=0.30, help="final card center height as a fraction of the frame (default 0.30)")
    p.add_argument("--screen-y", type=float, default=0.66, help="center height of the screenshot as a fraction of the frame (default 0.66)")
    p.add_argument("--card-width", type=int, default=420)


def render(clip, out, brand, args):
    W, H = clip.size
    shot = images_or_placeholders([args.screen] if args.screen else None, brand, 1, size=(1000, 1700), label="YOUR APP")[0]
    shot = crop(shot, args.crop)
    s = W / shot.shape[1]
    shot = cv2.resize(shot, (W, int(shot.shape[0] * s)), interpolation=cv2.INTER_AREA)
    ui = np.zeros((H, W, 3), np.float32) + as_float(shot[min(20, shot.shape[0] - 1), 20])
    top = int(args.screen_y * H - shot.shape[0] / 2)          # where the screenshot sits, so the card lands above its content
    y0, y1 = max(0, top), min(H, top + shot.shape[0])
    if y1 > y0:
        ui[y0:y1] = shot[y0 - top:y1 - top]
    TW = args.card_width
    TH = int(TW * H / W)
    tx, ty = W // 2 - TW // 2, int(args.y * H) - TH // 2
    for i in range(clip.n):
        t = clip.t(i)
        f = as_float(clip.rgb(i))
        e = 1 - (1 - min(1, max(0, (t - args.at) / 0.7))) ** 3
        w, h = int(W + (TW - W) * e), int(H + (TH - H) * e)
        x, y = int(tx * e), int(ty * e)
        fr = ui.copy()
        v = cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA)
        m = round_mask(w, h, max(1, int(28 * e)))[..., None]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        mm = m[y0 - y:y1 - y, x0 - x:x1 - x]
        fr[y0:y1, x0:x1] = fr[y0:y1, x0:x1] * (1 - mm) + v[y0 - y:y1 - y, x0 - x:x1 - x] * mm
        out.write(fr)
