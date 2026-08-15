#!/usr/bin/env python3
"""s06: 按来源、条件与预算组装上下文。"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ContextBlock:
    source: str
    priority: int
    text: str


Contributor = Callable[[dict], ContextBlock | None]


class ContextAssembler:
    def __init__(self, contributors: list[Contributor]) -> None:
        self.contributors = contributors

    def build(self, state: dict, budget: int) -> list[ContextBlock]:
        candidates = [block for make in self.contributors if (block := make(state))]
        selected, used = [], 0
        for block in sorted(candidates, key=lambda item: item.priority, reverse=True):
            if used + len(block.text) <= budget:
                selected.append(block)
                used += len(block.text)
        return selected


def identity(_state: dict) -> ContextBlock:
    return ContextBlock("identity", 100, "你是编码助手；事实不足时先观察。")


def safety(_state: dict) -> ContextBlock:
    return ContextBlock("safety", 95, "只在工作区行动；破坏性操作必须审批。")


def workspace(state: dict) -> ContextBlock:
    return ContextBlock("workspace", 80, f"当前工作区：{state['workspace']}。")


def git_status(state: dict) -> ContextBlock | None:
    if not state["needs_git"]:
        return None
    return ContextBlock("git", 60, "当前分支 main，有 2 个未提交文件。")


def skill_catalog(_state: dict) -> ContextBlock:
    return ContextBlock("skills", 20, "可按需加载：Python 测试、文档写作、发布流程。")


if __name__ == "__main__":
    assembler = ContextAssembler([identity, safety, workspace, git_status, skill_catalog])
    blocks = assembler.build({"workspace": "demo/", "needs_git": True}, budget=120)
    print("ASSEMBLED CONTEXT")
    for block in blocks:
        print(f"[{block.source:9}] priority={block.priority}: {block.text}")
    print("\n最终文本：\n" + "\n".join(block.text for block in blocks))
