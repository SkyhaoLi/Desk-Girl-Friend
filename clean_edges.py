# -*- coding: utf-8 -*-
"""清理所有帧的边缘噪点"""
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage
import os

FRAMES_DIR = "assets/frames"
TARGET_H = 110

states = ["idle", "work", "exhausted", "greet", "cute", "shy",
          "yawn", "confused", "sad", "miss", "slacking"]

for state in states:
    state_dir = os.path.join(FRAMES_DIR, state)
    if not os.path.exists(state_dir):
        continue

    print(f"Processing {state}...")
    frames = sorted([f for f in os.listdir(state_dir) if f.endswith('.png')])

    for fname in frames:
        path = os.path.join(state_dir, fname)
        img = Image.open(path).convert("RGBA")
        arr = np.array(img, dtype=np.float64)

        r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

        # 1. 二值化alpha
        a_bin = np.where(a > 100, 255, 0).astype(np.uint8)

        # 2. 腐蚀去除边缘噪点
        a_eroded = ndimage.binary_erosion(a_bin > 0, iterations=1).astype(np.uint8) * 255

        # 3. 膨胀恢复
        a_final = ndimage.binary_dilation(a_eroded > 0, iterations=1).astype(np.uint8) * 255

        arr[:,:,3] = a_final

        # 4. 去除边缘附近的白色像素
        # 找到边缘区域
        edge_mask = ndimage.binary_dilation(a_final > 0, iterations=2) & (a_final == 0)
        near_edge = ndimage.binary_dilation(edge_mask, iterations=3)

        # 在边缘附近降低白色
        brightness = (r + g + b) / 3
        white_near_edge = near_edge & (brightness > 180) & (a_final > 0)

        # 向量化处理
        arr[white_near_edge, 0] = np.minimum(255, r[white_near_edge] * 0.85)
        arr[white_near_edge, 1] = np.minimum(255, g[white_near_edge] * 0.85)
        arr[white_near_edge, 2] = np.minimum(255, b[white_near_edge] * 0.85)

        result = Image.fromarray(arr.astype(np.uint8), "RGBA")

        # 缩放
        scale = TARGET_H / result.height
        result = result.resize((int(result.width * scale), TARGET_H), Image.LANCZOS)

        result.save(path)

    print(f"  Done: {len(frames)} frames")

print("\nAll done!")
