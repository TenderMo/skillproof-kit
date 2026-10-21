# SkillProof Kit

**面向 Codex、Claude Code 等 AI 编程助手的 Skills 质量检查与发布工具。**

[English](README.md) · [命令说明](docs/usage.md) · [规则说明](docs/rules.md) · [架构图](docs/architecture.md)

SkillProof Kit 帮助 Skills 作者在分享前发现元数据错误、丢失资源、未完成占位符等问题，并生成目录文档、资源关系图和发布 ZIP。

## 安装与运行

需要 Python 3.11 或更新版本。在项目源码目录运行：

```sh
python -m pip install .
skillproof check examples/skills --strict
skillproof docs examples/skills --output reports/catalog.md
skillproof diagram examples/skills --output reports/skills.mmd
skillproof pack examples/skills/write-project-docs --output dist/write-project-docs.zip
```

示例检查的预期输出：

```text
2 skill(s), 0 error(s), 0 warning(s)
```

当前支持从源码安装；尚未发布到 PyPI。

## 能解决什么问题

| 场景 | 工具作用 | 产出 |
| --- | --- | --- |
| 自己写一个 Skill | 检查名称、描述、正文和资源链接 | 可定位到文件、行号的报告 |
| 团队维护多个 Skills | 扫描集合，发现重名并生成目录 | Markdown 目录 |
| 给项目接入 CI | 用退出码阻止带错误的变更 | Text、JSON 或 Markdown 检查结果 |
| 分享写文档、画图等 Skills | 验证后打包完整资源 | ZIP 发布包 |
| 解释 Skill 的文件结构 | 自动列出 Skill 与附带资源的关系 | 可编辑 Mermaid 图 |

## 写文档、画图有什么用

**写文档 Skill**：用于 README、安装说明、入门教程、CLI 和 API 使用指南。让助手先查实现、再写示例，并说明哪些命令已经验证。适合把“代码能用”变成“别人看文档就能用”。

**画图 Skill**：用于架构图、业务流程图、时序图和依赖图。帮助读者理解组件怎样协作、数据怎样流动、一次请求经过哪些步骤。Mermaid 源码便于在 GitHub 预览、审阅和修改。

项目包含这两种 Skill 的完整示例：

- [write-project-docs](examples/skills/write-project-docs/SKILL.md)
- [draw-system-diagrams](examples/skills/draw-system-diagrams/SKILL.md)

SkillProof 的 `docs` 命令生成元数据目录，`diagram` 命令生成包内资源关系图。撰写自然语言教程、分析任意代码库并绘制架构图，由编程助手调用相应 Skill 完成。

## 五个命令

```sh
skillproof init write-api-docs --template docs --dir skills
skillproof check skills --strict
skillproof docs skills --output reports/catalog.md
skillproof diagram skills --output reports/resources.mmd
skillproof pack skills/write-api-docs --output dist/write-api-docs.zip
```

退出码：`0` 通过；`1` 存在错误，或严格模式下存在警告；`2` 命令、路径或文件操作失败。

## 兼容范围

工具检查 `SKILL.md` 的共享结构及部分元数据约束，保留 Codex、Claude Code 等宿主的扩展字段。它提供静态质量信号；实际触发效果和任务完成质量需要在目标助手里验证。完整范围见[规则说明](docs/rules.md)。

## 开发与参与

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

欢迎提供失败示例、改进规则、完善中文文档。项目采用 [MIT 许可证](LICENSE)，维护方式见[维护指南](docs/maintaining.md)。
