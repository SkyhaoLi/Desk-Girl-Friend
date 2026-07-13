# -*- coding: utf-8 -*-
"""猫耳女友桌宠 - 完整版"""
import os, sys, math, random, json, subprocess, winreg, time
from pathlib import Path
from tkinter import Menu
from PIL import Image, ImageTk, ImageFilter

_tcl_dir = os.path.join(os.path.dirname(sys.executable), "tcl")
if os.path.exists(_tcl_dir):
    os.environ["TCL_LIBRARY"] = os.path.join(_tcl_dir, "tcl8.6")
    os.environ["TK_LIBRARY"] = os.path.join(_tcl_dir, "tk8.6")

import tkinter as tk

BASE_DIR = Path(__file__).parent
FRAMES_DIR = BASE_DIR / "assets" / "frames_fixed"
CONFIG_FILE = BASE_DIR / "config.json"

WIN_W, WIN_H, FPS = 130, 180, 24
TARGET_H = 150  # 角色高度

# ===================== 状态配置 =====================
# 互动触发（左键点击）
CLICK_STATES = ["greet", "cute", "shy"]

# 空闲随机触发（长时间无操作）
IDLE_RANDOM_STATES = ["yawn", "confused", "sad", "miss", "slacking"]

# 待机时偶尔插入的随机状态
IDLE_INTERRUPT_STATES = ["yawn", "confused", "slacking", "miss"]

# 待机静态帧显示时长（秒）
IDLE_STATIC_DURATION = 30

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

DIALOGUES = {
    "idle": ["...", "在发呆~", "(*^_^*)"],
    "work": ["工作中...", "认真ing", "加油~"],
    "exhausted": ["好累...", "终于干完了", "需要休息..."],
    "greet": ["嗨~", "你好呀！", "好久不见！"],
    "cute": ["看我看我~", "(*^▽^*)", "嘻嘻~"],
    "shy": ["讨厌~", "人家会害羞的", "别这样啦"],
    "yawn": ["困了...", "zzZ...", "打个哈欠~"],
    "confused": ["嗯？", "啥情况？", "？？？"],
    "sad": ["难过...", "委屈屈", "呜呜~"],
    "miss": ["想你了~", "你在哪", "好想你"],
    "slacking": ["偷偷摸鱼~", "嘿嘿", "放松一下"],
}


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
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text("utf-8"))
        return {"x": 1500, "y": 500}

    def save_config(self):
        self.config["x"] = self.root.winfo_x()
        self.config["y"] = self.root.winfo_y()
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

    def create_transition(self, from_state, to_state, num_frames=8):
        """创建两个状态之间的过渡帧"""
        if from_state not in self.all_frames or to_state not in self.all_frames:
            return

        from_frames = self.all_frames[from_state]
        to_frames = self.all_frames[to_state]

        # 取两个状态的最后一帧和第一帧
        from_img = from_frames[-1]
        to_img = to_frames[0]

        # 确保尺寸一致
        w1, h1 = from_img.size
        w2, h2 = to_img.size
        if (w1, h1) != (w2, h2):
            to_img = to_img.resize((w1, h1), Image.LANCZOS)

        transition = []
        for i in range(num_frames):
            alpha = i / (num_frames - 1)
            # 混合两帧
            blended = Image.blend(from_img, to_img, alpha)
            transition.append(blended)

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
        return random.choice(DIALOGUES.get(state or self.current_state, ["..."]))

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
            state = random.choice(CLICK_STATES)
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
                state = random.choice(IDLE_RANDOM_STATES)
                self.set_state(state, duration=FPS * 3)
                self.show_bubble(self.random_dialogue(state), 2500)

        self.root.after(self.WORK_CHECK_INTERVAL * 1000, self.check_idle)

    # ===================== 动画 =====================
    def animate(self):
        self.time += 1
        t = self.time

        # 状态计时
        if self.state_timer > 0:
            self.state_timer -= 1
            if self.state_timer == 0:
                self.set_state("idle")

        # 过渡动画
        if self.is_transitioning:
            self.transition_idx += 1
            if self.transition_idx >= len(self.transition_frames):
                self.is_transitioning = False
            else:
                img = self.transition_frames[self.transition_idx]
                self.tk_img = ImageTk.PhotoImage(img)
                self.canvas.itemconfig(self.char_id, image=self.tk_img)
                self.root.after(1000 // FPS, self.animate)
                return

        # 播放动画帧
        if self.current_state == "idle":
            # 静态待机，偶尔触发随机状态
            if t % (FPS * IDLE_STATIC_DURATION) == 0:
                if random.random() < 0.3:
                    interrupt = random.choice(IDLE_INTERRUPT_STATES)
                    self.set_state(interrupt, duration=FPS * 3)
                    self.show_bubble(self.random_dialogue(interrupt), 2500)
        elif self.frames and len(self.frames) > 1:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)

        # 整体动画参数（平滑过渡）
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
        if self.frames:
            base_img = self.frames[min(self.frame_idx, len(self.frames)-1)]
            img = base_img.copy()
            if abs(self.anim_rot) > 0.1:
                rotated = img.rotate(self.anim_rot, expand=True, resample=Image.BICUBIC)
                canvas_w = max(base_img.width, rotated.width)
                canvas_h = max(base_img.height, rotated.height)
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
        sm = Menu(self.menu, tearoff=0, font=("微软雅黑", 10))
        labels = {
            "idle": "待机", "work": "工作", "exhausted": "力竭",
            "greet": "打招呼", "cute": "卖萌", "shy": "害羞",
            "yawn": "哈欠", "confused": "懵圈", "sad": "委屈屈",
            "miss": "想你", "slacking": "摸鱼"
        }
        for s, l in labels.items():
            sm.add_command(label=l, command=lambda st=s: (self.set_state(st, FPS*3), self.show_bubble(self.random_dialogue(st), 2500)))
        self.menu.add_cascade(label="切换状态", menu=sm)
        self.menu.add_separator()
        for a in [{"l":"Open MiMo","c":["cmd","/c","start","mimo"]},{"l":"Open Claude","c":["cmd","/c","start","claude"]},
                  {"l":"Open WeChat","c":["cmd","/c","start","","https://weixin.qq.com/"]},{"l":"Open Terminal","c":["cmd","/c","start","wt"]}]:
            self.menu.add_command(label=a["l"], command=lambda c=a["c"]: (subprocess.Popen(c, shell=True), self.show_bubble("已打开~", 2000)))
        self.menu.add_separator()
        self.menu.add_command(label="添加视频素材", command=self.open_add_video)
        self.menu.add_command(label="设置开机自启", command=self.toggle_autostart)
        self.menu.add_command(label="退出", command=self.on_close)

    def show_menu(self, event):
        self.show_bubble(random.choice(["要做什么呢？", "请选择~"]), 2000)
        self.menu.post(event.x_root, event.y_root)

    def open_add_video(self):
        """打开添加视频素材的说明"""
        msg = "请将视频放入 videos/ 目录\n然后运行 add_video.bat"
        self.show_bubble(msg, 4000)
        # 打开videos文件夹
        subprocess.Popen(["explorer", str(BASE_DIR / "videos")])

    def toggle_autostart(self):
        runner = str(BASE_DIR / "autostart.bat")
        Path(runner).write_text(f'@echo off\ncd /d "{BASE_DIR}"\nset "TCL_LIBRARY={os.path.join(os.path.dirname(sys.executable),"tcl","tcl8.6")}"\nset "TK_LIBRARY={os.path.join(os.path.dirname(sys.executable),"tcl","tk8.6")}"\nstart "" pyw pet.pyw\n', "utf-8")
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
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    DesktopPet().run()
