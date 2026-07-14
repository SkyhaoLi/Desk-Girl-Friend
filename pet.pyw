# -*- coding: utf-8 -*-
"""猫耳女友桌宠 - 完整版"""
import os, sys, math, random, json, subprocess, winreg, time, threading, queue, ctypes
from ctypes import wintypes
from pathlib import Path
from tkinter import Menu
from PIL import Image, ImageTk, ImageFilter

_tcl_dir = os.path.join(os.path.dirname(sys.executable), "tcl")
if os.path.exists(_tcl_dir):
    os.environ["TCL_LIBRARY"] = os.path.join(_tcl_dir, "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(_tcl_dir, "tk8.6")

import tkinter as tk
from tkinter import ttk

BASE_DIR = Path(__file__).parent
FRAMES_DIR = BASE_DIR / "assets" / "frames_fixed"
CONFIG_FILE = BASE_DIR / "config.json"

WIN_W, WIN_H, FPS = 130, 180, 24
TARGET_H = 150  # 角色高度

# ===================== 全屏/游戏检测 =====================
# 全屏应用关键词（游戏启动器、游戏本身、视频播放器、影视网站）
FULLSCREEN_KEYWORDS = [
    # 游戏
    "steam", "epic", "origin", "ubisoft", "battle.net", "gog",
    "league of legends", "lol", "valorant", "csgo", "cs2", "dota",
    "genshin", "原神", "崩坏", "honkai", "star rail", "星穹铁道",
    "minecraft", "我的世界", "cyberpunk", "赛博朋克",
    "red dead", "荒野大镖客", "gta", "黑神话", "black myth", "wukong",
    "pubg", "apex", "fortnite", "overwatch", "守望先锋",
    "原神", "绝区零", "zenless", "鸣潮", "wuthering",
    "黑曜石", "obsidian",
    # 视频播放器
    "potplayer", "vlc", "mpv", "mpc-hc", "kmplayer", "qqplayer", "qq影音",
    "bilibili", "哔哩哔哩", "爱奇艺", "iqiyi", "优酷", "youku",
    "腾讯视频", "qqlive", "芒果tv", "netflix", "youtube", "disney",
    "spotify", "网易云", "netease", "qq音乐",
    # 全屏浏览器标签（影视/游戏网站）
    "观影", "看电影", "追剧", "直播", "斗鱼", "虎牙", "twitch",
]

# 全屏检测间隔（秒）
FULLSCREEN_CHECK_INTERVAL = 2


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]

# ===================== 状态配置 =====================
# 默认互动触发（左键点击）— 启动时从 config.json 覆盖
DEFAULT_CLICK_STATES = ["greet", "cute", "shy"]

# 默认空闲随机触发（长时间无操作）
DEFAULT_IDLE_RANDOM_STATES = ["yawn", "confused", "sad", "miss", "slacking"]

# 默认待机时偶尔插入的随机状态
DEFAULT_IDLE_INTERRUPT_STATES = ["yawn", "confused", "slacking", "miss"]

# 待机静态帧显示时长（秒）
IDLE_STATIC_DURATION = 30

# 默认状态标签（中文名）
DEFAULT_STATE_LABELS = {
    "idle": "待机", "work": "工作", "exhausted": "力竭",
    "greet": "打招呼", "cute": "卖萌", "shy": "害羞",
    "yawn": "哈欠", "confused": "懵圈", "sad": "委屈屈",
    "miss": "想你", "slacking": "摸鱼",
}

# 默认台词
DEFAULT_DIALOGUES = {
    "idle": ["...", "在发呆~", "(*^_^*)"],
    "work": ["工作中...", "认真ing", "加油~"],
    "exhausted": ["好累...", "终于干完了", "需要休息..."],
    "greet": ["嗨~", "你好呀！", "好久不见！"],
    "cute": ["看我看我~", "(*^▽^*)", "嘻嘻~"],
    "shy": ["讨厌~", "人家会害羞的", "别这样啦"],
    "yawn": ["困了...", "zzZ...", "打个哈欠~"],
    "confused": ["嗯？", "啥情况？", "？？？" ],
    "sad": ["难过...", "委屈屈", "呜呜~"],
    "miss": ["想你了~", "你在哪", "好想你"],
    "slacking": ["偷偷摸鱼~", "嘿嘿", "放松一下"],
}

# 默认状态配置（首次运行写入 config.json）
DEFAULT_STATE_CONFIGS = {
    "idle":      {"trigger": "idle",           "label": "待机",    "dialogues": DEFAULT_DIALOGUES["idle"]},
    "work":      {"trigger": "work",           "label": "工作",    "dialogues": DEFAULT_DIALOGUES["work"]},
    "exhausted": {"trigger": "after_work",     "label": "力竭",    "dialogues": DEFAULT_DIALOGUES["exhausted"]},
    "greet":     {"trigger": "click",          "label": "打招呼",  "dialogues": DEFAULT_DIALOGUES["greet"]},
    "cute":      {"trigger": "click",          "label": "卖萌",    "dialogues": DEFAULT_DIALOGUES["cute"]},
    "shy":       {"trigger": "click",          "label": "害羞",    "dialogues": DEFAULT_DIALOGUES["shy"]},
    "yawn":      {"trigger": "idle_random",    "label": "哈欠",    "dialogues": DEFAULT_DIALOGUES["yawn"]},
    "confused":  {"trigger": "idle_random",    "label": "懵圈",    "dialogues": DEFAULT_DIALOGUES["confused"]},
    "sad":       {"trigger": "idle_random",    "label": "委屈屈",  "dialogues": DEFAULT_DIALOGUES["sad"]},
    "miss":      {"trigger": "idle_random",    "label": "想你",    "dialogues": DEFAULT_DIALOGUES["miss"]},
    "slacking":  {"trigger": "idle_interrupt", "label": "摸鱼",    "dialogues": DEFAULT_DIALOGUES["slacking"]},
}

# 办公软件关键词
WORK_KEYWORDS = [
    "cmd", "powershell", "terminal", "wt", "终端",
    "wps", "文字", "表格", "演示", "pdf",
    "飞书", "feishu", "lark", "钉钉", "dingtalk",
    "word", "excel", "powerpoint", "outlook", "teams",
    "photoshop", "illustrator", "figma", "sketch", "canva", "ps",
    "vscode", "visual studio", "pycharm", "intellij", "cursor",
    "notion", "obsidian", "typora", "markdown",
    "blender", "maya", "cinema4d", "ae", "after effects",
    "pr", "premiere", "达芬奇", "剪映", "capcut",
    "chrome", "edge", "firefox", "safari", "浏览器",
    "设计", "开发", "代码", "编程", "文档", "编辑",
    "claude", "mimo", "mc",
]


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("猫耳女友")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.98)
        self.root.config(bg="black")
        self.root.attributes("-transparentcolor", "black")

        self.config = self.load_config()
        self.root.geometry(f"{WIN_W}x{WIN_H}+{self.config.get('x',1500)}+{self.config.get('y',500)}")

        self.canvas = tk.Canvas(self.root, width=WIN_W, height=WIN_H, bg="black", highlightthickness=0)
        self.canvas.pack()

        # 状态配置：触发条件、台词、标签 — 从 config.json 加载
        self.state_configs = {}
        self.click_states = list(DEFAULT_CLICK_STATES)
        self.idle_random_states = list(DEFAULT_IDLE_RANDOM_STATES)
        self.idle_interrupt_states = list(DEFAULT_IDLE_INTERRUPT_STATES)
        self.dialogues = dict(DEFAULT_DIALOGUES)
        self.state_labels = dict(DEFAULT_STATE_LABELS)
        self.load_state_configs()

        # 加载所有状态的帧
        self.all_frames = {}
        self.load_all_frames()

        # 当前状态
        self.current_state = "idle"
        self.frame_idx = 0
        self.frames = self.all_frames.get("idle", [])

        # 过渡动画
        self.transition_frames = []
        self.transition_idx = 0
        self.is_transitioning = False

        # 状态计时
        self.time = 0
        self.state_timer = 0
        self.idle_static_timer = 0  # 待机静态帧计时
        self.last_activity_time = time.time()
        self.IDLE_TIMEOUT = 30
        self.WORK_CHECK_INTERVAL = 3

        # 动画参数
        self.anim_dx = 0
        self.anim_dy = 0
        self.anim_rot = 0
        self.target_dx = 0
        self.target_dy = 0
        self.target_rot = 0

        # 交互
        self.is_dragging = False
        self.drag_x = self.drag_y = 0
        self.interaction_cd = False

        # 隐藏状态
        self.is_hidden = False
        self._tray_icon = None

        # 全屏/游戏模式：检测到时取消置顶，避免遮挡游戏和影视
        self.in_fullscreen = False
        self._was_topmost = True

        # 气泡
        self.bubble_id = None
        self.bubble_text_id = None
        self.bubble_bg_id = None
        self.bubble_timer = 0

        # 位置
        self.char_x = WIN_W // 2
        self.char_y = WIN_H // 2 + 20

        # 显示
        if self.frames:
            self.tk_img = ImageTk.PhotoImage(self.frames[0])
        else:
            self.tk_img = ImageTk.PhotoImage(Image.new("RGBA", (100, 100), (255, 0, 255, 200)))
        self.char_id = self.canvas.create_image(self.char_x, self.char_y, image=self.tk_img, anchor="center")

        # 绑定
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.root.bind("<Key>", self.on_key)

        self.create_menu()
        self.animate()
        self.check_idle()
        self.check_fullscreen()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text("utf-8"))
        return {"x": 1500, "y": 500}

    def save_config(self):
        self.config["x"] = self.root.winfo_x()
        self.config["y"] = self.root.winfo_y()
        self.config["state_configs"] = self.state_configs
        CONFIG_FILE.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), "utf-8")

    def load_state_configs(self):
        """从 config.json 加载状态配置，合并默认值。首次运行时写入默认配置。"""
        saved = self.config.get("state_configs", {})
        if not saved:
            # 首次运行：写入默认 11 状态配置
            self.state_configs = dict(DEFAULT_STATE_CONFIGS)
            self.config["state_configs"] = self.state_configs
            CONFIG_FILE.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), "utf-8")
        else:
            # 合并：默认值 + 用户自定义（用户覆盖同名状态）
            self.state_configs = dict(DEFAULT_STATE_CONFIGS)
            self.state_configs.update(saved)

        # 根据配置重建触发条件列表和台词
        self._rebuild_trigger_lists()

    def _rebuild_trigger_lists(self):
        """根据 state_configs 重建 click/idle_random/idle_interrupt 列表和台词。"""
        self.click_states = []
        self.idle_random_states = []
        self.idle_interrupt_states = []
        self.dialogues = {}
        self.state_labels = {}

        for state, cfg in self.state_configs.items():
            trigger = cfg.get("trigger", "manual")
            label = cfg.get("label", state)
            dialogues = cfg.get("dialogues", ["..."])

            self.state_labels[state] = label
            self.dialogues[state] = dialogues

            if trigger == "click":
                self.click_states.append(state)
            elif trigger == "idle_random":
                self.idle_random_states.append(state)
            elif trigger == "idle_interrupt":
                self.idle_interrupt_states.append(state)
            # "idle", "work", "after_work", "manual" 不加入随机列表

        # 确保至少有默认值（防止配置为空时崩溃）
        if not self.click_states:
            self.click_states = list(DEFAULT_CLICK_STATES)
        if not self.idle_random_states:
            self.idle_random_states = list(DEFAULT_IDLE_RANDOM_STATES)
        if not self.idle_interrupt_states:
            self.idle_interrupt_states = list(DEFAULT_IDLE_INTERRUPT_STATES)

    def save_state_configs(self):
        """保存状态配置到 config.json。"""
        self.config["state_configs"] = self.state_configs
        CONFIG_FILE.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), "utf-8")

    def load_all_frames(self):
        """加载所有状态的帧"""
        target_h = TARGET_H
        for state_dir in FRAMES_DIR.iterdir():
            if state_dir.is_dir():
                state_name = state_dir.name
                frames = []
                for f in sorted(state_dir.glob("*.png")):
                    img = Image.open(f).convert("RGBA")
                    if img.height != target_h:
                        scale = target_h / img.height
                        img = img.resize((max(1, int(img.width * scale)), target_h), Image.LANCZOS)
                    frames.append(img)
                if frames:
                    self.all_frames[state_name] = frames
        print(f"Loaded {len(self.all_frames)} states")

    def _pad_to_canvas(self, img, w, h):
        """把图片居中放到指定尺寸的透明画布上，不拉伸。"""
        if img.width == w and img.height == h:
            return img
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        x = (w - img.width) // 2
        y = (h - img.height) // 2
        canvas.paste(img, (x, y), img)
        return canvas

    def create_transition(self, from_state, to_state, num_frames=12):
        """创建两个状态之间的过渡帧（alpha_composite + 余弦缓动，无鬼影）。"""
        if from_state not in self.all_frames or to_state not in self.all_frames:
            return

        from_img = self.all_frames[from_state][-1]
        to_img = self.all_frames[to_state][0]

        # pad 到统一画布尺寸（不拉伸）
        canvas_w = max(from_img.width, to_img.width)
        canvas_h = max(from_img.height, to_img.height)
        from_img = self._pad_to_canvas(from_img, canvas_w, canvas_h)
        to_img = self._pad_to_canvas(to_img, canvas_w, canvas_h)

        transition = []
        for i in range(num_frames):
            t = i / (num_frames - 1)
            # 余弦缓动 ease-in-out
            t_eased = 0.5 * (1 - math.cos(math.pi * t))
            # 缩放各自 alpha：旧帧淡出 (1-t)，新帧淡入 (t)
            from_a = from_img.getchannel('A').point(lambda x: int(x * (1 - t_eased)))
            to_a = to_img.getchannel('A').point(lambda x: int(x * t_eased))
            from_scaled = from_img.copy()
            from_scaled.putalpha(from_a)
            to_scaled = to_img.copy()
            to_scaled.putalpha(to_a)
            # alpha_composite 正确合成（新帧在上）
            result = Image.alpha_composite(from_scaled, to_scaled)
            transition.append(result)

        return transition

    def set_state(self, state, duration=0, with_transition=True):
        """设置状态"""
        if state not in self.all_frames:
            return

        # 创建过渡动画
        if with_transition and self.current_state != state:
            transition = self.create_transition(self.current_state, state)
            if transition:
                self.transition_frames = transition
                self.transition_idx = 0
                self.is_transitioning = True

        self.current_state = state
        self.frames = self.all_frames[state]
        self.frame_idx = 0
        if duration > 0:
            self.state_timer = duration

    def show_bubble(self, text, duration=3000):
        """显示聊天气泡 - 白底黑字"""
        self.clear_bubble()
        font = ("微软雅黑", 11)
        tw = len(text) * 13 + 20
        th = 28
        bx = self.char_x
        by = 25
        x1, x2 = max(5, bx - tw//2), min(WIN_W-5, bx + tw//2)
        y1, y2 = by - th//2, by + th//2

        # 白色背景气泡
        self.bubble_bg_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="white", outline="#ddd", width=1
        )
        # 小三角
        self.bubble_id = self.canvas.create_polygon(
            bx-5, y2, bx, y2+10, bx+5, y2,
            fill="white", outline="#ddd"
        )
        # 黑色文字
        self.bubble_text_id = self.canvas.create_text(
            (x1+x2)//2, (y1+y2)//2,
            text=text, fill="#333333", font=font
        )

        self.bubble_timer = duration
        self.root.after(100, self._tick_bubble)

    def _tick_bubble(self):
        if self.bubble_timer > 0:
            self.bubble_timer -= 100
            self.root.after(100, self._tick_bubble)
        else:
            self.clear_bubble()

    def clear_bubble(self):
        for i in [self.bubble_bg_id, self.bubble_id, self.bubble_text_id]:
            if i: self.canvas.delete(i)
        self.bubble_bg_id = self.bubble_id = self.bubble_text_id = None

    def random_dialogue(self, state=None):
        return random.choice(self.dialogues.get(state or self.current_state, ["..."]))

    # ===================== 办公检测 =====================
    def check_work_activity(self):
        """检测是否有办公/创作活动"""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()

            is_work = any(kw in title for kw in WORK_KEYWORDS)
            return is_work, title
        except:
            return False, ""

    def check_notifications(self):
        """检测微信/飞书通知"""
        try:
            import ctypes

            # 通知应用关键词
            notify_apps = ["微信", "weixin", "wechat", "飞书", "feishu", "lark", "钉钉", "dingtalk"]

            # 遍历所有顶层窗口
            result = []

            def enum_callback(hwnd, lParam):
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.lower()

                        # 检查是否是通知应用
                        for app in notify_apps:
                            if app in title:
                                # 检查窗口是否在闪烁（有通知）
                                FLASHW_STOP = 0
                                FLASHW_CAPTION = 0x00000001
                                FLASHW_TRAY = 0x00000002
                                FLASHW_ALL = FLASHW_CAPTION | FLASHW_TRAY

                                class FLASHWINFO(ctypes.Structure):
                                    _fields_ = [
                                        ("cbSize", ctypes.c_uint),
                                        ("hwnd", ctypes.c_void_p),
                                        ("dwFlags", ctypes.c_uint),
                                        ("uCount", ctypes.c_uint),
                                        ("dwTimeout", ctypes.c_uint),
                                    ]

                                fwi = FLASHWINFO()
                                fwi.cbSize = ctypes.sizeof(FLASHWINFO)
                                fwi.hwnd = hwnd

                                # 获取窗口信息
                                GUICON_FLASHING = 0x00000001
                                guick = ctypes.windll.user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE

                                # 简单检测：如果窗口标题包含数字（未读数），可能是通知
                                import re
                                if re.search(r'\(\d+\)', title) or re.search(r'\[\d+\]', title):
                                    result.append((hwnd, title))
                                    break
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

            return len(result) > 0, result
        except Exception as e:
            return False, []

    # ===================== 交互 =====================
    def on_click(self, event):
        self.is_dragging = True
        self.drag_x, self.drag_y = event.x, event.y
        self.last_activity_time = time.time()

        if not self.interaction_cd:
            self.interaction_cd = True
            self.root.after(1500, lambda: setattr(self, 'interaction_cd', False))
            state = random.choice(self.click_states)
            self.set_state(state, duration=FPS * 3)
            self.show_bubble(self.random_dialogue(state), 2500)

    def on_drag(self, event):
        if self.is_dragging:
            self.root.geometry(f"+{self.root.winfo_x()+event.x-self.drag_x}+{self.root.winfo_y()+event.y-self.drag_y}")
            self.last_activity_time = time.time()

    def on_release(self, event):
        self.is_dragging = False

    def on_double_click(self, event):
        self.last_activity_time = time.time()
        self.set_state("miss", duration=FPS * 3)
        self.show_bubble(self.random_dialogue("miss"), 3000)

    def on_key(self, event):
        self.last_activity_time = time.time()

    # ===================== 空闲检测 =====================
    def check_idle(self):
        """检查空闲状态 - 工作状态优先级最高"""
        now = time.time()
        idle_duration = now - self.last_activity_time

        is_work, title = self.check_work_activity()

        # 工作状态优先级最高
        if is_work:
            if self.current_state != "work":
                self.set_state("work", with_transition=False)
                self.show_bubble("开始工作~", 2000)
            self.root.after(self.WORK_CHECK_INTERVAL * 1000, self.check_idle)
            return

        # 离开工作状态
        if not is_work and self.current_state == "work":
            self.set_state("exhausted", duration=FPS * 4)
            self.show_bubble("终于干完了...", 3000)
            self.root.after(self.WORK_CHECK_INTERVAL * 1000, self.check_idle)
            return

        # 检测通知
        has_notify, notify_info = self.check_notifications()
        if has_notify and self.current_state == "idle":
            self.set_state("greet", duration=FPS * 3)
            self.show_bubble("有消息~", 2500)
            self.root.after(self.WORK_CHECK_INTERVAL * 1000, self.check_idle)
            return

        # 空闲状态 - 只有在待机状态下才触发随机事件
        if not is_work and self.current_state == "idle":
            if idle_duration > self.IDLE_TIMEOUT:
                state = random.choice(self.idle_random_states)
                self.set_state(state, duration=FPS * 3)
                self.show_bubble(self.random_dialogue(state), 2500)

        self.root.after(self.WORK_CHECK_INTERVAL * 1000, self.check_idle)

    # ===================== 全屏/游戏检测 =====================
    def _get_foreground_info(self):
        """返回 (hwnd, title, is_fullscreen_window)。is_fullscreen_window 判断前台窗口是否覆盖整个屏幕。"""
        try:
            user32 = ctypes.windll.user32
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.MonitorFromWindow.restype = wintypes.HANDLE
            user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return 0, "", False

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

            # 取窗口矩形和显示器工作区
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            user32.GetMonitorInfoW(monitor, ctypes.byref(mi))

            # 窗口尺寸
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            # 屏幕尺寸
            sw = mi.rcMonitor.right - mi.rcMonitor.left
            sh = mi.rcMonitor.bottom - mi.rcMonitor.top

            is_fs = (w >= sw and h >= sh)
            return hwnd, title, is_fs
        except Exception:
            return 0, "", False

    def check_fullscreen(self):
        """检测全屏/游戏/影视场景，自动取消置顶避免遮挡。"""
        if self.is_hidden:
            self.root.after(FULLSCREEN_CHECK_INTERVAL * 1000, self.check_fullscreen)
            return

        hwnd, title, is_fs = self._get_foreground_info()
        title_lower = title.lower()

        # 判断：前台是全屏窗口 OR 标题命中游戏/影视关键词
        is_game_or_media = any(kw in title_lower for kw in FULLSCREEN_KEYWORDS)
        should_lower = is_fs or is_game_or_media

        # 排除：自己被拖动时不要乱切
        if should_lower and self._was_topmost:
            self.root.attributes("-topmost", False)
            self._was_topmost = False
            self.in_fullscreen = True
        elif not should_lower and not self._was_topmost:
            self.root.attributes("-topmost", True)
            self._was_topmost = True
            self.in_fullscreen = False

        self.root.after(FULLSCREEN_CHECK_INTERVAL * 1000, self.check_fullscreen)

    # ===================== 动画 =====================
    def animate(self):
        self.time += 1
        t = self.time

        # 状态计时
        if self.state_timer > 0:
            self.state_timer -= 1
            if self.state_timer == 0:
                self.set_state("idle")

        # 确定本帧要显示的图片
        display_img = None

        # 过渡动画 — 不再 early return，位置/旋转照常更新
        if self.is_transitioning:
            self.transition_idx += 1
            if self.transition_idx >= len(self.transition_frames):
                self.is_transitioning = False
            else:
                display_img = self.transition_frames[self.transition_idx]

        # 正常动画帧推进（过渡期间不推进 frame_idx）
        if display_img is None:
            if self.current_state == "idle":
                # 静态待机，偶尔触发随机状态
                if t % (FPS * IDLE_STATIC_DURATION) == 0:
                    if random.random() < 0.3:
                        interrupt = random.choice(self.idle_interrupt_states)
                        self.set_state(interrupt, duration=FPS * 3)
                        self.show_bubble(self.random_dialogue(interrupt), 2500)
            elif self.frames and len(self.frames) > 1:
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)

            if self.frames:
                display_img = self.frames[min(self.frame_idx, len(self.frames) - 1)]

        # 整体动画参数（平滑过渡）— 过渡期间也更新，避免结束时位置跳变
        if self.current_state == "idle":
            self.target_dy = math.sin(t * 0.04) * 1
            self.target_rot = 0
        elif self.current_state == "exhausted":
            self.target_dy = math.sin(t * 0.06) * 2
            self.target_rot = 0
        elif self.current_state == "work":
            self.target_dy = math.sin(t * 0.1) * 1
            self.target_rot = 0
        elif self.current_state in ["greet", "cute"]:
            self.target_dy = -abs(math.sin(t * 0.2)) * 5
            self.target_rot = math.sin(t * 0.25) * 3
        elif self.current_state == "shy":
            self.target_dy = 0
            self.target_rot = math.sin(t * 0.15) * 4
        elif self.current_state == "miss":
            self.target_dy = -math.sin(t * 0.1) * 3
            self.target_rot = 0
        elif self.current_state == "sad":
            self.target_dy = math.sin(t * 0.05) * 2
            self.target_rot = math.sin(t * 0.04) * 3
        elif self.current_state == "slacking":
            self.target_dy = 0
            self.target_rot = math.sin(t * 0.08) * 5

        # 平滑插值
        self.anim_dx += (self.target_dx - self.anim_dx) * 0.1
        self.anim_dy += (self.target_dy - self.anim_dy) * 0.1
        self.anim_rot += (self.target_rot - self.anim_rot) * 0.1

        # 应用变换
        if display_img is not None:
            img = display_img.copy()
            if abs(self.anim_rot) > 0.1:
                rotated = img.rotate(self.anim_rot, expand=True, resample=Image.BICUBIC)
                canvas_w = max(img.width, rotated.width)
                canvas_h = max(img.height, rotated.height)
                canvas_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                paste_x = (canvas_w - rotated.width) // 2
                paste_y = (canvas_h - rotated.height) // 2
                canvas_img.paste(rotated, (paste_x, paste_y), rotated)
                img = canvas_img
            self.tk_img = ImageTk.PhotoImage(img)
            self.canvas.coords(self.char_id, self.char_x + self.anim_dx, self.char_y + self.anim_dy)
            self.canvas.itemconfig(self.char_id, image=self.tk_img)

        self.root.after(1000 // FPS, self.animate)

    # ===================== 菜单 =====================
    def create_menu(self):
        self.menu = Menu(self.root, tearoff=0, font=("微软雅黑", 10))
        self.state_submenu = Menu(self.menu, tearoff=0, font=("微软雅黑", 10))
        self._populate_state_submenu()
        self.menu.add_cascade(label="切换状态", menu=self.state_submenu)
        self.menu.add_separator()
        # 快捷启动
        self.menu.add_command(label="Open MiMo", command=lambda: (self.launch_cli("mimo"), self.show_bubble("已打开~", 2000)))
        self.menu.add_command(label="Open MiMo (危险模式)", command=lambda: (self.launch_cli("mimo", "--dangerously-skip-permissions"), self.show_bubble("危险模式~小心哦", 2500)))
        self.menu.add_command(label="Open Claude", command=lambda: (self.launch_cli("claude"), self.show_bubble("已打开~", 2000)))
        self.menu.add_command(label="Open Claude (危险模式)", command=lambda: (self.launch_cli("claude", "--dangerously-skip-permissions"), self.show_bubble("危险模式~小心哦", 2500)))
        self.menu.add_command(label="Open WeChat", command=self.open_wechat)
        self.menu.add_command(label="Open Terminal", command=self.open_terminal)
        self.menu.add_separator()
        self.menu.add_command(label="隐藏桌宠", command=self.hide)
        self.menu.add_command(label="添加素材", command=self.open_add_video)
        self.menu.add_command(label="设置开机自启", command=self.toggle_autostart)
        self.menu.add_command(label="退出", command=self.on_close)

    def _populate_state_submenu(self):
        """根据 state_configs 填充状态切换子菜单。"""
        self.state_submenu.delete(0, "end")
        for state, cfg in self.state_configs.items():
            if state not in self.all_frames:
                continue
            label = cfg.get("label", state)
            self.state_submenu.add_command(
                label=label,
                command=lambda st=state: (self.set_state(st, FPS*3), self.show_bubble(self.random_dialogue(st), 2500))
            )

    def rebuild_state_menu(self):
        """重建状态切换子菜单（添加新素材后调用）。"""
        self._populate_state_submenu()

    def launch_cli(self, exe, *extra_args):
        """启动命令行工具（mimo/claude 等），在新终端窗口中打开。
        用 cmd /k 保持窗口不立即关闭；带 --dangerously-skip-permissions 时为危险模式。"""
        try:
            cmd = ["cmd", "/c", "start", exe] + list(extra_args)
            subprocess.Popen(cmd, shell=False)
        except Exception as e:
            print(f"launch_cli failed: {e}")
            self.show_bubble("打开失败了...", 2000)

    def open_wechat(self):
        """打开微信。优先用注册表/常见路径定位 Weixin.exe(新版)/WeChat.exe(旧版)，找不到则回退到官网。"""
        try:
            # 1) 注册表 HKCU\Software\Tencent\WeChat 的 InstallPath
            candidates = []
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for sub in (r"Software\Tencent\WeChat",
                            r"Software\Tencent\Weixin",
                            r"Software\WOW6432Node\Tencent\WeChat",
                            r"Software\WOW6432Node\Tencent\Weixin"):
                    try:
                        k = winreg.OpenKey(root, sub, 0, winreg.KEY_READ)
                        try:
                            install, _ = winreg.QueryValueEx(k, "InstallPath")
                            if install:
                                base = Path(install)
                                candidates.append(base / "Weixin.exe")
                                candidates.append(base / "WeChat.exe")
                        except FileNotFoundError:
                            pass
                        winreg.CloseKey(k)
                    except OSError:
                        pass

            # 2) 常见安装路径（新版 Weixin + 旧版 WeChat）
            common_bases = [
                Path(r"C:\Program Files\Tencent\Weixin"),
                Path(r"C:\Program Files\Tencent\WeChat"),
                Path(r"C:\Program Files (x86)\Tencent\Weixin"),
                Path(r"C:\Program Files (x86)\Tencent\WeChat"),
                Path(r"D:\Program Files\Tencent\Weixin"),
                Path(r"D:\Program Files\Tencent\WeChat"),
                Path(r"D:\Tencent\Weixin"),
                Path(r"D:\Tencent\WeChat"),
                Path(r"E:\Program Files\Tencent\Weixin"),
                Path(r"E:\Program Files\Tencent\WeChat"),
            ]
            for base in common_bases:
                candidates.append(base / "Weixin.exe")
                candidates.append(base / "WeChat.exe")

            wechat_exe = next((p for p in candidates if p.exists()), None)
            if wechat_exe:
                subprocess.Popen([str(wechat_exe)], shell=False)
                self.show_bubble("已打开微信~", 2000)
            else:
                # 找不到本地安装，打开官网下载页
                subprocess.Popen(["cmd", "/c", "start", "", "https://weixin.qq.com/"], shell=False)
                self.show_bubble("没找到微信，已打开官网~", 3000)
        except Exception as e:
            print(f"open_wechat failed: {e}")
            self.show_bubble("打开微信失败...", 2000)

    def open_terminal(self):
        """打开终端。优先 Windows Terminal (wt)，回退到 PowerShell，再回退到 cmd。"""
        try:
            # 1) Windows Terminal：WindowsApps 下的 wt.exe（可能不在 PATH）
            wt_candidates = [
                Path(r"C:\Users\Skyha\AppData\Local\Microsoft\WindowsApps\wt.exe"),
                Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "wt.exe",
            ]
            wt = next((p for p in wt_candidates if p.exists()), None)
            if wt:
                subprocess.Popen(["cmd", "/c", "start", str(wt)], shell=False)
                self.show_bubble("已打开终端~", 2000)
                return

            # 2) PowerShell
            ps = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
            if ps.exists():
                subprocess.Popen(["cmd", "/c", "start", "powershell"], shell=False)
                self.show_bubble("已打开 PowerShell~", 2000)
                return

            # 3) cmd
            subprocess.Popen(["cmd", "/c", "start", "cmd"], shell=False)
            self.show_bubble("已打开命令行~", 2000)
        except Exception as e:
            print(f"open_terminal failed: {e}")
            self.show_bubble("打开终端失败...", 2000)

    def show_menu(self, event):
        self.show_bubble(random.choice(["要做什么呢？", "请选择~"]), 2000)
        self.menu.post(event.x_root, event.y_root)

    # ===================== 隐藏/托盘 =====================
    def hide(self):
        """隐藏桌宠窗口到系统托盘。"""
        if self.is_hidden:
            return
        self.root.withdraw()
        self.is_hidden = True
        self._ensure_tray_icon()

    def show(self):
        """从托盘恢复显示桌宠。"""
        if not self.is_hidden:
            return
        self.root.deiconify()
        self.is_hidden = False
        self.root.attributes("-topmost", True)
        self._was_topmost = True
        # 重新触发一次全屏检测以同步置顶状态
        self.root.after(100, self.check_fullscreen)

    def _ensure_tray_icon(self):
        """创建系统托盘图标（用 ctypes 直接调 Shell_NotifyIcon，不依赖 pystray）。"""
        if self._tray_icon is not None:
            return
        try:
            self._tray_icon = _TrayIcon(self)
            self._tray_icon.start()
        except Exception as e:
            print(f"tray icon failed: {e}")
            # 托盘失败时不要让用户无法恢复，直接重新显示
            self.is_hidden = False
            self.root.deiconify()

    def open_add_video(self):
        """打开添加素材对话框，自动扫描 videos/ 目录。"""
        videos_dir = BASE_DIR / "videos"
        if not videos_dir.exists():
            videos_dir.mkdir(parents=True, exist_ok=True)
        # 收集 videos/ 中的视频文件
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        videos = sorted([f for f in videos_dir.iterdir()
                         if f.suffix.lower() in video_exts])
        if not videos:
            self.show_bubble("videos/ 目录没有视频文件", 3000)
            subprocess.Popen(["explorer", str(videos_dir)])
            return
        try:
            AddAssetDialog(self.root, self, videos)
        except Exception as e:
            print(f"open_add_video failed: {e}")
            self.show_bubble("打开添加素材失败...", 2000)

    def hot_reload_state(self, state):
        """从 frames_fixed/<state>/ 热重载帧到内存，无需重启。"""
        state_dir = FRAMES_DIR / state
        if not state_dir.is_dir():
            return
        frames = []
        for f in sorted(state_dir.glob("*.png")):
            img = Image.open(f).convert("RGBA")
            if img.height != TARGET_H:
                scale = TARGET_H / img.height
                img = img.resize((max(1, int(img.width * scale)), TARGET_H), Image.LANCZOS)
            frames.append(img)
        if frames:
            self.all_frames[state] = frames
            print(f"Hot reloaded {state}: {len(frames)} frames")

    def process_assets(self, items, progress_callback, done_callback):
        """后台线程：对每个 (state, video_path, trigger, label, dialogues) 运行管线。
        items: list of dicts with keys: state, video, trigger, label, dialogues
        progress_callback(step_text, current, total) — 在主线程执行
        done_callback() — 在主线程执行"""
        def worker():
            n = len(items)
            for idx, item in enumerate(items):
                state = item["state"]
                video = item["video"]
                # 1. 抽帧
                self.root.after(0, progress_callback, f"抽帧: {state}", idx, n)
                try:
                    subprocess.run(
                        [sys.executable, "extract_all.py", state, video],
                        check=True, cwd=str(BASE_DIR),
                        capture_output=True, text=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"extract failed for {state}: {e.stderr}")
                    continue
                # 2. rembg
                self.root.after(0, progress_callback, f"抠图: {state}", idx, n)
                try:
                    subprocess.run(
                        [sys.executable, "rembg_proper.py", state],
                        check=True, cwd=str(BASE_DIR),
                        capture_output=True, text=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"rembg failed for {state}: {e.stderr}")
                    continue
                # 3. fix_edges
                self.root.after(0, progress_callback, f"修边: {state}", idx, n)
                try:
                    subprocess.run(
                        [sys.executable, "fix_edges.py", state],
                        check=True, cwd=str(BASE_DIR),
                        capture_output=True, text=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"fix_edges failed for {state}: {e.stderr}")
                    continue
                # 4. 热重载（主线程）
                self.root.after(0, self.hot_reload_state, state)
            self.root.after(0, done_callback)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def toggle_autostart(self):
        runner = str(BASE_DIR / "autostart.bat")
        # 用 %~dp0 引用 bat 自身目录，避免中文路径在 GBK cmd 下乱码
        Path(runner).write_text(
            '@echo off\r\n'
            'cd /d "%~dp0"\r\n'
            'set "PYTHONW=C:\\ProgramData\\anaconda3\\pythonw.exe"\r\n'
            'set "TCL_LIBRARY=C:\\ProgramData\\anaconda3\\tcl\\tcl8.6"\r\n'
            'set "TK_LIBRARY=C:\\ProgramData\\anaconda3\\tcl\\tk8.6"\r\n'
            'start "" "%PYTHONW%" pet.pyw\r\n',
            "ascii",
        )
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_ALL_ACCESS)
            try:
                winreg.QueryValueEx(k, "CatGirl"); winreg.DeleteValue(k, "CatGirl")
                self.show_bubble("已取消开机自启", 2000)
            except:
                winreg.SetValueEx(k, "CatGirl", 0, winreg.REG_SZ, f'"{runner}"')
                self.show_bubble("已设置开机自启~", 2000)
            winreg.CloseKey(k)
        except:
            self.show_bubble("设置失败...", 2000)

    def on_close(self):
        self.save_config()
        if self._tray_icon is not None:
            self._tray_icon.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ===================== 添加素材对话框 =====================
class AddAssetDialog:
    """tkinter Toplevel 对话框：扫描 videos/，让用户填写状态名/触发条件/台词，
    后台自动运行管线，完成后热重载。"""

    # 触发类型选项
    TRIGGER_OPTIONS = {
        "点击触发": "click",
        "空闲随机": "idle_random",
        "待机插入": "idle_interrupt",
        "手动切换": "manual",
    }

    # 中文文件名 → 默认状态名映射（反向）
    CN_TO_STATE = {
        "待机": "idle", "工作中": "work", "力竭了": "exhausted",
        "打招呼": "greet", "卖萌": "cute", "害羞": "shy",
        "哈欠": "yawn", "懵圈": "confused", "委屈屈": "sad",
        "想你": "miss", "摸鱼": "slacking",
    }

    def __init__(self, parent, pet, videos):
        self.pet = pet
        self.videos = videos
        self.items = []  # 每个: {var, state_entry, trigger_var, dialogue_entry, video_path}

        self.win = tk.Toplevel(parent)
        self.win.title("添加素材")
        self.win.geometry("520x520")
        self.win.resizable(True, True)
        self.win.grab_set()
        self.win.focus_force()

        # 标题
        tk.Label(self.win, text="添加新素材", font=("微软雅黑", 14, "bold")).pack(pady=(10, 5))

        # 滚动区域
        container = tk.Frame(self.win)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 为每个视频创建一行
        for vpath in videos:
            self._add_video_row(scroll_frame, vpath)

        # 底部：进度 + 按钮
        bottom = tk.Frame(self.win)
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        self.progress_label = tk.Label(bottom, text="", font=("微软雅黑", 9))
        self.progress_label.pack(anchor="w")

        self.progress = ttk.Progressbar(bottom, length=500, mode="determinate")
        self.progress.pack(fill="x", pady=(2, 8))

        btn_frame = tk.Frame(bottom)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="打开 videos/ 文件夹", command=self._open_videos_dir).pack(side="left")
        tk.Button(btn_frame, text="开始处理", command=self._start_processing, bg="#4CAF50", fg="white").pack(side="right", padx=(5, 0))
        tk.Button(btn_frame, text="取消", command=self.win.destroy).pack(side="right")

        self._processing = False

    def _add_video_row(self, parent, vpath):
        """为单个视频创建一行配置 UI。"""
        row = tk.Frame(parent, bd=1, relief="groove", padx=8, pady=6)
        row.pack(fill="x", pady=3)

        # 勾选框 + 文件名
        top = tk.Frame(row)
        top.pack(fill="x")
        var = tk.IntVar(value=1)
        tk.Checkbutton(top, variable=var).pack(side="left")
        fname = vpath.stem  # 文件名（无扩展名）
        tk.Label(top, text=fname, font=("微软雅黑", 10, "bold")).pack(side="left", padx=(4, 0))

        # 状态名
        mid1 = tk.Frame(row)
        mid1.pack(fill="x", pady=(4, 0))
        tk.Label(mid1, text="状态名:", font=("微软雅黑", 9), width=8).pack(side="left")
        # 默认状态名：如果中文文件名在映射中，用对应英文；否则用文件名拼音/原文
        default_state = self.CN_TO_STATE.get(fname, fname.lower().replace(" ", "_"))
        state_entry = tk.Entry(mid1, width=20, font=("微软雅黑", 9))
        state_entry.insert(0, default_state)
        state_entry.pack(side="left", padx=(2, 10))

        # 触发条件
        tk.Label(mid1, text="触发:", font=("微软雅黑", 9), width=6).pack(side="left")
        trigger_var = tk.StringVar(value="点击触发")
        trigger_menu = tk.OptionMenu(mid1, trigger_var, *self.TRIGGER_OPTIONS.keys())
        trigger_menu.config(font=("微软雅黑", 9), width=10)
        trigger_menu.pack(side="left")

        # 台词
        mid2 = tk.Frame(row)
        mid2.pack(fill="x", pady=(4, 2))
        tk.Label(mid2, text="台词:", font=("微软雅黑", 9), width=8).pack(side="left")
        dialogue_entry = tk.Entry(mid2, width=50, font=("微软雅黑", 9))
        dialogue_entry.insert(0, f"{fname}~")
        dialogue_entry.pack(side="left", padx=(2, 0))

        self.items.append({
            "var": var,
            "state_entry": state_entry,
            "trigger_var": trigger_var,
            "dialogue_entry": dialogue_entry,
            "video_path": str(vpath),
            "filename": fname,
        })

    def _open_videos_dir(self):
        subprocess.Popen(["explorer", str(BASE_DIR / "videos")])

    def _start_processing(self):
        if self._processing:
            return

        # 收集勾选的项
        to_process = []
        for item in self.items:
            if item["var"].get() != 1:
                continue
            state = item["state_entry"].get().strip()
            if not state:
                continue
            trigger_cn = item["trigger_var"].get()
            trigger = self.TRIGGER_OPTIONS.get(trigger_cn, "manual")
            dialogue_text = item["dialogue_entry"].get().strip()
            dialogues = [d.strip() for d in dialogue_text.split("/") if d.strip()] if dialogue_text else [f"{state}~"]
            to_process.append({
                "state": state,
                "video": item["video_path"],
                "trigger": trigger,
                "label": item["filename"],
                "dialogues": dialogues,
            })

        if not to_process:
            self.progress_label.config(text="没有勾选任何视频！")
            return

        # 检查状态名是否合法（简单校验）
        for item in to_process:
            state = item["state"]
            if not state.replace("_", "").isalnum():
                self.progress_label.config(text=f"状态名 '{state}' 不合法，只能用字母数字下划线")
                return

        self._processing = True
        self.progress["maximum"] = len(to_process) * 3  # 3 步: extract, rembg, fix
        self.progress["value"] = 0

        def on_progress(step_text, current, total):
            self.progress_label.config(text=f"({current+1}/{total}) {step_text}")
            self.progress["value"] += 1

        def on_done():
            # 更新 state_configs
            for item in to_process:
                state = item["state"]
                self.pet.state_configs[state] = {
                    "trigger": item["trigger"],
                    "label": item["label"],
                    "dialogues": item["dialogues"],
                }
            # 重建触发列表和菜单
            self.pet._rebuild_trigger_lists()
            self.pet.rebuild_state_menu()
            self.pet.save_state_configs()
            # UI 反馈
            self.progress_label.config(text="全部完成！新素材已就绪~")
            self._processing = False
            self.pet.show_bubble("新素材已就绪~", 3000)
            self.win.after(1500, self.win.destroy)

        self.pet.process_assets(to_process, on_progress, on_done)


# ===================== 系统托盘（纯 ctypes，不依赖 pystray） =====================
class _TrayIcon:
    """系统托盘图标，用 Shell_NotifyIconW + 隐藏窗口消息循环实现。"""

    WM_TRAY = 0x0400 + 20
    NIM_ADD = 0
    NIM_DELETE = 2
    NIF_MESSAGE = 1
    NIF_ICON = 2
    NIF_TIP = 4
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONUP = 0x0205
    WM_CLOSE = 0x0010
    WM_DESTROY = 0x0002
    TPM_RIGHTBUTTON = 0x0002
    TPM_BOTTOMALIGN = 0x0020
    TPM_RETURNCMD = 0x0100
    IDI_APPLICATION = 32512
    IDC_ARROW = 32512

    class _NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", wintypes.HICON),
            ("szTip", wintypes.WCHAR * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", wintypes.WCHAR * 256),
            ("uTimeout", wintypes.UINT),
            ("szInfoTitle", wintypes.WCHAR * 64),
            ("dwInfoFlags", wintypes.DWORD),
        ]

    def __init__(self, pet):
        self.pet = pet
        self._hwnd = None
        self._thread = None
        self._running = False
        self._hicon = None
        self._wnd_proc_ref = None  # 防止 GC 回收 WNDPROC

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._hwnd:
            ctypes.windll.user32.PostMessageW(self._hwnd, self.WM_CLOSE, 0, 0)
        if self._thread:
            self._thread.join(timeout=2)

    def _make_icon(self):
        """从桌宠 idle 第一帧生成 HICON；失败则用系统默认图标。"""
        try:
            frames = self.pet.all_frames.get("idle", [])
            if not frames:
                raise ValueError("no idle frames")
            img = frames[0].convert("RGBA").resize((32, 32), Image.LANCZOS)
            self._hicon = _pil_to_hicon(img)
            if self._hicon:
                return self._hicon
        except Exception as e:
            print(f"tray icon from frame failed: {e}")
        self._hicon = ctypes.windll.user32.LoadIconW(0, self.IDI_APPLICATION)
        return self._hicon

    def _run(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # 设置 64 位安全的返回类型（句柄是指针，不能用默认 c_int）
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        user32.LoadIconW.restype = wintypes.HICON
        user32.LoadCursorW.restype = wintypes.HANDLE
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
            wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
        ]
        user32.DefWindowProcW.restype = ctypes.c_long
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        ]
        user32.RegisterClassW.restype = wintypes.ATOM
        user32.CreatePopupMenu.restype = wintypes.HMENU
        user32.CreateIconIndirect.restype = wintypes.HICON
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        gdi32 = ctypes.windll.gdi32
        gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
        gdi32.CreateBitmap.restype = wintypes.HBITMAP

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        class WNDCLASS(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == self.WM_TRAY:
                if lparam == self.WM_LBUTTONUP:
                    self.pet.root.after(0, self.pet.show)
                elif lparam == self.WM_RBUTTONUP:
                    self._show_popup_menu(hwnd)
                return 0
            elif msg == self.WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            elif msg == self.WM_DESTROY:
                self._delete_icon(hwnd)
                kernel32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc_ref = WNDPROC(wnd_proc)

        wc = WNDCLASS()
        wc.style = 0
        wc.lpfnWndProc = self._wnd_proc_ref
        wc.cbClsExtra = 0
        wc.cbWndExtra = 0
        wc.hInstance = kernel32.GetModuleHandleW(None)
        wc.hIcon = user32.LoadIconW(0, self.IDI_APPLICATION)
        wc.hCursor = user32.LoadCursorW(0, self.IDC_ARROW)
        wc.hbrBackground = 0
        wc.lpszMenuName = None
        wc.lpszClassName = "CatGirlTray"

        atom = user32.RegisterClassW(ctypes.byref(wc))
        if not atom:
            return

        self._hwnd = user32.CreateWindowExW(
            0, "CatGirlTray", "CatGirl Tray", 0,
            0, 0, 0, 0, 0, 0, wc.hInstance, 0,
        )
        if not self._hwnd:
            return

        self._add_icon()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        self._hwnd = None

    def _add_icon(self):
        nid = self._NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(nid)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        nid.uCallbackMessage = self.WM_TRAY
        nid.hIcon = self._make_icon()
        nid.szTip = "猫耳女友桌宠 (点击恢复)"
        ctypes.windll.shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(nid))

    def _delete_icon(self, hwnd):
        nid = self._NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(nid)
        nid.hWnd = hwnd
        nid.uID = 1
        ctypes.windll.shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(nid))

    def _show_popup_menu(self, hwnd):
        user32 = ctypes.windll.user32
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, 0, 1, "显示桌宠")
        user32.AppendMenuW(menu, 0, 2, "退出")

        # 获取光标位置
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))

        # 必须在前台才能显示菜单（Windows 要求）
        user32.SetForegroundWindow(hwnd)

        cmd = user32.TrackPopupMenu(
            menu,
            self.TPM_RIGHTBUTTON | self.TPM_BOTTOMALIGN | self.TPM_RETURNCMD,
            pt.x, pt.y, 0, hwnd, None,
        )

        user32.PostMessageW(hwnd, 0x0112, 0, 0)  # WM_NULL，让菜单正确关闭

        if cmd == 1:
            self.pet.root.after(0, self.pet.show)
        elif cmd == 2:
            self.pet.root.after(0, self.pet.on_close)

        user32.DestroyMenu(menu)


def _pil_to_hicon(img):
    """将 PIL RGBA 图像转换为 Windows HICON。"""
    import numpy as np
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    size = img.width  # 假设正方形
    arr = np.array(img.convert("RGBA"), dtype=np.uint8)  # (h, w, 4)

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", ctypes.c_long),
            ("biHeight", ctypes.c_long),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", ctypes.c_long),
            ("biYPelsPerMeter", ctypes.c_long),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ("bmiHeader", BITMAPINFOHEADER),
            ("bmiColors", wintypes.DWORD * 3),
        ]

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL),
            ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD),
            ("hbmMask", wintypes.HBITMAP),
            ("hbmColor", wintypes.HBITMAP),
        ]

    # 准备 32-bit BGRA 像素数据（Windows DIB 格式，bottom-up）
    bgra = np.zeros((size, size, 4), dtype=np.uint8)
    bgra[:, :, 0] = arr[:, :, 2]  # B
    bgra[:, :, 1] = arr[:, :, 1]  # G
    bgra[:, :, 2] = arr[:, :, 0]  # R
    bgra[:, :, 3] = arr[:, :, 3]  # A
    # 翻转为 bottom-up
    bgra = bgra[::-1, :, :]
    pixel_bytes = bgra.tobytes()

    # 创建 32-bit DIB section 作为 color bitmap
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = size
    bmi.bmiHeader.biHeight = size  # 正数 = bottom-up
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0  # BI_RGB

    hdc = user32.GetDC(0)
    color_bmp = gdi32.CreateCompatibleBitmap(hdc, size, size)

    # SetDIBits 把像素数据写入 color bitmap
    gdi32.SetDIBitsToDevice(
        hdc, 0, 0, size, size, 0, 0, 0, size,
        pixel_bytes, ctypes.byref(bmi), 0,
    )
    user32.ReleaseDC(0, hdc)

    # 创建 mask bitmap（1-bit，alpha > 0 的地方为 0）
    mask_arr = (arr[:, :, 3] > 0).astype(np.uint8) * 0  # mask: 0=visible, 1=transparent
    mask_bytes = np.packbits(mask_arr.flatten()).tobytes()
    # mask 是 bottom-up
    mask_bmp = gdi32.CreateBitmap(size, size, 1, 1, mask_bytes[::-1].tobytes() if len(mask_bytes) > 0 else None)

    # 创建 ICONINFO
    ii = ICONINFO()
    ii.fIcon = True
    ii.xHotspot = 0
    ii.yHotspot = 0
    ii.hbmMask = mask_bmp
    ii.hbmColor = color_bmp

    hicon = user32.CreateIconIndirect(ctypes.byref(ii))

    # 清理
    gdi32.DeleteObject(color_bmp)
    gdi32.DeleteObject(mask_bmp)

    return hicon or None


if __name__ == "__main__":
    DesktopPet().run()
