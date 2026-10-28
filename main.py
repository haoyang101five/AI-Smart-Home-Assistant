"""
终端 AI 助手：接入 DeepSeek（deepseek-chat），支持两个工具：
  1. add_todo(task)    - 把任务追加保存到当前目录的 todo.txt
  2. get_weather(city) - 调用 wttr.in 查询城市天气
在终端输入指令（如"明天下午3点提醒我开会，顺便查一下天津的天气"），
模型会自主决定调用哪些工具，工具结果回传后输出一句友好的总结回复。
输入 exit / quit / 退出 可结束程序。
"""

import json
from datetime import datetime, timedelta

import requests
from openai import OpenAI

# ========== 基础配置 ==========

client = OpenAI(
    api_key="你的API_KEY",
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"


# ========== 工具实现 ==========

def add_todo(task: str) -> str:
    """把任务追加写入当前目录下的 todo.txt"""
    with open("todo.txt", "a", encoding="utf-8") as f:
        f.write(task + "\n")
    return "保存成功"


def get_weather(city: str) -> str:
    """调用 wttr.in 查询城市天气概况"""
    url = f"https://wttr.in/{city}?format=3"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text.strip()
    except Exception as e:
        return f"天气查询失败: {e}"


AVAILABLE_TOOLS = {
    "add_todo": add_todo,
    "get_weather": get_weather,
}

# ========== 工具 Schema（OpenAI function calling 格式） ==========

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todo",
            "description": "把一条待办任务追加保存到 todo.txt 文件中",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "要保存的任务内容，例如：明天下午3点开会",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前天气概况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，例如：天津",
                    }
                },
                "required": ["city"],
            },
        },
    },
]

def get_system_prompt() -> str:
    """动态生成 System Prompt：注入当前时间，并规定 add_todo 的时间格式与默认提醒时间"""
    current_time = datetime.now()
    now = current_time.strftime("%Y-%m-%d %H:%M")
    default_time = (current_time + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M")
    return (
        "你是一个终端智能助手，可以使用两个工具：\n"
        "1. add_todo：把用户的待办任务保存到 todo.txt；\n"
        "2. get_weather：查询城市天气。\n"
        f"1. 当前系统时间是 {now}。\n"
        "2. 如果用户让你提醒，但没给具体时间，请默认推算为 5 分钟后"
        f"（本次应为 {default_time}）。\n"
        "3. 调用 add_todo 时，必须严格按照 [YYYY-MM-DD HH:MM] 任务内容 的格式存入文件，"
        "时间部分不能省略；用户说的模糊时间（如明天下午3点）要先换算成该格式。\n"
        "请根据用户指令自主决定是否调用工具、调用哪个工具、调用几次；"
        "如果一句话里包含多个需求，把它们全部完成。"
        "所有工具执行完毕后，用一句友好的中文总结回复用户。"
    )


# ========== Agent 核心逻辑 ==========

def run_tool(name: str, arguments: str) -> str:
    """按名称执行工具，把结果转成字符串"""
    try:
        args = json.loads(arguments) if arguments else {}
        fn = AVAILABLE_TOOLS.get(name)
        if fn is None:
            return f"未知工具: {name}"
        return str(fn(**args))
    except Exception as e:
        return f"工具 {name} 执行出错: {e}"


def chat(messages: list) -> str:
    """发送对话给模型，自动处理工具调用循环，最后打印并返回总结回复"""
    while True:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg = resp.choices[0].message

        # 模型请求调用工具
        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                result = run_tool(call.function.name, call.function.arguments)
                print(f"  [工具] {call.function.name} -> {result}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )
            continue  # 把工具结果交回模型继续对话

        # 没有工具调用，输出最终回复
        messages.append({"role": "assistant", "content": msg.content})
        print(f"助手: {msg.content or '(无回复)'}")
        return msg.content or ""


def main() -> None:
    print("终端 AI 助手已启动（输入 exit / quit / 退出 结束）")
    messages = [{"role": "system", "content": get_system_prompt()}]
    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"} or user_input == "退出":
            print("再见！")
            break

        messages.append({"role": "user", "content": user_input})
        try:
            chat(messages)
        except Exception as e:
            print(f"出错了: {e}")
            messages.pop()  # 移除失败的用户消息，避免污染上下文


if __name__ == "__main__":
    main()
