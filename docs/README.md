# 源码证据与延伸资料

本目录不是主学习路线。请先从可运行课程 [`../course/s01_one_loop/`](../course/s01_one_loop/) 开始；完成主线后，可用 [`../lessons/00-learning-map.md`](../lessons/00-learning-map.md) 做设计复盘。

这里保留实现层资料，用于验证课程中的判断或在需要时继续深入：

- `00-reading-map.md`：源码目录与入口地图。
- `01-architecture-overview.md`：Cordis、Profile、Bundle 和核心组件。
- `02-request-lifecycle.md`：一次请求的实现路径。
- `03-claude-code-comparison.md`：实现层差异记录。
- `04-evidence-boundary.md`：三份仓库的证据范围。
- `05-session-log.md`：Session 与模型消息面实现。
- `06-tool-runtime.md`：Tool Runtime 与并发调度实现。

使用原则：

1. 先从课程理解“为什么需要这个设计”。
2. 只有想验证边界或准备实现类似机制时，再查这里的源码位置。
3. 不要求按文件顺序通读 DeepSeek Harness。
