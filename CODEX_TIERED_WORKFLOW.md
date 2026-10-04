# Codex Cloud 分层工作流

本仓库携带 `.agents/skills/tiered-coding/` 技能、`.codex/agents/luna-worker.toml` 角色配置和根目录 `AGENTS.md` 默认指令。基于包含这些文件的版本创建新 Cloud chat，让实质性工程任务采用这套流程；这不改变用户选择的根模型或推理强度，也不影响其他仓库。

本机个人技能不会自动同步到 Cloud；仓库技能在 Cloud 任务中可用。项目级自定义代理采用 `.codex/agents/` 下的 TOML 文件。技能文件可发现、角色配置可解析，并不单独证明云端已执行 `gpt-6-luna / xhigh`。参考官方 [Cloud 环境说明](https://learn.chatgpt.com/docs/environments/cloud-environments#current-limitations)、[技能加载位置](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)及[自定义代理](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents)。

若云端环境固定了旧版本或尚未包含这些文件，先更新它使用的仓库版本；修改环境初始化流程时，重新发布环境，并用新 chat 验证。已有 chat 保留其自己的工作状态，不能假设自动获得新的配置。

## 一次真实云端验收

在该仓库的新 Cloud chat 中发送以下任务。先确认根代理是用户选择的 Sol；若真实 `luna_worker` 或目标模型/推理强度不可用，报告限制，不自动替换。

```text
使用 $tiered-coding，在新建临时目录中完成一次真实工作流验收。
保持当前 Sol/root 的模型和推理强度，不修改系统安全策略或全局配置。
先检查 Python 与真实 luna_worker；缺失时报告，不安装或替换角色。
root 给出完整 Task Packet，然后将有界任务委派给恰好一个真实 luna_worker，
使用独立上下文，不覆盖角色模型/推理强度，不递归委派。

实现 unique_in_order(items)：接受可哈希元素的可迭代对象，使用 set 和结果列表，
按首次出现顺序去重，不修改输入，并保留首次出现的对象。
Worker 仅在临时目录内编写实现与测试，覆盖空输入、重复值、顺序、生成器、
输入不变、哈希碰撞、首次对象身份和单次遍历，运行测试并返回规定结果契约。
root 独立审查源码与测试，重新运行测试并补充必要检查。

最终报告目录与文件、测试命令/结果、独立复查结论、实际子代理身份，
以及根与子代理的模型/推理强度运行元数据。
不以配置文件或代理自述代替实际执行证据；证据不可获取的部分明确标为未验证。
记录沙箱错误原文，不将临时验收文件提交到作品目录。
```

此验收用于验证代理工作流，不代表作品已经通过试玩、视觉或发布验收。
