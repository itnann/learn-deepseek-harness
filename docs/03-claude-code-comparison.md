# 03. 与 Claude Code 教学实现的差异

## 比较边界

本章比较两份可检查的源码：

- DeepSeek 官方开源的 `deepseek-harness`。
- shareAI-lab 的 `learn-claude-code` 教学复刻。

后者明确为了教学简化机制，并不是 Anthropic 官方发布的 Claude Code 完整源码。因此下文写“Claude 教学实现”时，指该仓库；除非有公开证据，不据此断言 Claude Code 产品内部一定采用相同代码结构。

## 总表

| 维度 | Claude 教学实现 | DeepSeek Harness | 本质差异 |
|---|---|---|---|
| 教学/产品定位 | 20 章渐进式 Python 复刻 | TypeScript 生产框架，开发者预览 | 最小机制 vs 完整生命周期 |
| 顶层结构 | 一个不断增强的 agent loop | profile 组合出的 Cordis 插件树 | loop 是中心 vs loop 是可替换插件 |
| 状态真源 | 内存 `messages[]`，部分章节另做持久化 | append-only SessionEvent log | 当前状态 vs 可重放事实流 |
| 工具注册 | `TOOL_HANDLERS`/dispatch map | scope-aware ToolRuntime service | 函数表 vs 带生命周期的注册表 |
| 工具执行 | loop 内调用 handler | pre/around/post waterfall + scheduler | 直接分发 vs 策略化管线 |
| Prompt | 字符串逐章增强 | section registry + ordered assembly | 构造值 vs 运行时贡献 |
| Hooks | hook 配置和回调机制 | typed events；兼容 Claude/Codex hook 的 bridge | hooks 是扩展层 vs 外部协议是适配层 |
| 权限 | 规则判断后 allow/ask/deny | sandbox、approval、fs/shell policy 分离 | 决策逻辑 vs 能力限制 + 人机审批 |
| 子 agent | 递归/独立上下文教学实现 | provider seam，支持多种进程内外后端 | 单一实现 vs 可替换执行后端 |
| 上下文压缩 | 对 `messages` 做分层压缩 | compaction capability + session surface replacement | 修改历史视图 vs 日志中记录投影替换 |
| 多前端 | CLI/教学 Web | Web、headless、ACP、JSON-RPC SDK | 单表面教学 vs 共享核心、多表面产品 |
| 自修改 | 非主线 | 插件检查、挂载和卸载能力 | 改代码/配置 vs 操作运行时组合 |

## 1. Agent Loop：同一个思想，不同的责任范围

[`learn-claude-code/s01`](https://github.com/shareAI-lab/learn-claude-code/blob/7b564c3ee6996039cb4e13a53024dfe2d4388d35/s01_agent_loop/code.py) 用最小循环表达核心：模型返回 tool use，harness 执行，再把结果送回模型。

DeepSeek 的 `ReactLoopAgent` 仍然是这个 ReAct 模式，但它还负责：

- next-turn / next-step Inbox。
- turn 与 step 的 durable bracket。
- 流式 chunk 记录与消息组装。
- 请求 header 和模型路由变化记录。
- 工具并发、有序提交与取消配对。
- steer、inject、followup 的边界语义。

所以“DeepSeek 的 loop 更复杂”是事实，但不能简单归结为过度设计；其中多数复杂度在承担 resume、replay、UI、并发和取消等生产责任。

## 2. 新增工具：handler 还是 capability family

Claude 教学实现的格言是“加一个工具，只加一个 handler”。这对理解模型工具调用非常好。

DeepSeek Harness 中，一个简单纯函数工具也可以接近这种体验；但涉及外部环境的能力通常按三角色拆分。例如 shell 的定义、provider 和 tool consumer 可以分别演进。这样做的收益是：

- 本地 shell 换成远程 sandbox 时，模型工具 schema 可以不变。
- 多个 consumer 可以复用同一个 provider。
- permission、timeout、telemetry 通过事件包装，不侵入 handler。
- 每个 agent scope 可以拥有不同工具集合。

代价也明确：包数量、类型和配置行显著增加，初学者需要先掌握依赖方向。

## 3. Hook：数组回调 vs 统一拦截面

Claude 教学实现的 s04 把 hook 插在 loop 的工具前后，直观展示“不改主循环也能扩展”。

DeepSeek Harness 把同一原则推广成类型化事件：

```text
agent/pre-step
agent/request
agent/request-error
agent/turn-stopping
tools/pre-execute
tools/execute
tools/post-execute
```

`packages/hooks` 不是 Harness 原生插件机制本身，而是把 Claude Code/Codex 的外部 shell-hook 协议翻译到这些事件上。这一点很关键：内部扩展面稳定，外部协议只是 adapter。

## 4. 权限：问不问用户只是其中一层

Claude 教学实现主要展示规则匹配与 allow/ask/deny。DeepSeek 把行动安全拆成多个正交问题：

- Sandbox：进程实际被限制在什么范围。
- Approval：某个行动是否需要用户确认。
- Filesystem policy：路径访问是否合法。
- Shell/subprocess provider：命令在哪里、以何种进程树运行。
- Tool pre-execute：在 dispatch 前做统一判定。

这避免把“用户点了允许”误当成“操作一定安全”。审批是意图授权，sandbox 是技术约束，二者不能互相替代。

## 5. Session Log：最值得重点学习的差异

`messages[]` 很适合教学，但它把几个概念混在一起：原始事件、当前模型上下文、UI 展示、持久化格式。

DeepSeek Harness 分开处理：

```text
SessionEvent log（完整事实）
    -> ordered surface（模型可见消息节点）
        -> deriveMessages（本次请求历史）

SessionEvent log
    -> UI projection / replay / telemetry / persistence / query
```

compaction 不是删除旧 event，而是在 surface 上追加 replace 操作并引用被替换节点。这样既缩短模型上下文，又保留审计和回放所需的原始历史。

如果只选一个 DeepSeek 特性深入研究，优先选 session log，而不是 Web UI。

## 6. Subagent：任务函数 vs provider seam

Claude 教学实现强调“干净上下文”和把结果带回父 agent。DeepSeek 保留这两个目标，但把“怎样运行 child”抽象成 provider：

- fresh in-process child。
- 从父历史 fork 的 child。
- ACP out-of-process child。
- 真实 Codex app-server child。
- 通过 Claude Agent SDK 运行的 Claude Code child。
- 通过 DSH SDK 运行的外部 Harness child。

这意味着 DeepSeek Harness 不只实现一种多 agent 拓扑，它也可以成为其他 agent 产品的统一宿主。这是它和单产品 harness 最明显的战略差异之一。

## 7. System Prompt：拼字符串 vs 注册 section

Claude 教学实现最终也会把 prompt 分段组装。DeepSeek 把这个模式做成 service：插件注册具名 section、顺序和文本；ToolRuntime 同时贡献 model-facing schemas。

结果是：

- skill、plan mode、surface persona 等可以独立贡献提示词。
- agent scope 可以选择不同 section。
- 插件卸载时 section 自动消失。
- 最终渲染文本与 tool schemas 一起进入 `request/header`，可以重建。

这里的关键并不是“字符串模板更高级”，而是 prompt 也被纳入插件生命周期和 session 可重建性。

## 8. DeepSeek Harness 的代价和风险

对比不能只写优点。当前架构的成本包括：

- 学习门槛高：Cordis、Loader patch、service injection、scope、event waterfall 必须一起理解。
- 间接性强：实际行为可能分布在 TypeScript、YAML patch 和多个插件中。
- 调试路径长：问题可能来自 provider、consumer、policy、scope 或装配层。
- 仍在开发者预览：源码明确不承诺兼容，包名、格式和边界可能快速变化。
- “一切皆插件”容易产生很多小包；必须依靠文档、生成图和约束检查控制复杂度。

因此，它不是“所有 agent 项目都应该照抄”的模板。单用途、小规模 agent 可能更适合教学项目那样的直接结构；当需求进入多 surface、多 provider、可恢复会话和严格权限时，DeepSeek 的抽象才开始明显回本。

## 9. 后续验证清单

下一轮源码阅读应通过可运行实验验证以下判断：

1. dump `headless` 与 `web` 的最终 config，比较实际插件树。
2. 跑一个 keyless snapshot/replay fixture，观察 session JSONL。
3. 写一个最小 tool plugin，确认 register/dispose 生命周期。
4. 在 `tools/pre-execute` 增加临时 policy，确认无需改 agent loop。
5. 对同一 session 做 resume/fork，比较 seed boundary 和 derived messages。
6. 切换 subagent provider，验证 model-facing tool 是否保持稳定。

这些实验完成后，比较会从静态架构判断升级为运行时证据。
