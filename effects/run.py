#!/usr/bin/env python3
"""Run one of Kristina's effects on your own video.

    python effects/run.py list
    python effects/run.py check
    python effects/run.py selftest --video my.mp4 --start 3 --end 7 --transcript words.json --keyword ai
    python effects/run.py 05 --video my.mp4 --start 12 --end 16 --transcript words.json --keyword annoying

Common options (every effect):
    --video       your video file (any size; it is cropped to 9:16)
    --start/--end the seconds of the video to use (default: the whole video)
    --transcript  word timings JSON (ElevenLabs or Whisper); needed by effects that react to words
    --brand       brand.json with your colors, fonts and handle (default: Kristina's look)
    --out         where to save the mp4 (default: renders/<video>-<effect>.mp4)
    --focus       where your face is, as fractions of the frame (default 0.52,0.33)
Output is always a vertical 1080x1920 video at 30 fps.
Each effect adds its own options; see: python effects/run.py 05 --help
"""
import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))

import kfx  # noqa: E402
from kfx import selftest  # noqa: E402


def effect_dirs():
    return sorted(d for d in os.listdir(HERE)
                  if os.path.isfile(os.path.join(HERE, d, "effect.py")))


def load_effect(name):
    if name == "selftest":
        return "selftest", selftest
    matches = [d for d in effect_dirs() if d == name or d.split("-", 1)[0] == name.zfill(2) or d.split("-", 1)[-1] == name]
    if not matches:
        raise SystemExit(f"No effect '{name}'. Run: python effects/run.py list")
    folder = matches[0]
    spec = importlib.util.spec_from_file_location(f"effect_{folder}", os.path.join(HERE, folder, "effect.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.FOLDER = os.path.join(HERE, folder)
    return folder, mod


def cmd_list():
    names = effect_dirs()
    if not names:
        print("No effects installed yet.")
    for d in names:
        _, mod = load_effect(d)
        flags = [x for x, on in (("cutout", getattr(mod, "NEEDS_CUTOUT", False)),
                                 ("words", getattr(mod, "NEEDS_WORDS", False))) if on]
        print(f"{d:28s} {mod.NAME}: {mod.ABOUT}" + (f"  [{', '.join(flags)}]" if flags else ""))


def cmd_check():
    ok = True
    try:
        print("ffmpeg:   ", kfx.video.ffmpeg_bin())
    except SystemExit as e:
        print("ffmpeg:    MISSING.", e)
        ok = False
    for mod, why in (("numpy", "required"), ("cv2", "required (pip install opencv-python)"),
                     ("PIL", "required (pip install pillow)"), ("torch", "only for cutout effects (pip install torch)")):
        try:
            m = __import__(mod)
            print(f"{mod + ':':10s} {getattr(m, '__version__', 'ok')}")
        except ImportError:
            print(f"{mod + ':':10s} MISSING, {why}")
            ok = ok and mod == "torch"
    try:
        kfx.Brand().font("display", 40)
        print("fonts:     ok")
    except Exception as e:  # noqa: BLE001
        print("fonts:     could not load:", e)
        ok = False
    print("Ready." if ok else "Fix the items marked MISSING, then run check again.")
    return 0 if ok else 1


def cmd_effect(name, argv):
    folder, mod = load_effect(name)
    p = argparse.ArgumentParser(prog=f"run.py {name}", description=f"{mod.NAME}: {mod.ABOUT}")
    p.add_argument("--video", required=True)
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None)
    p.add_argument("--transcript")
    p.add_argument("--brand")
    p.add_argument("--out")
    p.add_argument("--focus", default="0.52,0.33", help="face position as x,y fractions of the frame")
    if hasattr(mod, "add_args"):
        mod.add_args(p)
    args = p.parse_args(argv)

    if getattr(mod, "NEEDS_WORDS", False) and not args.transcript:
        p.error("this effect reacts to spoken words: add --transcript words.json")
    clip = kfx.Clip(args.video, args.start, args.end, args.transcript)
    fx, fy = (float(v) for v in args.focus.split(","))
    args.focus = (int(fx * clip.W), int(fy * clip.H))
    brand = kfx.Brand.load(args.brand)
    if getattr(mod, "NEEDS_CUTOUT", False):
        clip.ensure_matte()
    out_path = args.out or os.path.join("renders", f"{os.path.splitext(os.path.basename(args.video))[0]}-{folder}.mp4")
    audio = mod.audio(clip, args) if hasattr(mod, "audio") else clip.audio
    print(f"Rendering {mod.NAME} ...", flush=True)
    with kfx.Writer(out_path, clip.size, clip.fps, audio=audio) as out:
        mod.render(clip, out, brand, args)
    print("Saved:", os.path.abspath(out_path))
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "list":
        return cmd_list() or 0
    if argv[0] == "check":
        return cmd_check()
    return cmd_effect(argv[0], argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
