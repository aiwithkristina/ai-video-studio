"""Video in and out through ffmpeg: cut a clip into frames, pull its audio, write the result."""
import os
import shutil
import subprocess

import numpy as np


def ffmpeg_bin():
    """Find ffmpeg: KFX_FFMPEG, then PATH, then the imageio-ffmpeg package."""
    candidates = [os.environ.get("KFX_FFMPEG"), shutil.which("ffmpeg")]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    raise SystemExit("ffmpeg not found. Install it (on a Mac: brew install ffmpeg) or set KFX_FFMPEG to its path.")


def run_ffmpeg(args):
    subprocess.run([ffmpeg_bin(), "-v", "error", "-y", *args], check=True)


def fit_filter(size, fps):
    """Scale to cover the target size, then center-crop. Any input shape becomes a clean 9:16 (or whatever size is asked)."""
    w, h = size
    return f"fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"


def extract_frames(src, start, end, size, fps, outdir):
    os.makedirs(outdir, exist_ok=True)
    args = ["-ss", f"{start:.3f}", "-i", src]
    if end is not None:
        args = ["-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", src]
    run_ffmpeg([*args, "-an", "-vf", fit_filter(size, fps), "-q:v", "2", os.path.join(outdir, "f_%05d.jpg")])
    return len([f for f in os.listdir(outdir) if f.startswith("f_")])


def extract_audio(src, start, end, out):
    """Returns the audio path, or None when the video has no sound."""
    args = ["-ss", f"{start:.3f}", "-i", src]
    if end is not None:
        args = ["-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", src]
    try:
        run_ffmpeg([*args, "-vn", "-c:a", "aac", "-b:a", "192k", out])
    except subprocess.CalledProcessError:
        return None
    return out if os.path.exists(out) and os.path.getsize(out) > 0 else None


class Writer:
    """Pipe RGB frames into an H.264 mp4, with the clip's own audio underneath.

        with Writer("out.mp4", (1080, 1920), 30, audio=clip.audio) as out:
            out.write(frame)
    """

    def __init__(self, path, size, fps, audio=None, crf=20):
        self.size = tuple(size)
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        w, h = self.size
        cmd = [ffmpeg_bin(), "-v", "warning", "-y",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"]
        if audio:
            cmd += ["-i", audio]
        cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        if audio:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd.append(path)
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.count = 0

    def write(self, frame):
        frame = np.asarray(frame)
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[..., :3]
        h, w = frame.shape[:2]
        if (w, h) != self.size:
            raise ValueError(f"frame is {w}x{h}, writer expects {self.size[0]}x{self.size[1]}")
        self.proc.stdin.write(np.ascontiguousarray(np.clip(frame, 0, 255).astype(np.uint8)).tobytes())
        self.count += 1

    def close(self):
        if self.proc.stdin and not self.proc.stdin.closed:
            self.proc.stdin.close()
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed while writing {self.path}")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def concat_audio(paths, out):
    """Join several audio files end to end (used when an effect cuts from one clip to another)."""
    paths = [p for p in paths if p]
    if not paths:
        return None
    if len(paths) == 1:
        return paths[0]
    args = []
    for p in paths:
        args += ["-i", p]
    flt = "".join(f"[{k}:a]" for k in range(len(paths))) + f"concat=n={len(paths)}:v=0:a=1[a]"
    run_ffmpeg([*args, "-filter_complex", flt, "-map", "[a]", "-c:a", "aac", "-b:a", "192k", out])
    return out
