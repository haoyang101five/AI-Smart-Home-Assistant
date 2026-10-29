# 🤖 多端联动 AI 智能管家

基于 DeepSeek 大模型与 Python 开发的跨端智能提醒系统。

## ✨ 核心功能
- **多工具编排 (Tool Calling)**：大模型自主调度本地文件写入与天气 API 请求。
- **多端实时联动**：Web 端 (Streamlit) 下达指令，桌面端 (Tkinter) 悬浮便签实时刷新。
- **定时主动干预**：后台守护进程精准识别时间戳，到点自动弹窗响铃。

## 🛠️ 技术栈
- 前端：Streamlit (Web), Tkinter (Desktop)
- 后端：Python, OpenAI SDK
- 大模型：DeepSeek (deepseek-chat)

## 🚀 运行方式
1. `pip install -r requirements.txt`
2. 填入你的 DeepSeek API Key
3. `streamlit run app.py`

## 🏗️ 系统架构

```text
Streamlit Web 界面 (app.py)
    │
    ├── 用户自然语言输入 (聊天框)
    ▼
DeepSeek 大模型 (Agent 核心)
    │
    ├── 工具 1：add_todo(task) ────> 写入本地文件 (todo.txt)
    └── 工具 2：get_weather(city) ─> 请求外部天气 API (wttr.in)
    │
    ▼
桌面悬浮便签守护进程 (desktop_sticky.pyw)
    │
    ├── 每 1 秒轮询读取 (todo.txt)
    ├── 识别标准时间戳格式 [YYYY-MM-DD HH:MM]
    └── 到点触发：Win系统弹窗 + 提示音