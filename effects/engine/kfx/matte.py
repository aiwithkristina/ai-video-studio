"""Person cutout (alpha matte) for every frame, so effects can put things behind the speaker.

Uses Robust Video Matting (https://github.com/PeterL1n/RobustVideoMatting, GPL-3.0).
It is downloaded by PyTorch on first use and is not part of this repository.
"""
import os

import cv2
import numpy as np


def _device(torch):
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model():
    try:
        import torch
    except ImportError:
        raise SystemExit("This effect cuts the person out of the background and needs PyTorch: pip install torch")
    model = torch.hub.load("PeterL1n/RobustVideoMatting", "resnet50", trust_repo=True)
    dev = _device(torch)
    return torch, model.eval().to(dev), dev


def compute(frame_paths, out_dir, downsample=0.4, warmup=3):
    """Write a_00001.png ... next to the frames. Soft edges, slightly eroded so no background halo shows."""
    os.makedirs(out_dir, exist_ok=True)
    torch, model, dev = load_model()
    rec = [None] * 4

    def step(path):
        nonlocal rec
        rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        x = torch.from_numpy(rgb).permute(2, 0, 1).float().div(255).unsqueeze(0).to(dev)
        _, pha, *rec = model(x, *rec, downsample_ratio=downsample)
        return pha[0, 0].cpu().numpy()

    kernel = np.ones((3, 3), np.uint8)
    with torch.no_grad():
        for _ in range(warmup):  # the model is recurrent: let it settle on the first frame
            step(frame_paths[0])
        for i, p in enumerate(frame_paths, 1):
            a = np.clip((step(p) - 0.25) / 0.6, 0, 1)
            a = cv2.GaussianBlur(cv2.erode(a, kernel), (0, 0), 1.0)
            cv2.imwrite(os.path.join(out_dir, f"a_{i:05d}.png"), (a * 255).astype(np.uint8))
            if i % 30 == 0 or i == len(frame_paths):
                print(f"  cutout {i}/{len(frame_paths)}", flush=True)
