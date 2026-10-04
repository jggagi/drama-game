# drama-game

剧情向独立游戏与故事沙盘仓库。不同作品在各自的子目录中保存和迭代，逐步打磨故事、视觉与可玩片段。

## 当前项目

### [《雷雨：门外》（暂定名）](thunderstorm/README.md)

以《雷雨》为蓝本、以四凤为主视角的探索式叙事独立游戏。当前剧情与视觉文档均为讨论初稿，尚未定案。

- [剧情与游戏设计初稿](thunderstorm/docs/story-design.md)
- [视觉设计初稿](thunderstorm/docs/visual-design.md)
- [美术需求清单与概念图 Brief](thunderstorm/docs/art-production-brief.md)
- [Qwen Next 配音试听交接](thunderstorm/review/qwen-next-handoff/README.md)

## 目录

```text
drama-game/
├── README.md
└── thunderstorm/
    ├── README.md
    ├── docs/
    │   ├── story-design.md
    │   ├── visual-design.md
    │   └── art-production-brief.md
    └── review/
        └── qwen-next-handoff/
```

## 子项目边界

《雷雨：门外》的项目根目录为 `thunderstorm/`。其 README 与设计文档中提到的 `docs/`、`art/` 等项目相对路径，以该子目录为基准；后续原型代码、素材与运行说明也应放在该项目范围内，避免占用仓库根目录。

给 Codex 或其他协作者的旧指令，如仍引用仓库根目录下的 `docs/*.md`，请改为 `thunderstorm/docs/*.md`；也可以先进入 `thunderstorm/`，再按原有项目相对路径读取。

本次调整仅迁移现有项目 README 与三份设计文档，并更新仓库入口，不修改剧情、视觉提案或美术需求。历史版本由 Git 保留。
