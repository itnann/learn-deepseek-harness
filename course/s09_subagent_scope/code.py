#!/usr/bin/env python3
"""s09: 子 Agent 通过派生 Scope 获得最小能力集。"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class Scope:
    capabilities: frozenset[str]

    def derive(self, allow: set[str]) -> "Scope":
        if not allow.issubset(self.capabilities):
            extra = allow - self.capabilities
            raise ValueError(f"child cannot gain capabilities: {sorted(extra)}")
        return Scope(frozenset(allow))


class ScopedRuntime:
    def __init__(self, handlers: dict[str, Callable[..., str]], scope: Scope) -> None:
        self.handlers, self.scope = handlers, scope

    def execute(self, call: ToolCall) -> str:
        if call.name not in self.scope.capabilities:
            return f"scope denied: {call.name}"
        return self.handlers[call.name](**call.arguments)


if __name__ == "__main__":
    files = {"app.py": "print('hello')"}
    handlers = {
        "read_file": lambda path: files.get(path, "not found"),
        "search": lambda text: f"found '{text}' in app.py",
        "write_file": lambda path, text: files.__setitem__(path, text) or "written",
    }
    parent_scope = Scope(frozenset(handlers))
    reviewer_scope = parent_scope.derive({"read_file", "search"})
    parent = ScopedRuntime(handlers, parent_scope)
    reviewer = ScopedRuntime(handlers, reviewer_scope)

    print("REVIEWER", reviewer.execute(ToolCall("read_file", {"path": "app.py"})))
    print("REVIEWER", reviewer.execute(ToolCall("write_file", {"path": "app.py", "text": "changed"})))
    print("PARENT  ", parent.execute(ToolCall("write_file", {"path": "notes.md", "text": "ok"})))
    try:
        reviewer_scope.derive({"deploy"})
    except ValueError as error:
        print("SCOPE    ", error)
