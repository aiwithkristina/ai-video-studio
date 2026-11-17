"""A Clip is one stretch of the user's video, ready for an effect: frames, cutout, words, audio.

    clip = Clip("my-video.mp4", start=12.0, end=16.5, transcript="words.json")
    clip.n             number of frames
    clip.rgb(i)        frame i as an RGB array (H, W, 3)
    clip.alpha(i)      person cutout for frame i, floats 0..1 (H, W); computed once, then cached
    clip.words         spoken words, re-timed so the clip starts at 0
    clip.find("ai")    the moments a keyword is said
    clip.audio         the clip's sound (or None)

Frames and cutouts are cached in ~/.cache/kfx/clips, so re-rendering after a tweak is fast.
"""
import glob
import hashlib
import json
import os

import cv2
import numpy as np

from . import matte as _matte
from . import video as _video
from . import words as _words


def cache_root():
    d = os.environ.get("KFX_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "kfx", "clips")
    os.makedirs(d, exist_ok=True)
    return d


class Clip:
    def __init__(self, video, start=0.0, end=None, transcript=None, size=(1080, 1920), fps=30):
        if not os.path.isfile(video):
            raise SystemExit(f"Video not found: {video}")
        if end is not None and end <= start:
            raise SystemExit("--end must be after --start")
        self.video = os.path.abspath(video)
        self.start, self.end = float(start), (float(end) if end is not None else None)
        self.size, self.fps = tuple(size), fps
        self.W, self.H = self.size

        st = os.stat(self.video)
        key = json.dumps([self.video, st.st_size, st.st_mtime, self.start, self.end, self.size, fps])
        self.dir = os.path.join(cache_root(), hashlib.sha1(key.encode()).hexdigest()[:16])
        self._frames_dir = os.path.join(self.dir, "frames")
        self._alpha_dir = os.path.join(self.dir, "alpha")
        self._prepare()

        self.words = []
        if transcript:
            self.words = _words.window(_words.load_words(transcript), self.start, self.end)

    # setup -----------------------------------------------------------------
    def _prepare(self):
        done = os.path.join(self.dir, "frames.done")
        if not os.path.exists(done):
            print(f"Reading video frames ({os.path.basename(self.video)}) ...", flush=True)
            for f in glob.glob(os.path.join(self._frames_dir, "*")):
                os.remove(f)
            _video.extract_frames(self.video, self.start, self.end, self.size, self.fps, self._frames_dir)
            audio = _video.extract_audio(self.video, self.start, self.end, os.path.join(self.dir, "audio.m4a"))
            with open(done, "w") as f:
                json.dump({"audio": bool(audio)}, f)
        self._paths = sorted(glob.glob(os.path.join(self._frames_dir, "f_*.jpg")))
        if not self._paths:
            raise SystemExit("No frames came out of the video. Check --start/--end against the video length.")
        with open(done) as f:
            has_audio = json.load(f).get("audio")
        self.audio = os.path.join(self.dir, "audio.m4a") if has_audio else None

    def ensure_matte(self):
        done = os.path.join(self.dir, "alpha.done")
        if not os.path.exists(done):
            print("Cutting the person out of the background (first time only) ...", flush=True)
            _matte.compute(self._paths, self._alpha_dir)
            open(done, "w").close()

    # frames ----------------------------------------------------------------
    @property
    def n(self):
        return len(self._paths)

    @property
    def duration(self):
        return self.n / self.fps

    def t(self, i):
        return i / self.fps

    def rgb(self, i):
        i = max(0, min(int(i), self.n - 1))
        return cv2.cvtColor(cv2.imread(self._paths[i]), cv2.COLOR_BGR2RGB)

    def alpha(self, i):
        self.ensure_matte()
        i = max(0, min(int(i), self.n - 1))
        return cv2.imread(os.path.join(self._alpha_dir, f"a_{i + 1:05d}.png"), 0).astype(np.float32) / 255

    def person_box(self, i=0):
        """Bounding box (x0, y0, x1, y1) and center x of the person in frame i, from the cutout."""
        a = self.alpha(i) > 0.5
        ys, xs = np.nonzero(a)
        if len(xs) == 0:
            return (0, 0, self.W, self.H), self.W // 2
        top = ys.min()
        head = xs[ys < top + max(20, (ys.max() - top) * 0.15)]
        return (int(xs.min()), int(top), int(xs.max()), int(ys.max())), int(np.median(head))

    # words -----------------------------------------------------------------
    def find(self, keywords):
        return _words.find(self.words, keywords)

    def word_at(self, t):
        return _words.word_at(self.words, t)
