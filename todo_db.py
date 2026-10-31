"""
todo.db 的 SQLite 读写封装，供 main.py / app.py / desktop_sticky 共用。
todos 表字段：id, task, remind_time, is_completed
"""

import os
import sqlite3
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "todo.db")


def get_conn() -> sqlite3.Connection:
    """打开数据库连接（调用方用 with 自动提交/回滚）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库：建 todos 表（已存在则跳过），可重复调用"""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                remind_time TEXT,
                is_completed INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def add_todo(task: str, remind_time: Optional[str] = None) -> int:
    """新增一条待办，返回新记录的 id"""
    init_db()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO todos (task, remind_time, is_completed) VALUES (?, ?, 0)",
            (task, remind_time),
        )
        return cur.lastrowid


def list_todos(include_completed: bool = False) -> list:
    """按 id 升序返回待办；默认只返回未完成的"""
    init_db()
    sql = "SELECT * FROM todos"
    if not include_completed:
        sql += " WHERE is_completed = 0"
    sql += " ORDER BY id"
    with get_conn() as conn:
        return conn.execute(sql).fetchall()


def complete_todo(todo_id: int) -> None:
    """把某条待办标记为已完成"""
    with get_conn() as conn:
        conn.execute("UPDATE todos SET is_completed = 1 WHERE id = ?", (todo_id,))


def delete_todo(todo_id: int) -> None:
    """删除某条待办"""
    with get_conn() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def due_todos(now_minute: str, now_second: str) -> list:
    """返回 remind_time 与当前时间匹配的未完成待办（分钟 / 秒级都支持）"""
    init_db()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE is_completed = 0 AND remind_time IS NOT NULL"
        ).fetchall()

    due = []
    for row in rows:
        remind_time = row["remind_time"]
        target = now_second if len(remind_time) >= 19 else now_minute
        if remind_time == target:
            due.append(row)
    return due
