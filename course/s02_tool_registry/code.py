#!/usr/bin/env python3
"""s02: 用注册表把工具数量与 Agent Loop 解耦。"""

from dataclasses import dataclass
from typing import Callable


VIRTUAL_FILES = {"README.md": "Harness 学习项目", "app.py": "print('hello')"}


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[..., str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def execute(self, call: ToolCall) -> str:
        if call.name not in self._tools:
            return f"error: unknown tool {call.name}"
        return self._tools[call.name].handler(**call.arguments)


class ScriptedModel:
    def __init__(self) -> None:
        self.step = 0

    def complete(self, _messages: list[dict]) -> ToolCall | str:
        script = [ToolCall("list_files", {}), ToolCall("read_file", {"path": "README.md"})]
        if self.step < len(script):
            call = script[self.step]
            self.step += 1
            return call
        return "我先发现 README.md，再读到：Harness 学习项目"


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool("list_files", "列出工作区文件", lambda: ", ".join(VIRTUAL_FILES)))
    registry.register(Tool("read_file", "读取一个文本文件", lambda path: VIRTUAL_FILES.get(path, "not found")))
    return registry


def agent_loop(query: str) -> str:
    model, registry = ScriptedModel(), build_registry()
    messages = [{"role": "user", "content": query}]
    while True:
        response = model.complete(messages)
        if isinstance(response, str):
            print(f"MODEL    {response}")
            return response
        print(f"MODEL    请求 {response.name}{response.arguments}")
        result = registry.execute(response)
        print(f"TOOL     {result}")
        messages.append({"role": "tool", "name": response.name, "content": result})


if __name__ == "__main__":
    agent_loop("先找说明文件，再告诉我内容")
