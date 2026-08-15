# 00. 阅读地图

DeepSeek Harness 的仓库很大，第一遍不应该逐目录阅读。最有效的路线是先追踪一条真实请求，再沿扩展点向外展开。

## 基础薄弱也不用先补完整 TypeScript

第一遍只需要先记住四件事：

1. `interface` 和 `type` 主要描述数据长什么样，先顺着字段名读，不必一开始掌握所有泛型。
2. `async` 函数返回 Promise，`await` 表示这里可能暂停等结果；Agent Loop 的大部分时序都靠它表达。
3. 一个 `packages/<group>/<name>` 通常是一个独立 npm package，跨 package 通过 `@deepseek-ai/dsh-*` 名称导入。
4. `ctx.tools`、`ctx.sessions` 不是神秘语法，而是插件通过 Cordis Context 取得的 service。

遇到 `Scoped<T>`、declaration merging、branded id 或复杂条件类型时，先看它们保护的运行时关系，不要卡在语法上。等主调用链走通后，再回头看类型为何能提前阻止错误。

## 三遍阅读法

| 轮次 | 只回答什么 | 推荐材料 |
|---|---|---|
| 第一遍：建立地图 | 请求从哪里进、从哪里出？ | 本文、[架构总览](01-architecture-overview.md)、[请求生命周期](02-request-lifecycle.md) |
| 第二遍：理解关键数据 | 历史和工具结果怎样保持可重放？ | [Session Log](05-session-log.md)、[工具运行时](06-tool-runtime.md) |
| 第三遍：比较设计 | 哪些是 DSH 源码事实，哪些只是 Claude 教学类比？ | [比较](03-claude-code-comparison.md)、[证据边界](04-evidence-boundary.md) |

不要第一遍就从 `package.json` 开始数全部 workspace，也不要按文件名顺序阅读 `packages/`。先用下面的一条主线建立位置感。

## 一条主线，五层代码

| 层 | 先读文件 | 要回答的问题 |
|---|---|---|
| 1. 命令入口 | [`apps/cli/src/bin.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/apps/cli/src/bin.ts) | `dsh web` / `dsh --profile headless` 如何选运行模式？ |
| 2. 组合启动 | [`apps/cli/src/profile-boot.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/apps/cli/src/profile-boot.ts)、[`packages/bundle/base/cordis.patch.yml`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/bundle/base/cordis.patch.yml) | 这次运行到底装载了哪些插件？ |
| 3. Agent 主干 | [`packages/core/agent-loop/src/agent.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/core/agent-loop/src/agent.ts) | turn、step、LLM 请求和工具调用如何衔接？ |
| 4. 状态与能力 | [`packages/core/session/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/core/session/src/index.ts)、[`packages/core/tools/src/index.ts`](https://github.com/deepseek-ai/deepseek-harness/blob/47f943859bef60e4160492346772ded9b24f765a/packages/core/tools/src/index.ts) | 历史怎样持久化？工具怎样注册、审批和执行？ |
| 5. 外围能力 | `packages/fs`、`shell`、`skill`、`compaction`、`subagent` | 核心不修改时，新行为怎样接入？ |

## 第一遍可以跳过什么

以下内容很重要，但不适合作为入口：

- `apps/web` 和 `packages/client`：规模大，先理解 session event 后再看 UI 投影。
- `vendor/`：Cordis 的 vendored 源码；第一遍先读 `docs/cordis-primer.md`，遇到生命周期疑问再下钻。
- `packages/typert`：远程类型图和 RPC 基础设施，属于产品表面而非 agent loop 主干。
- `native/`：平台沙箱实现，先理解 `sandbox` service seam。
- 大量 tests：先用 README 和实现建立模型，再用测试确认边界条件。

## 推荐的源码阅读动作

### 1. 先看最终组合，不要猜

DeepSeek Harness 的运行时不是由某个 `main.ts` 硬编码出来的。`dsh-base` 先插入共享插件，`web-app` 或 `headless` 再覆盖/增加行，用户 profile、Harness home 和 `--patch` 继续叠加。

源码运行环境准备好后，可用：

```bash
dsh --profile web --dump-config
dsh --profile headless --dump-config
```

这比单独阅读某个 bundle 更接近实际运行状态。

### 2. 看到 capability 时按三种角色找

Harness 把可替换能力拆成：

1. Service Definition：声明接口和 `ctx` key。
2. Service Provider：提供本地、远程或第三方实现。
3. Consumer：通常是给模型使用的 tool，也可能是 UI 或另一个 service。

例如 shell：

```text
dsh-shell（定义）
    <- dsh-shell-local / pwsh provider（实现）
    <- dsh-tool-bash / dsh-tool-pwsh（模型入口）
```

只读 `tool-bash` 会误以为工具自己管理进程；只读 provider 又看不到模型如何调用它。

### 3. 区分三类事件

| 事件域 | 是否持久化 | 用途 |
|---|---:|---|
| Session events | 是 | turn、step、消息、tool call/result、request header 等事实 |
| Agent events | 否 | 拦截正在发生的 pre-step、request、错误和停止过程 |
| Capability events | 通常否 | 权限、工具执行、文件系统策略等能力内部扩展点 |

最重要的判断规则是：**模型可见的信息必须能从 session log 重建。**

## 与 learn-claude-code 的阅读顺序对应

| learn-claude-code | DeepSeek Harness 对应入口 | 阅读提醒 |
|---|---|---|
| s01 Agent Loop | `core/agent-loop` | DSH 中 loop 本身也是插件，不是最高层入口 |
| s02 Tool Use | `core/tools` + 各 capability family | 注册、策略和执行器分层 |
| s03 Permission | `interaction` + `sandbox` + `fs`/`shell` policy | 审批与隔离不是一个布尔判断 |
| s04 Hooks | typed `agent/*`、`tools/*` events + `packages/hooks` bridge | 原生扩展是插件；hooks 包主要做外部协议兼容 |
| s06 Subagent | `packages/subagent` | provider 可替换，支持 in-process、ACP、Codex、Claude Code |
| s07 Skill | `packages/skill` | catalog/provider/tool 三层 |
| s08 Compaction | `packages/compaction` + session surface replacement | 压缩结果也是可重放的日志事实 |
| s10 System Prompt | `core/system-prompt` | section 注册并按顺序组装，工具 schema 同步参与 |
| s12 Task System | `goal`、`todo`、`plan`、`workflow` | DSH 没把所有“任务”压成一种数据结构 |

## 第一轮完成标准

读完第一轮后，应能不看文档回答：

- `dsh --profile headless "task"` 从哪里进入？
- base bundle、mode bundle、用户 patch 的覆盖顺序是什么？
- turn 和 step 有什么区别？
- 为什么工具结果不是简单地 `messages.append(result)`？
- 哪些事实进入 session log，哪些只存在于实时 event？
- 新增一个 shell provider 时，为什么通常不需要修改 agent loop？
