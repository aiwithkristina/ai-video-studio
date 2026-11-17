"""Split screen: a real app screen on top, you below, with cards flying into the app."""
import cv2
import numpy as np

from kfx import as_float, crop, images_or_placeholders, paste

NAME = "App world"
ABOUT = "Split screen: a real app on top, you below, cards fly into the app."
NEEDS_CUTOUT = False
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--crop", help="show only part of the screenshot: x0,y0,x1,y1 as fractions, e.g. 0.3,0.2,0.9,0.6")
    p.add_argument("--screen", help="a real screenshot of the app you talk about (desktop or phone)")
    p.add_argument("--images", nargs="+", help="up to 5 small images that fly into the app (photos, files)")
    p.add_argument("--split", type=float, default=0.45, help="how much of the height the app takes (default 0.45)")


def render(clip, out, brand, args):
    W, H = clip.size
    UH = int(args.split * H)
    screen = images_or_placeholders([args.screen] if args.screen else None, brand, 1, size=(1000, 600), label="YOUR APP")[0]
    screen = crop(screen, args.crop)
    s = (W - 80) / screen.shape[1]
    screen = cv2.resize(screen, (W - 80, int(screen.shape[0] * s)), interpolation=cv2.INTER_AREA)
    if screen.shape[0] > UH - 40:
        top = (screen.shape[0] - (UH - 40)) // 2
        screen = screen[top:top + UH - 40]
    bgc = as_float(screen[5, 5])
    ox, oy = 40, (UH - screen.shape[0]) // 2
    thumbs = [cv2.resize(im, (104, 185), interpolation=cv2.INTER_AREA)
              for im in images_or_placeholders(args.images, brand, 5, size=(208, 370), label="")]
    land_y = oy + screen.shape[0] * 0.55

    def ui(t):
        arr = np.zeros((H, W, 3), np.float32) + bgc
        arr[oy:oy + screen.shape[0], ox:ox + screen.shape[1]] = screen
        for k, th in enumerate(thumbs):
            t0 = 0.25 + k * 0.22
            if t < t0:
                continue
            p = min(1, (t - t0) / 0.25)
            e = 1 - (1 - p) ** 3
            tx, ty = ox + 120 + k * 78, land_y
            sx, sy = W + 80, -120
            c = np.zeros((185 + 8, 104 + 8, 4), np.uint8)
            c[..., :3] = 255
            c[..., 3] = 255
            c[4:-4, 4:-4, :3] = th
            paste(arr, c, sx + (tx - sx) * e, sy + (ty - sy) * e, 0.6, (1 - e) * -14)
        return arr[:UH]

    fy = args.focus[1]
    crop_top = int(np.clip(fy - (H - UH) * 0.35, 0, UH))  # keep your face in the lower panel
    for i in range(clip.n):
        f = as_float(clip.rgb(i))
        fr = np.zeros((H, W, 3), np.float32)
        fr[:UH] = ui(clip.t(i))
        fr[UH:] = f[crop_top:crop_top + H - UH]
        out.write(fr)
