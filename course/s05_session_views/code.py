#!/usr/bin/env python3
"""s05: 完整事实与面向模型/UI 的视图分离。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Event:
    kind: str
    data: dict[str, Any]


class Session:
    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def audit_view(self) -> list[Event]:
        return list(self._events)

    def model_view(self) -> list[dict]:
        messages = []
        for event in self._events:
            if event.kind == "message":
                messages.append(event.data)
            elif event.kind == "tool_result":
                messages.append({"role": "tool", "content": event.data["output"]})
            # policy 和 trace 是事实，但不占用模型上下文。
        return messages

    def ui_view(self) -> list[str]:
        rows = []
        for event in self._events:
            if event.kind == "message":
                rows.append(f"{event.data['role']}: {event.data['content']}")
            elif event.kind == "tool_result":
                rows.append(f"工具 {event.data['tool']} 完成：{event.data['output']}")
        return rows


if __name__ == "__main__":
    session = Session()
    session.append(Event("message", {"role": "user", "content": "读取 README"}))
    session.append(Event("message", {"role": "assistant", "content": "调用 read_file"}))
    session.append(Event("policy", {"effect": "allow", "rule": "workspace-read"}))
    session.append(Event("trace", {"latency_ms": 1.7}))
    session.append(Event("tool_result", {"tool": "read_file", "output": "Harness 学习项目"}))

    print("AUDIT   完整事实：")
    for item in session.audit_view():
        print("        ", item)
    print("\nMODEL   只看推理所需消息：", session.model_view())
    print("\nUI      面向人的展示：")
    for row in session.ui_view():
        print("        ", row)
