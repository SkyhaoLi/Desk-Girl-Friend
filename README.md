# 🐱‍💻 猫耳女友桌宠 (Desk Girl Friend)

一个 Windows 桌面宠物应用 — 带猫耳的虚拟女友角色，会在桌面上待机、工作、卖萌、害羞……支持点击互动、状态切换、自动检测全屏游戏/影视并隐藏。

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 功能特性

- **11 种默认状态**：待机、工作、力竭、打招呼、卖萌、害羞、哈欠、懵圈、委屈屈、想你、摸鱼
- **平滑状态切换**：基于 `alpha_composite` + 余弦缓动的过渡动画，无鬼影、无位置跳变
- **智能互动**：
  - 左键点击 → 随机触发打招呼/卖萌/害羞
  - 双击 → 想你
  - 右键 → 菜单（切换状态、快捷启动、设置等）
  - 拖拽移动位置
- **自动行为**：
  - 检测办公软件 → 进入工作状态
  - 离开工作 → 力竭状态
  - 长时间无操作 → 随机触发哈欠/懵圈/委屈屈/想你/摸鱼
  - 检测微信/飞书通知 → 打招呼
- **全屏感知**：玩游戏或看电影时自动取消置顶，不遮挡画面
- **系统托盘**：隐藏到托盘，右键恢复
- **开机自启**：一键设置/取消
- **快捷启动**：菜单直接打开 MiMo / Claude（含危险模式）、微信、终端
- **素材添加自动化**：
  - 放视频到 `videos/` → 右键"添加素材" → GUI 填写状态名/触发条件/台词
  - 自动运行 抽帧 → 抠图(rembg) → 边缘修复 管线
  - 处理完成后**热重载**，无需重启即可使用新状态
  - 配置持久化到 `config.json`

## 📁 项目结构

```
Desk-Girl-Friend/
├── pet.pyw              # 主程序（桌宠应用）
├── extract_all.py       # 素材管线 1/3：视频抽帧
├── rembg_proper.py      # 素材管线 2/3：rembg 抠图 + 裁剪
├── fix_edges.py         # 素材管线 3/3：填洞 + 锐化 + 去白边 + 暗色偏移 + 抗锯齿
├── reprocess.py         # 管线一键运行入口
├── config.json          # 用户配置（位置、状态触发条件、台词）— 自动生成
├── autostart.bat        # 开机自启脚本 — 自动生成
├── .gitignore
├── videos/              # 原始视频素材（mp4）
│   ├── 待机.mp4
│   ├── 工作中.mp4
│   ├── 打招呼.mp4
│   └── ...
└── assets/              # 生成素材（gitignore，可从视频重建）
    ├── frames/          # 原始抽帧
    ├── frames_nobg/     # rembg 抠图后
    └── frames_fixed/    # 边缘修复后（pet.pyw 加载此目录）
```

## 🚀 快速开始

### 环境要求

- Windows 10/11
- Python 3.8+
- 依赖：`tkinter`、`Pillow`、`opencv-python`、`rembg`、`scipy`、`numpy`

### 安装

```bash
git clone https://github.com/SkyhaoLi/Desk-Girl-Friend.git
cd Desk-Girl-Friend
pip install Pillow opencv-python rembg scipy numpy
```

### 运行

```bash
pythonw pet.pyw
```

或双击 `启动桌宠.bat`。

### 首次素材处理

项目不包含生成好的帧素材（体积太大）。首次使用需要从视频生成：

```bash
python reprocess.py
```

这会依次运行 `extract_all.py` → `rembg_proper.py` → `fix_edges.py`，处理 `videos/` 中的全部视频。

## 🎬 添加自定义素材

1. 将你的视频文件放入 `videos/` 目录
2. 右键桌宠 → **添加素材**
3. 在弹出的对话框中：
   - 勾选要处理的视频
   - 填写**状态名**（英文，如 `dance`）
   - 选择**触发条件**：点击触发 / 空闲随机 / 待机插入 / 手动切换
   - 填写**台词**（用 `/` 分隔多条）
4. 点击 **开始处理**
5. 等待处理完成 → 新状态立即可用，无需重启

### 触发条件说明

| 触发类型 | 行为 |
|---------|------|
| 点击触发 | 左键点击桌宠时随机触发 |
| 空闲随机 | 长时间无操作时随机触发 |
| 待机插入 | 待机状态下偶尔自动插入 |
| 手动切换 | 仅通过右键菜单手动切换 |

## 🔧 素材处理管线

```
videos/*.mp4
  │
  ├─ extract_all.py    视频抽帧 → assets/frames/<state>/
  │                    支持自定义视频路径参数
  │
  ├─ rembg_proper.py   rembg u2net 模型抠图 → assets/frames_nobg/<state>/
  │                    自动裁剪 + 缩放到 150px 高
  │
  └─ fix_edges.py      边缘修复 → assets/frames_fixed/<state>/
                       ├─ 去噪点（移除离散小连通域）
                       ├─ 填内部洞（binary_fill_holes 修复身体缺块）
                       ├─ Alpha 锐化（对比度拉伸，边缘更清晰）
                       ├─ 去白边（半透明边缘 RGB 去污染）
                       ├─ 暗色偏移（防止 -transparentcolor 吃掉黑色特征）
                       └─ 抗锯齿（硬边缘外圈补 1px 半透明过渡）
```

## ⚙️ 配置

`config.json` 在首次运行时自动生成：

```json
{
  "x": 1500,
  "y": 500,
  "state_configs": {
    "greet": {
      "trigger": "click",
      "label": "打招呼",
      "dialogues": ["嗨~", "你好呀！", "好久不见！"]
    }
  }
}
```

- `x`, `y`：窗口位置（拖拽后自动保存）
- `state_configs`：每个状态的触发条件、中文标签、台词列表

## 📜 许可证

MIT License
