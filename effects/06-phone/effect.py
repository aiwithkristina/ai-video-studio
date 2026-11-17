"""A 3D phone showing a real app floats next to you, turned toward you."""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from kfx import as_float, crop, images_or_placeholders

NAME = "Phone"
ABOUT = "A 3D phone with a real app screen floats beside you, turned toward you."
NEEDS_CUTOUT = True
NEEDS_WORDS = False

PW, PH, B = 430, 880, 16


def add_args(p):
    p.add_argument("--crop", help="show only part of the screenshot: x0,y0,x1,y1 as fractions, e.g. 0.3,0.2,0.9,0.6")
    p.add_argument("--screen", help="a real phone screenshot (portrait works best)")
    p.add_argument("--side", choices=["right", "left"], default="right", help="which side of you the phone floats (default right)")
    p.add_argument("--angle", type=float, default=30, help="how far the phone turns toward you, in degrees (default 30)")
    p.add_argument("--y", type=float, default=0.34, help="phone height as a fraction of the frame (default 0.34)")


def phone_image(screen):
    sw, sh = PW - 2 * B, PH - 2 * B
    if screen.shape[1] > screen.shape[0]:
        # a wide (desktop) screenshot: fit its width and center it on the app's own background color
        s = sw / screen.shape[1]
        fitted = cv2.resize(screen, (sw, max(1, int(screen.shape[0] * s))), interpolation=cv2.INTER_AREA)
        sc = np.zeros((sh, sw, 3), np.uint8) + screen[2, 2]
        y = (sh - fitted.shape[0]) // 2
        sc[y:y + fitted.shape[0]] = fitted[:sh]
    else:
        s = max(sw / screen.shape[1], sh / screen.shape[0])
        sc = cv2.resize(screen, (int(screen.shape[1] * s) + 1, int(screen.shape[0] * s) + 1), interpolation=cv2.INTER_AREA)
        y0, x0 = (sc.shape[0] - sh) // 2, (sc.shape[1] - sw) // 2
        sc = sc[y0:y0 + sh, x0:x0 + sw]
    ph = Image.new("RGBA", (PW + 12, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 200, 10, 260), 4, fill=(70, 70, 74))           # side buttons
    d.rounded_rectangle((0, 280, 10, 360), 4, fill=(70, 70, 74))
    d.rounded_rectangle((PW + 2, 250, PW + 12, 370), 4, fill=(70, 70, 74))
    d.rounded_rectangle((6, 0, PW + 6, PH - 1), 70, fill=(92, 92, 98))     # frame
    d.rounded_rectangle((10, 4, PW + 2, PH - 5), 66, fill=(14, 14, 16))    # bezel
    arr = np.array(ph)
    m = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, sw - 1, sh - 1), 54, fill=255)
    m = np.asarray(m)[..., None] / 255.0
    reg = arr[B:B + sh, 6 + B:6 + B + sw]
    reg[..., :3] = (reg[..., :3] * (1 - m) + sc * m).astype(np.uint8)
    L = Image.fromarray(arr)
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((6 + PW / 2 - 62, B + 20, 6 + PW / 2 + 62, B + 56), 18, fill=(0, 0, 0))   # camera island
    glare = Image.new("RGBA", L.size, (0, 0, 0, 0))
    ImageDraw.Draw(glare).polygon([(40, 20), (200, 20), (60, PH - 200), (20, PH - 200)], fill=(255, 255, 255, 18))
    L.alpha_composite(glare)
    return np.asarray(L)


def render(clip, out, brand, args):
    W, H = clip.size
    screen = images_or_placeholders([args.screen] if args.screen else None, brand, 1, size=(600, 1300), label="YOUR APP")[0]
    screen = crop(screen, args.crop)
    P = phone_image(screen)
    h, w = P.shape[:2]
    if args.side == "left":
        P = P[:, ::-1].copy()
    sign = -1 if args.side == "right" else 1
    px = W * (0.76 if args.side == "right" else 0.24)

    def place(cx, cy, ang):
        f = 1100
        a = np.radians(ang)
        pts = []
        for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
            X = 0.82 * x * np.cos(a)
            Z = 0.82 * x * np.sin(a) + f
            pts.append([cx + X * f / Z, cy + 0.82 * y * f / Z])
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(pts))
        return cv2.warpPerspective(P, M, (W, H), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)), np.float32(pts)

    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        fr = base.copy()
        e = 1 - (1 - min(1, max(0, (t - 0.1) / 0.35))) ** 3
        cy = args.y * H + 90 * (1 - e) + 10 * np.sin(t * 2.2)
        img, pts = place(px, cy, sign * args.angle + 3 * np.sin(t * 1.3))
        sh = np.zeros((H, W), np.float32)
        cv2.fillConvexPoly(sh, (pts + [18, 30]).astype(np.int32), 0.45)
        fr = fr * (1 - cv2.GaussianBlur(sh, (0, 0), 28)[..., None] * e)     # soft shadow
        al = img[..., 3] / 255.0
        for kk in range(16, 0, -1):                                             # phone thickness
            sa = np.roll(al, kk * (-sign), 1) * e
            c = 48 + kk * 2
            fr = fr * (1 - sa[..., None]) + np.float32((c, c, c + 4)) * sa[..., None]
        pa = img[..., 3:4] / 255.0 * e
        fr = fr * (1 - pa) + img[..., :3] * pa
        out.write(fr * (1 - a) + base * a)
