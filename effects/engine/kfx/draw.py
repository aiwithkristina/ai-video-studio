"""Drawing helpers shared by the effects: text, layering, cards, 3D tilt, easing."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def as_float(img):
    return np.asarray(img).astype(np.float32)


def comp(bg, fg, a):
    """Layer fg over bg with alpha a (H, W floats 0..1). Typical use: put the person (fg) back over a new background."""
    a = a[..., None]
    return (fg * a + bg * (1 - a)).astype(np.uint8)


def text(img, xy, s, font, fill=(255, 255, 255), shadow=True, anchor="mm"):
    """Draw text with an optional soft shadow. font comes from brand.font(...)."""
    layer = Image.fromarray(np.asarray(img).astype(np.uint8)) if not isinstance(img, Image.Image) else img
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text(xy, s, font=font, anchor=anchor, fill=(0, 0, 0, 110))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        layer.paste(sh, (0, 0), sh)
    ImageDraw.Draw(layer).text(xy, s, font=font, anchor=anchor, fill=fill)
    return np.asarray(layer.convert("RGB"))


def load_image(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"Image not found or unreadable: {path}")
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        return cv2.cvtColor(im, cv2.COLOR_BGRA2RGB)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def card(img, w, h, border=8, radius=22, border_color=(255, 255, 255)):
    """Fit an image (screenshot, photo) into a rounded RGBA card of w x h with a border."""
    if isinstance(img, str):
        img = load_image(img)
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    img = cv2.resize(img, (int(iw * s) + 1, int(ih * s) + 1), interpolation=cv2.INTER_AREA)
    y, x = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    img = img[y:y + h, x:x + w]
    c = np.zeros((h + 2 * border, w + 2 * border, 4), np.uint8)
    c[..., :3] = border_color
    c[border:border + h, border:border + w, :3] = img
    m = np.zeros(c.shape[:2], np.uint8)
    H_, W_ = m.shape
    r = radius
    cv2.rectangle(m, (r, 0), (W_ - r, H_), 255, -1)
    cv2.rectangle(m, (0, r), (W_, H_ - r), 255, -1)
    for cx, cy in [(r, r), (W_ - r, r), (r, H_ - r), (W_ - r, H_ - r)]:
        cv2.circle(m, (cx, cy), r, 255, -1)
    c[..., 3] = m
    return c


def paste(dst, c, cx, cy, scale=1.0, rot=0, alpha=1.0):
    """Paste an RGBA card onto dst (float or uint8 array), centered at (cx, cy), scaled and rotated. Edits dst in place."""
    if scale <= 0.01 or alpha <= 0:
        return
    c = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    if rot:
        h, w = c.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1)
        c = cv2.warpAffine(c, M, (w, h), borderValue=(0, 0, 0, 0))
    H, W = dst.shape[:2]
    h, w = c.shape[:2]
    x, y = int(cx - w / 2), int(cy - h / 2)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    a = c[y0 - y:y1 - y, x0 - x:x1 - x, 3:4] / 255.0 * alpha
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - a) + c[y0 - y:y1 - y, x0 - x:x1 - x, :3] * a


def tilt(img, angle, size, scale=1.0, dx=0, dy=0, focal=1400):
    """Turn a flat image around its vertical axis (3D perspective). Returns the warped frame and its 4 corners."""
    W, H = size
    h, w = img.shape[:2]
    a = np.radians(angle)
    pts = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        X = x * np.cos(a) * scale
        Z = x * np.sin(a) * scale + focal
        Y = y * scale
        pts.append([W / 2 + dx + X * focal / Z, H / 2 + dy + Y * focal / Z])
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(pts))
    return cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0), np.float32(pts)


# easing -------------------------------------------------------------------
def progress(t, start, duration):
    """0 before start, 1 after start + duration, linear in between."""
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return float(min(1, max(0, (t - start) / duration)))


def ease_out(k):
    return 1 - (1 - k) ** 3


def ease_in_out(k):
    return 3 * k * k - 2 * k * k * k


def pop(t, start, duration=0.18, overshoot=0.12):
    """Scale for a pop-in: 0 before start, appears at full size with a quick bounce, settles at 1.
    (Same curve as the approved effects pack.)"""
    if t < start:
        return 0.0
    k = progress(t, start, duration)
    return 1.0 if k >= 1 else 1 + overshoot * np.sin(k * np.pi) * (1 - k)


def back_out(k, overshoot=2.0):
    """Ease that overshoots a little and settles (like GSAP back.out)."""
    k = min(1.0, max(0.0, k)) - 1
    return 1 + (overshoot + 1) * k ** 3 + overshoot * k ** 2


def round_mask(w, h, r):
    """Float mask (h, w) of a rounded rectangle, 1 inside."""
    w, h, r = int(w), int(h), int(max(1, min(r, w // 2, h // 2)))
    m = np.zeros((h, w), np.float32)
    cv2.rectangle(m, (r, 0), (w - r, h), 1, -1)
    cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
    for cx, cy in [(r, r), (w - r, r), (r, h - r), (w - r, h - r)]:
        cv2.circle(m, (cx, cy), r, 1, -1)
    return m


def placeholder(brand, label="YOUR SCREENSHOT", size=(720, 1280), dark=False):
    """A stand-in image in brand colors, used when the user has not given their own screenshots yet."""
    w, h = size
    bg = brand.rgb("primary") if dark else brand.rgb("secondary")
    fg = brand.rgb("light") if dark else brand.rgb("text")
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    pad = int(w * 0.08)
    for k in range(5):
        y = int(h * 0.25) + k * int(h * 0.09)
        d.rounded_rectangle((pad, y, w - pad - (k % 3) * int(w * 0.12), y + int(h * 0.035)), int(h * 0.017), fill=brand.tint("line", -0.05) if not dark else brand.tint("primary", 0.25))
    f = brand.font("label", max(14, int(w * 0.06)))
    d.text((w // 2, int(h * 0.12)), label, font=f, fill=fg, anchor="mm")
    return np.asarray(im)


def images_or_placeholders(paths, brand, count, size=(720, 1280), label="YOUR SCREENSHOT"):
    """The user's images (cycled to fill count), or brand-colored placeholders when none were given."""
    if paths:
        imgs = [load_image(p) for p in paths]
        return [imgs[k % len(imgs)] for k in range(count)]
    return [placeholder(brand, f"{label} {k + 1}", size, dark=(k % 3 == 1)) for k in range(count)]


def fit_font(brand, role, size, s, max_width, weight=800, width=100, min_size=24):
    """Largest font (up to size) that keeps s within max_width pixels."""
    while size > min_size:
        f = brand.font(role, size, weight, width)
        if f.getlength(s) <= max_width:
            return f
        size -= 4
    return brand.font(role, min_size, weight, width)


def text_on_path(layer, path, s, font, start, fill=(255, 255, 255, 255), shadow=True):
    """Draw s along a polyline path (N x 2 points) on an RGBA PIL layer, starting at arc length start.
    Returns the arc length where the text ended."""
    path = np.asarray(path, np.float32)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
    pos = start
    for ch in s:
        adv = font.getlength(ch)
        mid = pos + adv / 2
        if mid > seg[-1]:
            break
        x = np.interp(mid, seg, path[:, 0])
        y = np.interp(mid, seg, path[:, 1])
        x2 = np.interp(min(seg[-1], mid + 2), seg, path[:, 0])
        y2 = np.interp(min(seg[-1], mid + 2), seg, path[:, 1])
        x1 = np.interp(max(0, mid - 2), seg, path[:, 0])
        y1 = np.interp(max(0, mid - 2), seg, path[:, 1])
        ang = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        if ch.strip():
            box = int(font.size * 2)
            g = Image.new("RGBA", (box, box), (0, 0, 0, 0))
            if shadow:
                sh = Image.new("RGBA", (box, box), (0, 0, 0, 0))
                ImageDraw.Draw(sh).text((box / 2, box / 2), ch, font=font, anchor="mm", fill=(0, 0, 0, 120))
                g.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
            ImageDraw.Draw(g).text((box / 2, box / 2), ch, font=font, anchor="mm", fill=fill)
            g = g.rotate(-ang, resample=Image.BICUBIC)
            layer.alpha_composite(g, (int(x - box / 2), int(y - box / 2)))
        pos += adv
    return pos


def crop(img, box):
    """Crop to the part that matters. box = 'x0,y0,x1,y1' as fractions (0..1) of the image, or None."""
    if not box:
        return img
    x0, y0, x1, y1 = (float(v) for v in box.split(","))
    h, w = img.shape[:2]
    return img[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
