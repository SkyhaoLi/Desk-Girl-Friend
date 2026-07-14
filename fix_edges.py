# -*- coding: utf-8 -*-
"""修复边缘 - 填内部洞 + alpha 锐化 + 去白边污染"""
from PIL import Image
import numpy as np
from scipy import ndimage
import os
import sys

SRC_DIR = "assets/frames_nobg"
OUT_DIR = "assets/frames_fixed"

DEFAULT_STATES = [
    "idle", "work", "exhausted", "greet", "cute", "shy",
    "yawn", "confused", "sad", "miss", "slacking",
]

ALPHA_KEEP_THRESHOLD = 3
COLOR_SOURCE_ALPHA = 20
FRINGE_RADIUS = 5
MIN_COMPONENT_SIZE = 12

# Alpha 锐化参数
ALPHA_LOW = 100
ALPHA_HIGH = 190

# 暗色偏移：-transparentcolor "black" 会把 RGB=(0,0,0) 变透明，
# 角色的黑色特征（头发、瞳孔）需要提升到此值以上才不会被吃掉
DARK_RGB_MIN = 8

# 抗锯齿：锐化后在边缘外圈补 1px 半透明过渡
AA_ALPHA = 120


def iter_states():
    states = sys.argv[1:]
    return states or DEFAULT_STATES


def clear_pngs(folder):
    if not os.path.exists(folder):
        return
    for fname in os.listdir(folder):
        if fname.endswith(".png"):
            os.remove(os.path.join(folder, fname))


def remove_tiny_components(alpha):
    """移除离散小噪点（保留最大连通区域 + 大于阈值的组件）"""
    mask = alpha > ALPHA_KEEP_THRESHOLD
    if not mask.any():
        return alpha

    labels, count = ndimage.label(mask)
    if count <= 1:
        return alpha

    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = np.zeros(count + 1, dtype=bool)
    keep[int(np.argmax(sizes)) + 1] = True

    for idx, size in enumerate(sizes, start=1):
        if size >= MIN_COMPONENT_SIZE:
            keep[idx] = True

    cleaned = alpha.copy()
    remove_mask = (labels > 0) & ~keep[labels]
    cleaned[remove_mask] = 0
    return cleaned


def fill_interior_holes(arr):
    """填充被不透明区域包围的内部洞（角色身体上的缺块）。
    用 binary_fill_holes 只填内部洞，外部透明区域不受影响。"""
    alpha = arr[:, :, 3]
    opaque = alpha > 128

    # binary_fill_holes：把被 True 包围的 False 区域填为 True
    filled_mask = ndimage.binary_fill_holes(opaque)

    # 新填的像素 = filled_mask 中为 True 但原 opaque 为 False
    new_pixels = filled_mask & ~opaque
    if not new_pixels.any():
        return arr

    # 填 alpha = 255
    arr[:, :, 3][new_pixels] = 255

    # 填 RGB：用最近邻不透明像素的颜色
    if opaque.any():
        distance, nearest = ndimage.distance_transform_edt(
            ~opaque, return_indices=True
        )
        # 对所有新填像素取最近不透明源
        ys, xs = np.where(new_pixels)
        src_y = nearest[0][new_pixels]
        src_x = nearest[1][new_pixels]
        for c in range(3):
            arr[:, :, c][new_pixels] = arr[:, :, c][src_y, src_x]

    return arr


def sharpen_alpha(alpha):
    """Alpha 对比度拉伸：压缩半透明过渡带，让边缘更锐利。
    alpha < ALPHA_LOW → 0, alpha > ALPHA_HIGH → 255, 中间线性拉伸。"""
    alpha_f = alpha.astype(np.float32)
    # 线性拉伸
    scaled = (alpha_f - ALPHA_LOW) * 255.0 / (ALPHA_HIGH - ALPHA_LOW)
    return np.clip(scaled, 0, 255).astype(np.uint8)


def decontaminate_rgb(arr):
    """去白边/颜色污染：半透明边缘的 RGB 用最近不透明像素替换。"""
    alpha = arr[:, :, 3]
    source_mask = alpha >= COLOR_SOURCE_ALPHA
    fringe_mask = (alpha > 0) & ~source_mask

    if not source_mask.any() or not fringe_mask.any():
        return arr

    distance, nearest = ndimage.distance_transform_edt(~source_mask, return_indices=True)
    near_source = fringe_mask & (distance <= FRINGE_RADIUS)
    src_y = nearest[0][near_source]
    src_x = nearest[1][near_source]

    for channel_idx in range(3):
        channel = arr[:, :, channel_idx]
        channel[near_source] = channel[src_y, src_x]

    return arr


def shift_dark_rgb(arr):
    """把极暗像素的 RGB 提升到 DARK_RGB_MIN 以上，防止被
    -transparentcolor "black" 当成透明吃掉。只改 RGB，不改 alpha。"""
    alpha = arr[:, :, 3]
    opaque = alpha > 128
    if not opaque.any():
        return arr
    for c in range(3):
        ch = arr[:, :, c]
        too_dark = opaque & (ch < DARK_RGB_MIN)
        ch[too_dark] = DARK_RGB_MIN
    return arr


def add_antialias(arr):
    """在锐化后的硬边缘外圈补 1px 半透明过渡，消除锯齿。
    找到不透明区域边界外侧的完全透明像素，给它们赋一个低 alpha 值。"""
    alpha = arr[:, :, 3]
    opaque = alpha > 200
    if not opaque.any():
        return arr
    # 膨胀 1px，找出紧邻不透明区域的外圈像素
    dilated = ndimage.binary_dilation(opaque, iterations=1)
    outer_ring = dilated & ~opaque & (alpha == 0)
    if not outer_ring.any():
        return arr
    # 用最近不透明像素的颜色填充这些像素
    distance, nearest = ndimage.distance_transform_edt(~opaque, return_indices=True)
    src_y = nearest[0][outer_ring]
    src_x = nearest[1][outer_ring]
    for c in range(3):
        arr[:, :, c][outer_ring] = arr[:, :, c][src_y, src_x]
    arr[:, :, 3][outer_ring] = AA_ALPHA
    return arr


def clean_frame(img):
    arr = np.array(img, dtype=np.uint8)
    alpha = arr[:, :, 3].astype(np.uint8)

    # 1. 去噪点
    alpha = remove_tiny_components(alpha)
    arr[:, :, 3] = alpha

    # 2. 填内部洞（角色身体缺块）
    arr = fill_interior_holes(arr)

    # 3. Alpha 锐化（边缘更清晰）
    arr[:, :, 3] = sharpen_alpha(arr[:, :, 3])

    # 4. 去白边污染
    arr = decontaminate_rgb(arr)

    # 5. 暗色偏移：防止黑色特征被 -transparentcolor 吃掉
    arr = shift_dark_rgb(arr)

    # 6. 抗锯齿：在硬边缘外圈补 1px 半透明过渡
    arr = add_antialias(arr)

    return Image.fromarray(arr, "RGBA")


def process_state(state):
    src = os.path.join(SRC_DIR, state)
    out = os.path.join(OUT_DIR, state)

    if not os.path.exists(src):
        print(f"  [SKIP] {src} not found")
        return

    os.makedirs(out, exist_ok=True)
    clear_pngs(out)
    frames = sorted([f for f in os.listdir(src) if f.endswith('.png')])
    print(f"Processing {state}: {len(frames)} frames...")

    for i, fname in enumerate(frames):
        img = Image.open(os.path.join(src, fname)).convert("RGBA")
        result = clean_frame(img)
        result.save(os.path.join(out, fname))

        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(frames)}")

    print("  Done")


def main():
    for state in iter_states():
        process_state(state)
    print("\nAll fixed!")


if __name__ == "__main__":
    main()
