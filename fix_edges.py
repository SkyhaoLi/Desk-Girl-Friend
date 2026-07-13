# -*- coding: utf-8 -*-
"""温和修复边缘 - 保留 alpha，只清理离散噪点和黑边污染"""
from PIL import Image
import numpy as np
from scipy import ndimage
import os
import sys

SRC_DIR = "assets/frames_nobg"
OUT_DIR = "assets/frames_fixed"

DEFAULT_STATES = [
    "idle", "work", "exhausted", "greet", "cute", "shy",
    "yawn", "confused", "sad", "miss", "slacking",
]

ALPHA_KEEP_THRESHOLD = 3
COLOR_SOURCE_ALPHA = 24
FRINGE_RADIUS = 3
MIN_COMPONENT_SIZE = 12


def iter_states():
    states = sys.argv[1:]
    return states or DEFAULT_STATES


def clear_pngs(folder):
    if not os.path.exists(folder):
        return
    for fname in os.listdir(folder):
        if fname.endswith(".png"):
            os.remove(os.path.join(folder, fname))


def remove_tiny_components(alpha):
    mask = alpha > ALPHA_KEEP_THRESHOLD
    if not mask.any():
        return alpha

    labels, count = ndimage.label(mask)
    if count <= 1:
        return alpha

    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = np.zeros(count + 1, dtype=bool)
    keep[int(np.argmax(sizes)) + 1] = True

    for idx, size in enumerate(sizes, start=1):
        if size >= MIN_COMPONENT_SIZE:
            keep[idx] = True

    cleaned = alpha.copy()
    remove_mask = (labels > 0) & ~keep[labels]
    cleaned[remove_mask] = 0
    return cleaned


def decontaminate_rgb(arr):
    alpha = arr[:, :, 3]
    source_mask = alpha >= COLOR_SOURCE_ALPHA
    fringe_mask = (alpha > 0) & ~source_mask

    if not source_mask.any() or not fringe_mask.any():
        return arr

    distance, nearest = ndimage.distance_transform_edt(~source_mask, return_indices=True)
    near_source = fringe_mask & (distance <= FRINGE_RADIUS)
    src_y = nearest[0][near_source]
    src_x = nearest[1][near_source]

    for channel_idx in range(3):
        channel = arr[:, :, channel_idx]
        channel[near_source] = channel[src_y, src_x]

    return arr


def clean_frame(img):
    arr = np.array(img, dtype=np.uint8)
    alpha = arr[:, :, 3].astype(np.uint8)

    alpha = remove_tiny_components(alpha)
    arr[:, :, 3] = alpha
    arr = decontaminate_rgb(arr)

    return Image.fromarray(arr, "RGBA")


def process_state(state):
    src = os.path.join(SRC_DIR, state)
    out = os.path.join(OUT_DIR, state)

    if not os.path.exists(src):
        print(f"  [SKIP] {src} not found")
        return

    os.makedirs(out, exist_ok=True)
    clear_pngs(out)
    frames = sorted([f for f in os.listdir(src) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for i, fname in enumerate(frames):
        img = Image.open(os.path.join(src, fname)).convert("RGBA")
        result = clean_frame(img)
        result.save(os.path.join(out, fname))

        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(frames)}")

    print("  Done")


def main():
    for state in iter_states():
        process_state(state)
    print("\nAll fixed!")


if __name__ == "__main__":
    main()
