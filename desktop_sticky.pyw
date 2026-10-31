"""
桌面悬浮便签 + 定时提醒（.pyw 版本，双击运行时不会出现黑色控制台窗口）：
- 无边框、半透明黑底、置顶，固定在屏幕右上角
- 每 1 秒从 todo.db（SQLite 的 todos 表）读取一次待办并刷新显示
- remind_time 与当前系统时间匹配（支持分钟级和秒级）时：
  播放提示音 + 弹出提醒弹窗，然后把该条标记为 is_completed = 1，防止重复提醒
- 按 Esc 或右键菜单可退出
运行方式：双击 desktop_sticky.pyw，或 pythonw desktop_sticky.pyw
"""

import tkinter as tk
import winsound
from datetime import datetime
from tkinter import messagebox

import todo_db

REFRESH_MS = 1000  # 自动刷新间隔（毫秒）
ALPHA = 0.85  # 窗口整体透明度


def format_todo(row) -> str:
    """把一条数据库记录格式化成便签上显示的文字"""
    if row["remind_time"]:
        return f"[{row['remind_time']}] {row['task']}"
    return row["task"]


def check_reminders(now: datetime) -> None:
    """到期的待办：提示音 + 弹窗，并把它们标记为已完成"""
    due = todo_db.due_todos(
        now.strftime("%Y-%m-%d %H:%M"),
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )
    for row in due:
        task = row["task"] or "(未填写内容)"
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)  # 系统提示音
        messagebox.showwarning("待办提醒", f"时间到了！该做{task}了")
        todo_db.complete_todo(row["id"])  # 标记完成，避免重复提醒


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
        check_reminders(datetime.now())
        rows = todo_db.list_todos()
        lines = [format_todo(row) for row in rows]
        content.config(text="\n".join(lines) if lines else "暂无待办")
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
