#!/usr/bin/env python3
"""s01: 一个确定性、无外部副作用的最小 Agent Loop。"""


class ScriptedModel:
    def complete(self, messages: list[dict]) -> dict:
        if not any(message["role"] == "tool" for message in messages):
            return {"role": "assistant", "type": "tool_call", "name": "list_files"}
        files = messages[-1]["content"]
        return {"role": "assistant", "type": "final", "text": f"项目包含：{files}"}


def list_files() -> str:
    print("TOOL     list_files()")
    return "README.md, app.py, tests.py"


def agent_loop(query: str) -> str:
    model = ScriptedModel()
    messages = [{"role": "user", "content": query}]

    while True:
        response = model.complete(messages)
        messages.append(response)

        if response["type"] == "final":
            print(f"MODEL    {response['text']}")
            return response["text"]

        print(f"MODEL    请求 {response['name']}")
        result = list_files()
        messages.append({"role": "tool", "content": result})
        print(f"HARNESS  把工具结果送回消息流：{result}")


if __name__ == "__main__":
    agent_loop("这个项目里有什么？")
