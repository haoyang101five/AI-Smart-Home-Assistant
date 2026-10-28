"""
Streamlit 网页版 AI 智能管家（独立版）：
- 输入指令后调用 DeepSeek 大模型，回复用 st.write 显示
- 如果指令是记待办/提醒类，会把内容（带当前时间戳）追加到当前目录的 todo.txt
运行方式：streamlit run app.py
"""

import os
from datetime import datetime

import streamlit as st
from openai import OpenAI

# ========== 大模型配置（请填入你的 API Key） ==========
client = OpenAI(
    api_key="你的API_KEY",
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

# 与 desktop_sticky.pyw 读取的是同一个文件（脚本所在目录的 todo.txt）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TODO_FILE = os.path.join(BASE_DIR, "todo.txt")

# 命中这些关键词时，把指令作为待办写入文件
TODO_KEYWORDS = ["待办", "提醒", "记一下", "记住", "别忘了", "todo"]


def save_todo(task: str) -> str:
    """把待办内容（带当前时间戳）追加写入 todo.txt"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{timestamp}] {task}"
    with open(TODO_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line


def ask_model(user_text: str) -> str:
    """调用 DeepSeek，返回模型的文字回复"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是一个友好的中文智能管家，回答简洁。"},
            {"role": "user", "content": user_text},
        ],
    )
    return resp.choices[0].message.content or "(无回复)"


# ========== 页面 ==========
st.title("我的 AI 智能管家")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("请输入你的指令", placeholder="例如：提醒我明天下午3点开会")
    submitted = st.form_submit_button("发送")

if submitted:
    text = user_input.strip()
    if not text:
        st.warning("请先输入指令")
    else:
        # 待办类指令：带时间戳追加到 todo.txt
        if any(kw in text for kw in TODO_KEYWORDS):
            saved = save_todo(text)
            st.info(f"已记录待办：{saved}")

        try:
            with st.spinner("助手思考中..."):
                reply = ask_model(text)
            st.write("助手：", reply)
        except Exception as e:
            st.error(f"调用大模型出错了: {e}")
