# -*- coding: utf-8 -*-
"""直接提取原始帧，不做任何处理"""
import cv2
from PIL import Image
import os

VIDEOS_DIR = "videos"
OUTPUT_DIR = "assets/frames"
TARGET_H = 110

states = {
    "打招呼": "greet",
    "待机": "idle",
    "工作中": "work",
    "哈欠": "yawn",
    "害羞": "shy",
    "力竭了": "exhausted",
    "卖萌": "cute",
    "懵圈": "confused",
    "摸鱼": "slacking",
    "委屈屈": "sad",
    "想你": "miss",
}

for cn_name, en_name in states.items():
    video_path = os.path.join(VIDEOS_DIR, f"{cn_name}.mp4")
    output_dir = os.path.join(OUTPUT_DIR, en_name)

    if not os.path.exists(video_path):
        print(f"  [SKIP] {cn_name}.mp4")
        continue

    os.makedirs(output_dir, exist_ok=True)
    print(f"  {cn_name} -> {en_name}...")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 待机只取一帧
    if en_name == "idle":
        cap.set(cv2.CAP_PROP_POS_FRAMES, 60)
        ret, frame = cap.read()
        if ret:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            scale = TARGET_H / img.height
            img = img.resize((int(img.width * scale), TARGET_H), Image.LANCZOS)
            img.save(os.path.join(output_dir, "0000.png"))
        cap.release()
        print(f"    1 frame")
        continue

    # 工作中裁剪
    start = 30 if en_name == "work" else 0
    end = 100 if en_name == "work" else total

    frame_idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if start <= frame_idx < end:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            scale = TARGET_H / img.height
            img = img.resize((int(img.width * scale), TARGET_H), Image.LANCZOS)
            img.save(os.path.join(output_dir, f"{saved:04d}.png"))
            saved += 1
        frame_idx += 1

    cap.release()
    print(f"    {saved} frames")

print("Done!")
