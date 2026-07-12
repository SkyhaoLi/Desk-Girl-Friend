# -*- coding: utf-8 -*-
"""提取所有状态视频的帧"""
import cv2
import numpy as np
from PIL import Image
import os

VIDEOS_DIR = "videos"
OUTPUT_BASE = "assets/frames"

# 视频名称映射
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
    output_dir = os.path.join(OUTPUT_BASE, en_name)

    if not os.path.exists(video_path):
        print(f"  [SKIP] {video_path} not found")
        continue

    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  {cn_name}: {total} frames @ {fps}fps")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 转成PIL处理
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

        result.save(os.path.join(output_dir, f"{frame_idx:04d}.png"))
        frame_idx += 1

    cap.release()
    print(f"    -> Saved {frame_idx} frames")

print("\nDone!")
