#!/usr/bin/env python3
"""s04: 通过 Middleware 组合日志、计时和 Policy。"""

from dataclasses import dataclass
from functools import reduce
from time import perf_counter
from typing import Callable


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


Handler = Callable[[ToolCall], str]
Middleware = Callable[[ToolCall, Handler], str]


def compose(final_handler: Handler, middlewares: list[Middleware]) -> Handler:
    def wrap(next_handler: Handler, middleware: Middleware) -> Handler:
        return lambda call: middleware(call, next_handler)
    return reduce(wrap, reversed(middlewares), final_handler)


def logging_middleware(call: ToolCall, next_handler: Handler) -> str:
    print(f"LOG      before {call.name}")
    result = next_handler(call)
    print(f"LOG      after  {call.name}: {result}")
    return result


def timing_middleware(call: ToolCall, next_handler: Handler) -> str:
    started = perf_counter()
    result = next_handler(call)
    print(f"TIMER    {(perf_counter() - started) * 1000:.3f} ms")
    return result


def policy_middleware(call: ToolCall, next_handler: Handler) -> str:
    if call.arguments.get("path") == ".env":
        print("POLICY   deny：凭据文件不可读取（执行链在这里短路）")
        return "blocked: credential file"
    print("POLICY   allow")
    return next_handler(call)


def build_runtime() -> Handler:
    files = {"README.md": "hello", ".env": "SECRET"}

    def dispatch(call: ToolCall) -> str:
        print("HANDLER  真正执行工具")
        return files.get(call.arguments["path"], "not found")

    return compose(dispatch, [logging_middleware, timing_middleware, policy_middleware])


if __name__ == "__main__":
    runtime = build_runtime()
    for path in ["README.md", ".env"]:
        print(f"\nMODEL    请求 read_file({path})")
        print(f"RESULT   {runtime(ToolCall('read_file', {'path': path}))}")
