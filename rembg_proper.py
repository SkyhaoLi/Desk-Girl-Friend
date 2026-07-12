# -*- coding: utf-8 -*-
"""用rembg处理原始尺寸帧，保持人物完整"""
from rembg import remove, new_session
from PIL import Image
import os

SRC_DIR = "assets/frames"
OUT_DIR = "assets/frames_nobg"
TARGET_H = 250

states = ["idle", "work", "exhausted", "greet", "cute", "shy",
          "yawn", "confused", "sad", "miss", "slacking"]

print("Loading AI model...")
session = new_session("u2net")

for state in states:
    src = os.path.join(SRC_DIR, state)
    out = os.path.join(OUT_DIR, state)

    if not os.path.exists(src):
        continue

    os.makedirs(out, exist_ok=True)
    frames = sorted([f for f in os.listdir(src) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for i, fname in enumerate(frames):
        input_path = os.path.join(src, fname)
        output_path = os.path.join(out, fname)

        # 读取原始尺寸图片
        with open(input_path, "rb") as f:
            input_data = f.read()

        # AI扣图
        output_data = remove(input_data, session=session)

        # 保存并缩放
        from io import BytesIO
        img = Image.open(BytesIO(output_data)).convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        # 缩放到目标高度
        scale = TARGET_H / img.height
        img = img.resize((int(img.width * scale), TARGET_H), Image.LANCZOS)

        img.save(output_path, "PNG")

        if (i+1) % 30 == 0:
            print(f"  {i+1}/{len(frames)}")

    print(f"  Done")

print("\nAll done!")
