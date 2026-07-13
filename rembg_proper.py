# -*- coding: utf-8 -*-
"""用 rembg 处理原始帧，保留透明边缘细节"""
from io import BytesIO
from rembg import remove, new_session
from PIL import Image
import os
import sys

SRC_DIR = "assets/frames"
OUT_DIR = "assets/frames_nobg"
TARGET_H = 150
CROP_PAD = 8

DEFAULT_STATES = [
    "idle", "work", "exhausted", "greet", "cute", "shy",
    "yawn", "confused", "sad", "miss", "slacking",
]


def iter_states():
    states = sys.argv[1:]
    return states or DEFAULT_STATES


def clear_pngs(folder):
    if not os.path.exists(folder):
        return
    for fname in os.listdir(folder):
        if fname.endswith(".png"):
            os.remove(os.path.join(folder, fname))


def crop_with_padding(img):
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return img

    left = max(0, bbox[0] - CROP_PAD)
    top = max(0, bbox[1] - CROP_PAD)
    right = min(img.width, bbox[2] + CROP_PAD)
    bottom = min(img.height, bbox[3] + CROP_PAD)
    return img.crop((left, top, right, bottom))


print("Loading AI model...")
session = new_session("u2net")

for state in iter_states():
    src = os.path.join(SRC_DIR, state)
    out = os.path.join(OUT_DIR, state)

    if not os.path.exists(src):
        print(f"  [SKIP] {src} not found")
        continue

    os.makedirs(out, exist_ok=True)
    clear_pngs(out)
    frames = sorted([f for f in os.listdir(src) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for i, fname in enumerate(frames):
        input_path = os.path.join(src, fname)
        output_path = os.path.join(out, fname)

        with open(input_path, "rb") as f:
            input_data = f.read()

        output_data = remove(input_data, session=session)
        img = Image.open(BytesIO(output_data)).convert("RGBA")
        img = crop_with_padding(img)

        if img.height != TARGET_H:
            scale = TARGET_H / img.height
            img = img.resize((max(1, int(img.width * scale)), TARGET_H), Image.LANCZOS)

        img.save(output_path, "PNG")

        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(frames)}")

    print("  Done")

print("\nAll done!")
