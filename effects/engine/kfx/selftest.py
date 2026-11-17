"""Engine self-test. Proves every part works on the user's own clip before any real effect runs:
frames, sound, person cutout, word timings and brand fonts/colors.

Output: the speaker on a brand-colored background, the word being spoken at the top,
and the keyword popping in the brand's accent color when it is said.
"""
import numpy as np

from .draw import as_float, comp, pop, text

NAME = "Engine self-test"
ABOUT = "Checks video, sound, cutout, words and brand on your clip."
NEEDS_CUTOUT = True
NEEDS_WORDS = True


def add_args(parser):
    parser.add_argument("--keyword", help="a word you say in the clip; it pops in when spoken")


def render(clip, out, brand, args):
    bg = np.zeros((clip.H, clip.W, 3), np.float32) + brand.rgb("background")
    hits = clip.find(args.keyword) if args.keyword else []
    small = brand.font("body", int(clip.W * 0.06), weight=700)
    for i in range(clip.n):
        t = clip.t(i)
        frame = comp(bg, as_float(clip.rgb(i)), clip.alpha(i))
        word = clip.word_at(t)
        if word:
            frame = text(frame, (clip.W // 2, int(clip.H * 0.12)), word, small, fill=brand.rgb("text"), shadow=False)
        for h in hits:
            s = pop(t, h.start)
            if s and t < h.end + 0.8:
                f = brand.font("display", max(8, int(clip.W * 0.12 * s)), weight=900, width=125)
                frame = text(frame, (clip.W // 2, int(clip.H * 0.80)), h.text.strip(".,!?").upper(), f,
                             fill=brand.rgb("primary"), shadow=False)
        out.write(frame)
