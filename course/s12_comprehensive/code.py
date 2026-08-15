#!/usr/bin/env python3
"""s12: 无 API、无真实文件副作用的综合 Mini Harness。"""

from dataclasses import dataclass
from functools import reduce
from typing import Callable, Protocol


# ---------- Messages and model contract ----------

@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class FinalAnswer:
    text: str


ModelOutput = ToolCall | FinalAnswer


class ScriptedModel:
    """固定剧本让我们只观察 Harness，而不是模型随机性。"""

    def __init__(self) -> None:
        self.script = iter([
            ToolCall("list_files", {}),
            ToolCall("read_file", {"path": "README.md"}),
            ToolCall("read_file", {"path": ".env"}),
            FinalAnswer("完成：已读取说明；凭据文件被运行时拒绝。"),
        ])

    def complete(self, context: str, messages: list[dict]) -> ModelOutput:
        print(f"MODEL    context={len(context)} chars, messages={len(messages)}")
        return next(self.script)


# ---------- Durable facts and model projection ----------

@dataclass(frozen=True)
class Event:
    kind: str
    data: dict


class EventStore(Protocol):
    def append(self, session_id: str, event: Event) -> None: ...
    def load(self, session_id: str) -> list[Event]: ...


class MemoryEventStore:
    def __init__(self) -> None:
        self.events: dict[str, list[Event]] = {}

    def append(self, session_id: str, event: Event) -> None:
        self.events.setdefault(session_id, []).append(event)

    def load(self, session_id: str) -> list[Event]:
        return list(self.events.get(session_id, []))


class Session:
    def __init__(self, session_id: str, store: EventStore) -> None:
        self.session_id, self.store = session_id, store

    def append(self, kind: str, **data) -> None:
        self.store.append(self.session_id, Event(kind, data))

    def model_view(self) -> list[dict]:
        messages = []
        for event in self.store.load(self.session_id):
            if event.kind == "message":
                messages.append(event.data)
            elif event.kind == "tool_result":
                messages.append({"role": "tool", "content": event.data["output"]})
        return messages

    def audit_view(self) -> list[Event]:
        return self.store.load(self.session_id)


# ---------- Context assembly ----------

class ContextAssembler:
    def build(self, state: dict) -> str:
        blocks = [
            "你是编码助手；先观察再行动。",
            "安全边界由运行时执行，不能自行绕过。",
            f"工作区：{state['workspace']}。",
            f"当前能力：{', '.join(sorted(state['capabilities']))}。",
        ]
        return "\n".join(blocks)


# ---------- Tools, scope, policy, and middleware ----------

@dataclass(frozen=True)
class Scope:
    capabilities: frozenset[str]


Handler = Callable[[ToolCall], str]
Middleware = Callable[[ToolCall, Handler], str]


class ToolRegistry:
    def __init__(self) -> None:
        self.handlers: dict[str, Callable[..., str]] = {}

    def register(self, name: str, handler: Callable[..., str]) -> None:
        self.handlers[name] = handler

    def dispatch(self, call: ToolCall) -> str:
        if call.name not in self.handlers:
            return f"unknown tool: {call.name}"
        return self.handlers[call.name](**call.arguments)


def compose(final_handler: Handler, middlewares: list[Middleware]) -> Handler:
    def wrap(next_handler: Handler, middleware: Middleware) -> Handler:
        return lambda call: middleware(call, next_handler)
    return reduce(wrap, reversed(middlewares), final_handler)


def scoped(scope: Scope) -> Middleware:
    def middleware(call: ToolCall, next_handler: Handler) -> str:
        if call.name not in scope.capabilities:
            return f"scope denied: {call.name}"
        return next_handler(call)
    return middleware


def policy(call: ToolCall, next_handler: Handler) -> str:
    if call.arguments.get("path") == ".env":
        print("POLICY   deny credential file")
        return "blocked: credential file"
    print("POLICY   allow")
    return next_handler(call)


def logging(call: ToolCall, next_handler: Handler) -> str:
    print(f"RUNTIME  -> {call.name}{call.arguments}")
    result = next_handler(call)
    print(f"RUNTIME  <- {result}")
    return result


# ---------- Lifecycle ----------

class Lifecycle:
    def __init__(self) -> None:
        self.cleanups: list[Callable[[], None]] = []

    def add_cleanup(self, cleanup: Callable[[], None]) -> None:
        self.cleanups.append(cleanup)

    def close(self) -> None:
        for cleanup in reversed(self.cleanups):
            cleanup()


# ---------- Stable core and product surface ----------

class AppCore:
    def __init__(self, model: ScriptedModel, runtime: Handler, session: Session,
                 context: ContextAssembler, scope: Scope, lifecycle: Lifecycle) -> None:
        self.model, self.runtime, self.session = model, runtime, session
        self.context, self.scope, self.lifecycle = context, scope, lifecycle

    def run(self, prompt: str) -> str:
        self.session.append("message", role="user", content=prompt)
        system = self.context.build({"workspace": "virtual-demo/", "capabilities": self.scope.capabilities})
        try:
            while True:
                response = self.model.complete(system, self.session.model_view())
                if isinstance(response, FinalAnswer):
                    self.session.append("message", role="assistant", content=response.text)
                    return response.text

                self.session.append("tool_call", name=response.name, arguments=response.arguments)
                result = self.runtime(response)
                self.session.append("tool_result", tool=response.name, output=result)
        finally:
            self.lifecycle.close()


class CLIAdapter:
    def __init__(self, app: AppCore) -> None:
        self.app = app

    def handle(self, line: str) -> None:
        print(f"\nANSWER   {self.app.run(line)}")


def build_app() -> tuple[AppCore, Session]:
    files = {"README.md": "Mini Harness", "app.py": "print('hi')", ".env": "SECRET"}
    registry = ToolRegistry()
    registry.register("list_files", lambda: ", ".join(files))
    registry.register("read_file", lambda path: files.get(path, "not found"))

    scope = Scope(frozenset({"list_files", "read_file"}))
    runtime = compose(registry.dispatch, [logging, scoped(scope), policy])
    session = Session("demo", MemoryEventStore())
    lifecycle = Lifecycle()
    lifecycle.add_cleanup(lambda: print("CLEANUP  model adapter closed"))
    lifecycle.add_cleanup(lambda: print("CLEANUP  session flushed"))
    app = AppCore(ScriptedModel(), runtime, session, ContextAssembler(), scope, lifecycle)
    return app, session


if __name__ == "__main__":
    app, session = build_app()
    CLIAdapter(app).handle("读取项目说明，但不要泄露凭据")
    print("\nAUDIT    完整事件仍在：")
    for event in session.audit_view():
        print("         ", event)
