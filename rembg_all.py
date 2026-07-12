# -*- coding: utf-8 -*-
"""用rembg AI去除所有帧的背景"""
from rembg import remove, new_session
from PIL import Image
import os

FRAMES_DIR = "assets/frames"
OUTPUT_DIR = "assets/frames_clean"

states = ["idle", "work", "exhausted", "greet", "cute", "shy",
          "yawn", "confused", "sad", "miss", "slacking"]

print("Loading AI model...")
session = new_session("u2net")

for state in states:
    state_dir = os.path.join(FRAMES_DIR, state)
    out_dir = os.path.join(OUTPUT_DIR, state)

    if not os.path.exists(state_dir):
        continue

    os.makedirs(out_dir, exist_ok=True)
    frames = sorted([f for f in os.listdir(state_dir) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for fname in frames:
        input_path = os.path.join(state_dir, fname)
        output_path = os.path.join(out_dir, fname)

        with open(input_path, "rb") as f:
            input_data = f.read()

        output_data = remove(input_data, session=session)

        with open(output_path, "wb") as f:
            f.write(output_data)

    print(f"  Done")

print("\nAll done!")
