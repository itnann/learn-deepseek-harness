#!/usr/bin/env python3
"""s07: 相同 EventStore 契约下替换内存和远端 Provider。"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Event:
    kind: str
    text: str


class EventStore(Protocol):
    def append(self, session_id: str, event: Event) -> None: ...
    def load(self, session_id: str) -> list[Event]: ...


class MemoryEventStore:
    def __init__(self) -> None:
        self.data: dict[str, list[Event]] = defaultdict(list)

    def append(self, session_id: str, event: Event) -> None:
        self.data[session_id].append(event)

    def load(self, session_id: str) -> list[Event]:
        return list(self.data[session_id])


class FakeRemoteEventStore:
    def __init__(self) -> None:
        self.server: dict[str, list[Event]] = defaultdict(list)

    def append(self, session_id: str, event: Event) -> None:
        print(f"REMOTE   POST /sessions/{session_id}/events")
        self.server[session_id].append(event)

    def load(self, session_id: str) -> list[Event]:
        print(f"REMOTE   GET  /sessions/{session_id}/events")
        return list(self.server[session_id])


class SessionCore:
    def __init__(self, store: EventStore, session_id: str) -> None:
        self.store, self.session_id = store, session_id

    def say(self, role: str, text: str) -> None:
        self.store.append(self.session_id, Event(role, text))

    def history(self) -> list[Event]:
        return self.store.load(self.session_id)


def run_demo(name: str, store: EventStore) -> None:
    session = SessionCore(store, "demo-1")
    session.say("user", "你好")
    session.say("assistant", "你好，我能帮什么？")
    print(f"{name:8} {session.history()}")


if __name__ == "__main__":
    run_demo("memory", MemoryEventStore())
    run_demo("remote", FakeRemoteEventStore())
