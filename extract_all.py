# -*- coding: utf-8 -*-
"""提取状态视频的原始帧"""
import cv2
from PIL import Image
import os
import sys

VIDEOS_DIR = "videos"
OUTPUT_BASE = "assets/frames"

STATE_FILES = {
    "idle": "待机.mp4",
    "work": "工作中.mp4",
    "exhausted": "力竭了.mp4",
    "greet": "打招呼.mp4",
    "cute": "卖萌.mp4",
    "shy": "害羞.mp4",
    "yawn": "哈欠.mp4",
    "confused": "懵圈.mp4",
    "sad": "委屈屈.mp4",
    "miss": "想你.mp4",
    "slacking": "摸鱼.mp4",
}

STATES = list(STATE_FILES.keys())


def clear_pngs(folder):
    if not os.path.exists(folder):
        return
    for fname in os.listdir(folder):
        if fname.endswith(".png"):
            os.remove(os.path.join(folder, fname))


def iter_states():
    args = sys.argv[1:]
    if not args:
        return STATES
    return [state for state in args if state in STATE_FILES]


for state in iter_states():
    video_path = os.path.join(VIDEOS_DIR, STATE_FILES[state])
    output_dir = os.path.join(OUTPUT_BASE, state)

    if not os.path.exists(video_path):
        print(f"  [SKIP] {video_path} not found")
        continue

    os.makedirs(output_dir, exist_ok=True)
    clear_pngs(output_dir)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"  {state}: {total} frames @ {fps}fps")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        img.save(os.path.join(output_dir, f"{frame_idx:04d}.png"))
        frame_idx += 1

    cap.release()
    print(f"    -> Saved {frame_idx} frames")

print("\nDone!")
