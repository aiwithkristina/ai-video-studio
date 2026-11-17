"""Your words write themselves along the outline of your body, up one side, over your head and down the other."""
import cv2
import numpy as np
from PIL import Image

from kfx import as_float, text_on_path

NAME = "Silhouette words"
ABOUT = "Your words write themselves along your outline, over your head, as you say them."
NEEDS_CUTOUT = True
NEEDS_WORDS = True


def add_args(p):
    p.add_argument("--offset", type=int, default=34, help="gap between you and the text in pixels (default 34)")
    p.add_argument("--cut", type=float, default=0.6, help="ignore the outline below this height, e.g. a desk (fraction, default 0.6)")
    p.add_argument("--size", type=int, default=46, help="text size (default 46)")
    p.add_argument("--color", default="light", help="brand color for the text (default light = white)")
    p.add_argument("--text", help="fixed text instead of the transcript (typed in over the clip)")


def outline_path(clip, offset, cut):
    """Union of your outline over the clip, pushed out by offset, walked bottom-left -> over the head -> bottom-right."""
    m = None
    for i in range(0, clip.n, max(1, clip.n // 30)):
        a = (clip.alpha(i) > 0.5).astype(np.uint8)
        m = a if m is None else (m | a)
    d = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * offset + 1, 2 * offset + 1)))
    cs, _ = cv2.findContours(d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not cs:
        raise SystemExit("No person found in the clip, so there is no outline to follow.")
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    c = c[c[:, 1] < cut * clip.H]
    edge = offset + 4                      # where you touch the frame edge there is no outline to follow
    c = c[(c[:, 0] > edge) & (c[:, 0] < clip.W - edge) & (c[:, 1] > edge)]
    if len(c) < 20:
        raise SystemExit("The outline is too short to write on. Try a lower --cut or a wider shot.")
    top = np.argmin(c[:, 1])
    pts = np.roll(c, -top, axis=0)
    left = pts[pts[:, 0] < pts[0, 0]]
    right = pts[pts[:, 0] >= pts[0, 0]]
    left = left[np.argsort(-left[:, 1])]
    right = right[np.argsort(right[:, 1])]
    path = np.vstack([left, right])
    k = 41
    pad = np.pad(path, ((k, k), (0, 0)), mode="edge")
    sm = np.array([pad[i:i + 2 * k + 1].mean(0) for i in range(len(path))])
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(sm, axis=0).T))]
    s = np.arange(0, seg[-1], 4.0)
    return np.c_[np.interp(s, seg, sm[:, 0]), np.interp(s, seg, sm[:, 1])]


def render(clip, out, brand, args):
    W, H = clip.size
    path = outline_path(clip, args.offset, args.cut)
    font = brand.font("body", args.size, 700)
    color = brand.rgb(args.color) + (255,)
    if args.text:
        full = args.text
        reveal = [(len(full[:j + 1]), (j + 1) / len(full) * max(0.5, clip.duration - 0.5)) for j in range(len(full))]
    else:
        full, reveal = "", []
        for w in clip.words:
            full += ("" if not full else " ") + w.text
            reveal.append((len(full), w.start))
    for i in range(clip.n):
        t = clip.t(i)
        upto = 0
        for n_chars, t0 in reveal:
            if t >= t0:
                upto = n_chars
        fr = clip.rgb(i)
        if upto:
            L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            text_on_path(L, path, full[:upto], font, start=10, fill=color)
            la = np.asarray(L).astype(np.float32)
            al = la[..., 3:4] / 255
            fr = as_float(fr) * (1 - al) + la[..., :3] * al
        out.write(fr)
