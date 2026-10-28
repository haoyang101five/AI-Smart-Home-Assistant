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
