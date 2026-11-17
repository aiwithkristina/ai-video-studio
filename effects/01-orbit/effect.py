"""Screenshots circle around you like a carousel, passing behind you and in front of you."""
import numpy as np

from kfx import as_float, card, images_or_placeholders, paste

NAME = "Orbit"
ABOUT = "Your screenshots circle around you, behind and in front."
NEEDS_CUTOUT = True
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--images", nargs="+", help="2 to 8 screenshots or photos (real ones from your apps)")
    p.add_argument("--count", type=int, default=5, help="how many cards orbit (default 5)")
    p.add_argument("--y", type=float, default=0.515, help="orbit height as a fraction of the frame (default 0.515, chest level)")
    p.add_argument("--seconds-per-turn", type=float, default=6.0)


def render(clip, out, brand, args):
    imgs = images_or_placeholders(args.images, brand, args.count, size=(450, 800))
    cards = [card(im, 150, 266, border=6, radius=18) for im in imgs]
    _, cx = clip.person_box(0)
    cy = args.y * clip.H
    radius = clip.W * 0.435
    for i in range(clip.n):
        t = clip.t(i)
        base = as_float(clip.rgb(i))
        a = clip.alpha(i)[..., None]
        fr = base.copy()
        th = t * 2 * np.pi / args.seconds_per_turn
        pos = []
        for k in range(len(cards)):
            ang = th + k * 2 * np.pi / len(cards)
            z = np.sin(ang)
            pos.append((z, k, cx + radius * np.cos(ang), cy + 50 * z, 0.7 + 0.5 * (z + 1) / 2))
        for z, k, x, y, s in sorted(pos):
            if z < 0:
                paste(fr, cards[k], x, y, s)
        fr = fr * (1 - a) + base * a          # you stay in front of the far cards
        for z, k, x, y, s in sorted(pos):
            if z >= 0:
                paste(fr, cards[k], x, y, s)  # near cards pass in front of you
        out.write(fr)
