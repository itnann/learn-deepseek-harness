#!/usr/bin/env python3
"""s03: allow / ask / deny 策略管线。所有文件都在内存中。"""

from dataclasses import dataclass
from typing import Callable, Literal


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class PolicyDecision:
    effect: Literal["allow", "ask", "deny"]
    reason: str


class Registry:
    def __init__(self, handlers: dict[str, Callable[..., str]]) -> None:
        self.handlers = handlers

    def execute(self, call: ToolCall) -> str:
        return self.handlers[call.name](**call.arguments)


def decide(call: ToolCall) -> PolicyDecision:
    path = call.arguments.get("path", "")
    if path == ".env":
        return PolicyDecision("deny", "凭据文件不可读取")
    if call.name == "delete_file":
        return PolicyDecision("ask", "删除会改变工作区")
    return PolicyDecision("allow", "只读或低风险操作")


def approve(call: ToolCall, reason: str) -> bool:
    print(f"APPROVAL 请求确认：{call.name}，原因：{reason} -> 教学模式允许")
    return True


class ToolRuntime:
    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def execute(self, call: ToolCall) -> str:
        decision = decide(call)
        print(f"POLICY   {decision.effect}: {decision.reason}")
        if decision.effect == "deny":
            return f"blocked: {decision.reason}"
        if decision.effect == "ask" and not approve(call, decision.reason):
            return f"blocked by user: {decision.reason}"
        return self.registry.execute(call)


class ScriptedModel:
    def __init__(self) -> None:
        self.calls = iter([
            ToolCall("read_file", {"path": "README.md"}),
            ToolCall("delete_file", {"path": "draft.txt"}),
            ToolCall("read_file", {"path": ".env"}),
        ])

    def complete(self, _messages: list[dict]) -> ToolCall | str:
        return next(self.calls, "任务结束：普通读取成功，删除经审批，凭据读取被拒绝。")


def main() -> None:
    files = {"README.md": "hello", "draft.txt": "old", ".env": "SECRET"}
    registry = Registry({
        "read_file": lambda path: files.get(path, "not found"),
        "delete_file": lambda path: "deleted" if files.pop(path, None) is not None else "not found",
    })
    runtime, model, messages = ToolRuntime(registry), ScriptedModel(), []
    while True:
        response = model.complete(messages)
        if isinstance(response, str):
            print(f"MODEL    {response}")
            break
        print(f"MODEL    请求 {response.name}{response.arguments}")
        result = runtime.execute(response)
        print(f"TOOL     {result}\n")
        messages.append({"role": "tool", "content": result})


if __name__ == "__main__":
    main()
