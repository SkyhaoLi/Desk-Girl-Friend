# -*- coding: utf-8 -*-
"""兼容入口：原始抽帧请使用 extract_all.py"""
from extract_all import iter_states, clear_pngs, STATE_FILES
import cv2
from PIL import Image
import os

VIDEOS_DIR = "videos"
OUTPUT_DIR = "assets/frames"


def extract_state(state):
    video_path = os.path.join(VIDEOS_DIR, STATE_FILES[state])
    output_dir = os.path.join(OUTPUT_DIR, state)

    if not os.path.exists(video_path):
        print(f"  [SKIP] {video_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    clear_pngs(output_dir)
    print(f"  {state}...")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"    {total} frames @ {fps}fps")

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        img.save(os.path.join(output_dir, f"{frame_idx:04d}.png"))
        frame_idx += 1

    cap.release()
    print(f"    {frame_idx} frames")


if __name__ == "__main__":
    states = iter_states()
    for state in states:
        extract_state(state)
    print("Done!")
