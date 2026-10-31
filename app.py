# -*- coding: utf-8 -*-
"""
Streamlit 网页版 AI 智能管家（纯 B/S 架构）：
- 输入指令 → 调用 DeepSeek 大模型，回复用 st.write 显示
- 记待办类指令 → 让模型换算成标准时间，写入 todo.db（SQLite 的 todos 表）
- 页面每 5 秒轮询一次数据库；到点的待办用浏览器 Notification 弹出系统通知
运行方式：streamlit run app.py
"""

import json
import re
import sys
import traceback
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

import todo_db

# 强制标准输出 / 错误流使用 UTF-8：
# Windows 终端或某些运行环境编码不是 UTF-8 时，打印中文会触发
# "'ascii' codec can't encode characters" 报错
if hasattr(sys.stdout, "reconfigure") and getattr(sys.stdout, "encoding", None) != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure") and getattr(sys.stderr, "encoding", None) != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ========== 大模型配置（请填入你的 API Key） ==========
client = OpenAI(
    # 注意：API Key 只能包含 ASCII 字符。用中文占位符（如"你的API_KEY"）会在
    # 生成 Authorization 请求头时报 "'ascii' codec can't encode characters"。
    api_key="你的API_KEY",
    base_url="https://api.deepseek.com",
    # 显式指定请求头的字符集，请求体由 SDK 用标准 JSON 序列化
    default_headers={"Content-Type": "application/json; charset=utf-8"},
)
MODEL = "deepseek-chat"

# 命中这些关键词时，把指令当作待办处理
TODO_KEYWORDS = ["待办", "提醒", "记一下", "记住", "别忘了", "todo"]

# 匹配模型输出的 "[2026-01-01 09:00] 任务" / "[2026-01-01 09:00:00] 任务"
TIME_PATTERN = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)\]\s*(.*)$")

todo_db.init_db()  # 启动时确保 todos 表存在


def ask_model(user_text: str, system: str = "你是一个友好的中文智能管家，回答简洁。") -> str:
    """调用 DeepSeek，返回模型的文字回复"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
    )
    return resp.choices[0].message.content or "(无回复)"


def extract_todo(text: str):
    """让模型把指令换算成 (remind_time, task)；没有时间则 remind_time 为 None"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = (
        f"当前时间：{now}。请把下面这句话里的提醒时间换算成标准格式，只输出一行，不要解释：\n"
        "有明确或可推算的时间时，输出：[YYYY-MM-DD HH:MM] 任务内容；\n"
        "用户明确要求提醒但没说时间时，按 5 分钟后处理；\n"
        "完全没提时间也没有提醒意图时，输出：[无时间] 任务内容。\n"
        f"指令：{text}"
    )
    raw = ask_model(prompt, system="你只负责抽取待办内容和提醒时间，严格按要求的格式输出，不加任何解释。").strip()

    match = TIME_PATTERN.match(raw)
    if match:
        return match.group(1), match.group(2).strip()
    if raw.startswith("[无时间]"):
        return None, raw[len("[无时间]"):].strip() or text
    return None, text


def save_todo(text: str) -> str:
    """提取提醒时间后写入 todos 表，返回提示用的摘要"""
    remind_time, task = extract_todo(text)
    todo_id = todo_db.add_todo(task, remind_time)
    prefix = f"[{remind_time}] " if remind_time else ""
    return f"#{todo_id} {prefix}{task}"


# ========== 浏览器通知（前端 JS） ==========

PERMISSION_HTML = """
<div style="font-family:'Microsoft YaHei',sans-serif;font-size:13px;color:#555;line-height:1.6;">
  <button id="enableNotify"
          style="padding:6px 12px;border:1px solid #ccc;border-radius:6px;
                 background:#f7f7f7;cursor:pointer;font-size:13px;">
    开启浏览器通知
  </button>
  <button id="testNotify"
          style="padding:6px 12px;border:1px solid #ccc;border-radius:6px;
                 background:#f7f7f7;cursor:pointer;font-size:13px;margin-left:6px;">
    发送测试通知
  </button>
  <div id="permStatus" style="margin-top:6px;">状态：检测中…</div>
  <div id="detail" style="margin-top:4px;color:#b00020;font-size:12px;"></div>
</div>
<script>
(function () {
  var statusEl = document.getElementById('permStatus');
  var detailEl = document.getElementById('detail');

  function setDetail(msg, color) {
    detailEl.textContent = msg || '';
    detailEl.style.color = color || '#b00020';
  }

  function paint() {
    if (!('Notification' in window)) {
      statusEl.textContent = '状态：当前浏览器不支持 Notification API，无法弹出系统通知';
      setDetail('请改用 Chrome / Edge / Firefox 等现代浏览器打开本页面。');
      return;
    }
    var p = Notification.permission;
    if (p === 'granted') {
      statusEl.textContent = '状态：已授权（granted），通知可以正常工作';
      setDetail('');
    } else if (p === 'denied') {
      statusEl.textContent = '状态：已被拒绝（denied），再点按钮也不会弹出授权框';
      setDetail('请点击地址栏左侧的图标 → 网站设置 → 通知 → 选择“允许”，然后刷新页面。');
    } else {
      statusEl.textContent = '状态：尚未授权（default），请点击左侧「开启浏览器通知」';
      setDetail('');
    }
  }

  function fireTest() {
    try {
      new Notification('测试通知', { body: '看到这条说明浏览器通知已经正常工作' });
      setDetail('已发送测试通知；如果系统没弹出，请检查系统设置里的通知开关。', '#0a7d32');
    } catch (e) {
      setDetail('创建通知失败：' + e.name + ' - ' + e.message);
    }
  }

  document.getElementById('enableNotify').onclick = function () {
    if (!('Notification' in window)) { paint(); return; }
    if (Notification.permission === 'denied') { paint(); return; }
    try {
      var result = Notification.requestPermission(function () { paint(); });
      if (result && typeof result.then === 'function') {
        result.then(function (p) {
          paint();
          if (p === 'granted') fireTest();
        }).catch(function (e) {
          setDetail('请求授权失败：' + e.name + ' - ' + e.message);
        });
      }
    } catch (e) {
      setDetail('请求授权异常：' + e.name + ' - ' + e.message);
    }
  };

  document.getElementById('testNotify').onclick = function () {
    if (!('Notification' in window)) { paint(); return; }
    if (Notification.permission !== 'granted') { paint(); return; }
    fireTest();
  };

  // 沙箱自检：如果组件被塞进不带 allow-same-origin 的 iframe，
  // localStorage 会直接抛异常，这正是「点按钮没反应」的典型原因
  try {
    window.localStorage.setItem('__notify_probe', '1');
    window.localStorage.removeItem('__notify_probe');
  } catch (e) {
    setDetail('检测到组件运行在受限沙箱中（localStorage 不可用），通知会被浏览器拦截：' + e.name);
  }

  paint();
})();
</script>
"""

NOTIFY_HTML = """
<script>
var dueItems = __DUE__;
if ('Notification' in window && Notification.permission === 'granted') {
  dueItems.forEach(function (item) {
    new Notification('待办提醒', { body: item.task });
  });
}
</script>
"""


# ========== 页面 ==========
st.title("我的 AI 智能管家")
st.caption("可以试试：提醒我明天下午3点开会，顺便查一下天津的天气")

# 说明：st.components.html 的 iframe sandbox 由 Streamlit 自己固定为
# allow-forms allow-modals allow-popups allow-popups-to-escape-sandbox
# allow-same-origin allow-scripts allow-downloads，组件内无法再改 sandbox 属性；
# 因此这里用 JS 自检代替（能检测出同源被阻断、通知不可用等情况）。
components.html(PERMISSION_HTML, height=95)


@st.fragment(run_every="5s")
def reminder_panel() -> None:
    """每 5 秒轮询一次数据库，到点且本次会话没提醒过的待办交给 JS 弹通知"""
    now = datetime.now()
    due = todo_db.due_todos(
        now.strftime("%Y-%m-%d %H:%M"),
        now.strftime("%Y-%m-%d %H:%M:%S"),
    )

    if "notified_ids" not in st.session_state:
        st.session_state["notified_ids"] = set()
    new_due = [row for row in due if row["id"] not in st.session_state["notified_ids"]]
    for row in new_due:
        st.session_state["notified_ids"].add(row["id"])

    payload = [
        {"id": row["id"], "task": row["task"] or "(未填写内容)"} for row in new_due
    ]
    components.html(NOTIFY_HTML.replace("__DUE__", json.dumps(payload, ensure_ascii=False)), height=1)


reminder_panel()

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("请输入你的指令", placeholder="例如：提醒我明天下午3点开会")
    submitted = st.form_submit_button("发送")

if submitted:
    text = user_input.strip()
    if not text:
        st.warning("请先输入指令")
    else:
        # 待办类指令：提取时间后写入 todos 表
        if any(kw in text for kw in TODO_KEYWORDS):
            try:
                saved = save_todo(text)
                st.info(f"已记录待办：{saved}")
            except Exception as e:
                traceback.print_exc()  # 打印完整堆栈到运行 streamlit 的终端
                st.error(f"保存待办失败: {e}")

        try:
            with st.spinner("助手思考中..."):
                reply = ask_model(text)
            st.write("助手：", reply)
        except Exception as e:
            traceback.print_exc()  # 打印完整堆栈到运行 streamlit 的终端
            st.error(f"调用大模型出错了: {e}")
