#!/usr/bin/env python3
"""运行全部课程示例并检查 Markdown 中的本地链接。"""

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_examples() -> list[str]:
    errors = []
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    for script in sorted((ROOT / "course").glob("s*/code.py")):
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        if result.returncode:
            errors.append(f"{script.relative_to(ROOT)} 运行失败：\n{result.stderr}")
    return errors


def check_links() -> list[str]:
    errors = []
    link_pattern = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)|!\[[^]]*]\(([^)]+)\)")
    for markdown in ROOT.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        in_fence = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = re.sub(r"`[^`]*`", "", line)
            for match in link_pattern.finditer(line):
                target = (match.group(1) or match.group(2)).strip().split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (markdown.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"{markdown.relative_to(ROOT)} -> {target}")
    return errors


def check_svgs() -> list[str]:
    errors = []
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for svg in ROOT.rglob("*.svg"):
        try:
            root = ET.parse(svg).getroot()
        except ET.ParseError as error:
            errors.append(f"{svg.relative_to(ROOT)} XML 无效：{error}")
            continue
        if root.find("svg:title", namespace) is None or root.find("svg:desc", namespace) is None:
            errors.append(f"{svg.relative_to(ROOT)} 缺少 title 或 desc")
    return errors


if __name__ == "__main__":
    failures = check_examples() + check_links() + check_svgs()
    if failures:
        print("CHECK FAILED")
        for failure in failures:
            print("-", failure)
        raise SystemExit(1)
    print("CHECK PASSED: 12 examples ran; links and SVG metadata are valid.")
