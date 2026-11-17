"""Transition: the camera zooms into you and comes out of the next clip."""
import os

import cv2
import numpy as np

from kfx import Clip, as_float, concat_audio

NAME = "Zoom-through cut"
ABOUT = "Transition: zoom into you and come out of the next clip."
NEEDS_CUTOUT = False
NEEDS_WORDS = False


def add_args(p):
    p.add_argument("--next", required=True, help="the video to cut to")
    p.add_argument("--next-start", type=float, default=0.0)
    p.add_argument("--next-end", type=float, help="default: 2 seconds after --next-start")
    p.add_argument("--length", type=float, default=0.3, help="seconds of zoom on each side of the cut (default 0.3)")


def _second(clip, args):
    if not hasattr(args, "_clip_b"):
        end = args.next_end if args.next_end is not None else args.next_start + 2.0
        args._clip_b = Clip(args.next, args.next_start, end)
    return args._clip_b


def audio(clip, args):
    b = _second(clip, args)
    return concat_audio([clip.audio, b.audio], os.path.join(clip.dir, "zoomthrough-audio.m4a"))


def zoom_blur(img, z, blur, cx, cy, W, H):
    acc = np.zeros_like(img, dtype=np.float32)
    K = 8
    for k in range(K):
        zz = z * (1 + blur * k / K)
        M = np.float32([[zz, 0, cx - zz * cx], [0, zz, cy - zz * cy]])
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / K


def render(clip, out, brand, args):
    W, H = clip.size
    b = _second(clip, args)
    T = args.length
    cx, cy = args.focus
    tz = clip.duration - T
    for i in range(clip.n):
        t = clip.t(i)
        f = as_float(clip.rgb(i))
        if t >= tz:
            e = ((t - tz) / T) ** 2.2
            f = zoom_blur(f, 1 + 2.2 * e, 0.35 * e, cx, cy, W, H)
        out.write(f)
    for j in range(b.n):
        t = b.t(j)
        f = as_float(b.rgb(j))
        if t < T:
            e = (1 - t / T) ** 2.2
            f = zoom_blur(f, 1 + 1.6 * e, 0.3 * e, W / 2, H * 0.36, W, H)
        out.write(f)
