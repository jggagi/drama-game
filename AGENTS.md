# AGENTS.md — drama-game

本文件规定仓库根级代理工作流。先读根目录 [README.md](README.md)和目标作品的文档；各作品的代码、素材、测试与运行说明保持在各自子目录内。处理《雷雨：门外》时以 `thunderstorm/` 为项目根。作品状态以实际文件和用户最新要求为准，不把讨论稿当作已经定案的方案，也不因分层委派扩展任务范围。

## 分层代理工作流

对实质性工程任务，默认使用仓库技能 [$tiered-coding](.agents/skills/tiered-coding/SKILL.md)。简单修改、创意讨论和只读总结按任务需要处理，不为使用技能而强行委派。

保持用户选择的根代理模型与推理强度。Sol/root 负责意图、架构、任务分解、Worker 分配、集成、审查、重新规划与最终验证；只有已经决定实现方式、边界明确且值得委派的工作，才交给真实 `luna_worker`。该角色由 [.codex/agents/luna-worker.toml](.codex/agents/luna-worker.toml) 定义为 `gpt-6-luna / xhigh`，不依靠提示词模拟角色或切换模型。

委派前给出完整 Task Packet：Goal、Scope、Constraints、Acceptance criteria、Validation、Escalate if。优先使用独立上下文（接口支持时设 `fork_turns=none`），明确文件所有权，避免重叠编辑；Worker 不递归委派，除非 root 明确要求。

Worker 按技能返回 `DONE`、`BLOCKED` 或 `NEEDS_SOL` 及规定结果契约。root 检查实际修改与验收条件，独立运行最终验证；同一实施任务最多一次由 root 纠正后的重试，不反复尝试未解决的问题。

若当前根代理不是 Sol、真实角色不可用或目标模型/推理强度不受支持，明确报告限制，不自动更换根模型、模拟 Luna 或替换角色。区分“配置已部署”与“真实运行已验证”；实际执行模型和推理强度只能按运行元数据报告，无法取得时标为未验证。云端使用与验收见 [CODEX_TIERED_WORKFLOW.md](CODEX_TIERED_WORKFLOW.md)。
