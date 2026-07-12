# -*- coding: utf-8 -*-
"""重新处理帧"""
import cv2
import numpy as np
from PIL import Image
import os

VIDEOS_DIR = "videos"
OUTPUT_DIR = "assets/frames"
TARGET_H = 220

def extract_and_process(video_path, output_dir, start_frame=0, end_frame=None):
    """提取并处理帧"""
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if end_frame is None:
        end_frame = total

    print(f"  Extracting frames {start_frame}-{end_frame}...")

    frame_idx = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if start_frame <= frame_idx < end_frame:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
            arr = np.array(img)

            # 去除白色背景
            r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
            is_bg = (r > 200) & (g > 200) & (b > 200) & ((r.astype(int) - b.astype(int)) < 30)
            arr[is_bg, 3] = 0

            result = Image.fromarray(arr, "RGBA")

            # 裁剪
            bbox = result.getbbox()
            if bbox:
                pad = 3
                result = result.crop((max(0, bbox[0]-pad), max(0, bbox[1]-pad),
                                      min(img.width, bbox[2]+pad), min(img.height, bbox[3]+pad)))

            # 缩放
            scale = TARGET_H / result.height
            result = result.resize((int(result.width * scale), TARGET_H), Image.LANCZOS)

            result.save(os.path.join(output_dir, f"{saved:04d}.png"))
            saved += 1

        frame_idx += 1

    cap.release()
    print(f"    Saved {saved} frames")
    return saved

# 1. 工作中：跳过开头，只保留敲键盘部分（大约30-100帧）
print("工作中...")
extract_and_process(
    os.path.join(VIDEOS_DIR, "工作中.mp4"),
    os.path.join(OUTPUT_DIR, "work"),
    start_frame=30,
    end_frame=100
)

# 2. 待机：只保留一帧作为静态图
print("待机（静态）...")
cap = cv2.VideoCapture(os.path.join(VIDEOS_DIR, "待机.mp4"))
cap.set(cv2.CAP_PROP_POS_FRAMES, 60)  # 选中间帧
ret, frame = cap.read()
cap.release()

if ret:
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    arr = np.array(img)
    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    is_bg = (r > 200) & (g > 200) & (b > 200) & ((r.astype(int) - b.astype(int)) < 30)
    arr[is_bg, 3] = 0
    result = Image.fromarray(arr, "RGBA")
    bbox = result.getbbox()
    if bbox:
        result = result.crop((max(0, bbox[0]-3), max(0, bbox[1]-3),
                              min(img.width, bbox[2]+3), min(img.height, bbox[3]+3)))
    scale = TARGET_H / result.height
    result = result.resize((int(result.width * scale), TARGET_H), Image.LANCZOS)

    idle_dir = os.path.join(OUTPUT_DIR, "idle")
    os.makedirs(idle_dir, exist_ok=True)
    result.save(os.path.join(idle_dir, "0000.png"))
    print(f"    Saved static idle frame")

# 3. 其他状态保持不变
print("其他状态已存在，跳过")

print("\nDone!")
