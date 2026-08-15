#!/usr/bin/env python3
"""s08: 取消传播、等待后台任务、逆序 cleanup。"""

import asyncio
from collections.abc import Awaitable, Callable


Cleanup = Callable[[], Awaitable[None]]


class Lifecycle:
    def __init__(self) -> None:
        self.cancelled = asyncio.Event()
        self.cleanups: list[Cleanup] = []
        self.tasks: set[asyncio.Task] = set()

    def add_cleanup(self, cleanup: Cleanup) -> None:
        self.cleanups.append(cleanup)

    def spawn(self, coro: Awaitable[None]) -> None:
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def close(self) -> None:
        self.cancelled.set()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        for cleanup in reversed(self.cleanups):
            await cleanup()


async def background_tool(name: str, lifecycle: Lifecycle) -> None:
    print(f"TOOL     {name} started")
    await lifecycle.cancelled.wait()
    print(f"TOOL     {name} observed cancellation")


async def close_resource(name: str) -> None:
    print(f"CLEANUP  close {name}")


async def main() -> None:
    lifecycle = Lifecycle()
    lifecycle.add_cleanup(lambda: close_resource("provider"))
    lifecycle.add_cleanup(lambda: close_resource("stream"))
    lifecycle.spawn(background_tool("search", lifecycle))
    lifecycle.spawn(background_tool("index", lifecycle))
    await asyncio.sleep(0)
    print("USER     cancel")
    await lifecycle.close()
    print(f"HARNESS  pending tasks: {len(lifecycle.tasks)}")


if __name__ == "__main__":
    asyncio.run(main())
