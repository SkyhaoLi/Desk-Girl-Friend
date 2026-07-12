# -*- coding: utf-8 -*-
"""一次性彻底清理边缘噪点"""
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

        # 1. 严格二值化alpha（只有0或255）
        a_bin = np.where(a > 128, 255, 0).astype(np.uint8)

        # 2. 腐蚀2次彻底去除边缘噪点
        a_eroded = ndimage.binary_erosion(a_bin > 0, iterations=2).astype(np.uint8) * 255

        # 3. 膨胀1次恢复一点
        a_final = ndimage.binary_dilation(a_eroded > 0, iterations=1).astype(np.uint8) * 255

        arr[:,:,3] = a_final

        # 4. 对边缘附近的白色像素进行去白处理
        # 创建边缘掩码
        dilated = ndimage.binary_dilation(a_final > 0, iterations=3)
        eroded = ndimage.binary_erosion(a_final > 0, iterations=3)
        edge = dilated & ~eroded

        # 在边缘区域，降低偏白像素的亮度
        r_new = r.copy()
        g_new = g.copy()
        b_new = b.copy()

        # 边缘附近的白色像素
        brightness = (r + g + b) / 3
        edge_white = edge & (brightness > 160) & (a_final > 0)

        # 降低这些像素的白色
        r_new[edge_white] = np.clip(r[edge_white] * 0.7 + 40, 0, 255)
        g_new[edge_white] = np.clip(g[edge_white] * 0.7 + 30, 0, 255)
        b_new[edge_white] = np.clip(b[edge_white] * 0.7 + 20, 0, 255)

        arr[:,:,0] = r_new
        arr[:,:,1] = g_new
        arr[:,:,2] = b_new

        result = Image.fromarray(arr.astype(np.uint8), "RGBA")

        # 缩放
        scale = TARGET_H / result.height
        result = result.resize((int(result.width * scale), TARGET_H), Image.LANCZOS)

        result.save(path)

    print(f"  Done: {len(frames)} frames")

print("\nAll cleaned!")
