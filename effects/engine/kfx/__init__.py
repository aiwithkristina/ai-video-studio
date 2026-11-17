"""kfx: the shared engine behind Kristina's video effects.

An effect is a folder with an effect.py that defines:

    NAME = "Digital zoom"
    ABOUT = "Punches in on the speaker when a keyword is said."
    NEEDS_CUTOUT = False          # True if it puts things behind the person
    NEEDS_WORDS = True            # True if it reacts to spoken words

    def add_args(parser):         # optional: the effect's own options
        parser.add_argument("--keyword", default="ai")

    def render(clip, out, brand, args):
        for i in range(clip.n):
            frame = clip.rgb(i)
            ...
            out.write(frame)

The engine handles the rest: reading the user's video, the cutout, word timings,
brand colors and fonts, and writing the final mp4 with sound. Run effects with effects/run.py.
"""
from .brand import Brand
from .clip import Clip
from .draw import (as_float, back_out, card, comp, crop, ease_in_out, ease_out, fit_font, images_or_placeholders, load_image,
                   paste, placeholder, pop, progress, round_mask, text, text_on_path, tilt)
from .video import Writer, concat_audio
from .words import Word, find, load_words, word_at

__version__ = "0.1.0"
