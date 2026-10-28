"""
桌面悬浮便签 + 定时提醒（.pyw 版本，双击运行时不会出现黑色控制台窗口）：
- 无边框、半透明黑底、置顶，固定在屏幕右上角
- 每 1 秒读取一次 todo.txt 并刷新显示
- 支持 [YYYY-MM-DD HH:MM:SS]（精确到秒）和 [YYYY-MM-DD HH:MM]（精确到分钟）两种时间格式：
  时间与当前系统时间相同时，播放提示音 + 弹出提醒弹窗，然后把该条从 todo.txt 删除，防止重复提醒
- 按 Esc 或右键菜单可退出
运行方式：双击 desktop_sticky.pyw，或 pythonw desktop_sticky.pyw
"""

import os
import re
import tkinter as tk
import winsound
from datetime import datetime
from tkinter import messagebox

# 与 main.py 的 add_todo 保持同一目录（脚本所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TODO_FILE = os.path.join(BASE_DIR, "todo.txt")

REFRESH_MS = 1000  # 自动刷新间隔（毫秒）
ALPHA = 0.85  # 窗口整体透明度

# 匹配 "[2024-05-20 15:00:30] 任务" 或 "[2024-05-20 15:00] 任务"，秒部分可选
TIME_PATTERN = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})(?::(\d{2}))?\]\s*(.*)$")


def load_todos() -> list:
    """读取 todo.txt，返回行列表（去掉空行）；文件不存在返回空列表"""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except OSError:
        return []


def save_todos(lines: list) -> None:
    """把剩余待办写回 todo.txt"""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def check_reminders(lines: list) -> list:
    """检查到期待办：弹窗 + 提示音，返回需要保留的行（到期的已被移除）"""
    now = datetime.now()
    now_minute = now.strftime("%Y-%m-%d %H:%M")  # 不带秒的行按分钟比较
    now_second = now.strftime("%Y-%m-%d %H:%M:%S")  # 带秒的行按秒比较
    remaining = []
    for line in lines:
        match = TIME_PATTERN.match(line)
        if match:
            seconds = match.group(2)
            todo_time = match.group(1) + (f":{seconds}" if seconds else "")
            target = now_second if seconds else now_minute
            if todo_time == target:
                task = match.group(3) or "(未填写内容)"
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)  # 系统提示音
                messagebox.showwarning("待办提醒", f"时间到了！该做{task}了")
                continue  # 不加入 remaining，相当于从 todo.txt 中删除
        remaining.append(line)
    return remaining


def main() -> None:
    root = tk.Tk()
    root.overrideredirect(True)  # 无边框
    root.attributes("-topmost", True)  # 置顶
    root.attributes("-alpha", ALPHA)  # 半透明
    root.configure(bg="black")

    # 固定在屏幕右上角
    win_w, win_h = 320, 220
    screen_w = root.winfo_screenwidth()
    root.geometry(f"{win_w}x{win_h}+{screen_w - win_w - 20}+20")

    # ========== 标题栏 ==========
    header = tk.Frame(root, bg="black")
    header.pack(fill="x", padx=10, pady=(8, 0))

    title = tk.Label(
        header, text="待办事项", bg="black", fg="white",
        font=("Microsoft YaHei", 10, "bold"),
    )
    title.pack(side="left")

    hint = tk.Label(
        header, text="Esc 退出", bg="black", fg="#888888",
        font=("Microsoft YaHei", 8),
    )
    hint.pack(side="right")

    # ========== 待办内容 ==========
    content = tk.Label(
        root, text="", bg="black", fg="white",
        font=("Microsoft YaHei", 10),
        justify="left", anchor="nw", wraplength=290,
    )
    content.pack(fill="both", expand=True, padx=10, pady=(6, 10))

    # ========== 定时刷新 + 提醒检查 ==========
    def refresh() -> None:
        lines = load_todos()
        remaining = check_reminders(lines)
        if len(remaining) != len(lines):
            save_todos(remaining)  # 有待办被触发，写回文件
        content.config(text="\n".join(remaining) if remaining else "暂无待办")
        root.after(REFRESH_MS, refresh)

    refresh()

    # ========== 退出机制 ==========
    root.bind("<Escape>", lambda event: root.destroy())

    menu = tk.Menu(root, tearoff=0, bg="black", fg="white")
    menu.add_command(label="退出", command=root.destroy)

    def show_menu(event) -> None:
        menu.post(event.x_root, event.y_root)

    for widget in (root, header, title, content):
        widget.bind("<Button-3>", show_menu)  # 右键弹出菜单

    # 无边框窗口默认拿不到焦点，强制聚焦以保证 Esc 生效
    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()
