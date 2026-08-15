#!/usr/bin/env python3
"""s10: CLI 与 Web Adapter 共享同一个 AppCore 和组合根。"""


class AppCore:
    def __init__(self, list_files) -> None:
        self.list_files = list_files
        self.execution_log: list[str] = []

    def run(self, prompt: str) -> str:
        self.execution_log.append(f"prompt={prompt}")
        result = self.list_files()
        self.execution_log.append("tool=list_files")
        return f"项目文件：{result}"


def build_app() -> AppCore:
    virtual_files = ["README.md", "app.py"]
    return AppCore(list_files=lambda: ", ".join(virtual_files))


class CLIAdapter:
    def __init__(self, app: AppCore) -> None:
        self.app = app

    def handle(self, line: str) -> None:
        print(f"CLI      {self.app.run(line)}")


class WebAdapter:
    def __init__(self, app: AppCore) -> None:
        self.app = app

    def post(self, body: dict) -> dict:
        return {"status": 200, "data": {"answer": self.app.run(body["prompt"])}}


if __name__ == "__main__":
    app = build_app()
    CLIAdapter(app).handle("列出文件")
    print("WEB     ", WebAdapter(app).post({"prompt": "列出文件"}))
    print("CORE LOG", app.execution_log)
