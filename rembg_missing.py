# -*- coding: utf-8 -*-
"""处理缺失的状态"""
from rembg import remove, new_session
from PIL import Image
import os

FRAMES_DIR = "assets/frames"
OUTPUT_DIR = "assets/frames_clean"

# 检查哪些状态缺失
missing = []
for state in ["sad", "slacking", "miss"]:
    src = os.path.join(FRAMES_DIR, state)
    dst = os.path.join(OUTPUT_DIR, state)
    src_count = len([f for f in os.listdir(src) if f.endswith('.png')]) if os.path.exists(src) else 0
    dst_count = len([f for f in os.listdir(dst) if f.endswith('.png')]) if os.path.exists(dst) else 0
    if src_count > 0 and dst_count == 0:
        missing.append(state)

if not missing:
    print("No missing states")
    exit()

print(f"Loading AI model...")
session = new_session("u2net")

for state in missing:
    src_dir = os.path.join(FRAMES_DIR, state)
    dst_dir = os.path.join(OUTPUT_DIR, state)
    os.makedirs(dst_dir, exist_ok=True)

    frames = sorted([f for f in os.listdir(src_dir) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for i, fname in enumerate(frames):
        with open(os.path.join(src_dir, fname), "rb") as f:
            input_data = f.read()
        output_data = remove(input_data, session=session)
        with open(os.path.join(dst_dir, fname), "wb") as f:
            f.write(output_data)
        if (i+1) % 30 == 0:
            print(f"  {i+1}/{len(frames)}")

    print(f"  Done")

print("\nAll done!")
