# Document Skills

这个仓库维护文档相关的 Codex skills。每个 `skills/<name>/` 都是可独立安装的单元：入口、操作脚本、模板与运行时参考资料一起交付。仓库目录名沿用 Recto，但后续文档 skill 不必归入 Recto。

| Skill | 用途 | 输出 |
|---|---|---|
| [Recto](skills/recto/SKILL.md) | 中英文数学讲义、教材及国标正文；生成内容时按需配图和去 AI 腔，现有内容转换时忠实保留 | Typst、PDF、可编辑 DOCX |

使用时直接说：`用 $recto 把这份 Markdown 原样导出 PDF 和 Word，采用清爽课程讲义样式。` 内容生成也可以直接提出主题和要求，skill 会据此选择工作流程。

## 目录

```text
skills/<name>/     可安装的 skill；唯一的正式源文件
scripts/skills.py  仓库检查、打包与本地安装入口
checks/<name>/     维护者使用的行为检查场景，不随 skill 安装
docs/<name>/       设计依据、术语、决策与有日期的验证记录
archive/<name>/    已冻结的设计原型，不参与正式打包
output/<name>/     本地导出、渲染与试验产物，忽略版本控制
dist/             可分发安装包，忽略版本控制
```

`assets/examples/` 中的小型输入样例随 skill 保留，方便在安装后直接运行；大体积渲染、转换探针与缓存留在 `output/`。文档技能可能需要 PDF 或 DOCX 模板，因此不按扩展名一概排除资产。

## 维护入口

仓库工具使用 Python 3.10+ 与 `requirements-dev.txt` 中的 PyYAML。字体、Pandoc、Typst、DOCX 运行时由各 skill 自己说明；仓库管理命令不会安装这些依赖。

```sh
python3 -m pip install -r requirements-dev.txt  # 当前 Python 尚无 PyYAML 时
python3 scripts/skills.py list
python3 scripts/skills.py check               # 也可只检查 recto
python3 scripts/skills.py package recto       # dist/recto-skill.zip
python3 scripts/skills.py install recto
```

安装默认使用 `$CODEX_HOME/skills`，未设置时使用 `~/.codex/skills`；用 `--dest /path/to/skills` 可指定其他位置。内容相同则不改动；已有版本不同时默认停止。加 `--replace` 会先把旧版本保存到本仓库 `output/install-backups/`，再整体更新，避免遗留已删除的资源。后续修改始终回到 `skills/`，再重新安装，不把安装副本当作第二份源代码。

`check` 检查元数据、skill 内的相对链接和 Python 语法；它不执行文档转换，也不证明排版或内容正确。改动导出脚本、模板或字体后，要运行真实样例并逐页检查受影响格式。维护流程见 [AGENTS.md](AGENTS.md)，Recto 的行为场景见 [checks/recto/scenarios.md](checks/recto/scenarios.md)。

## Recto 的现有资料

- [引擎决策](docs/recto/adr/0001-typst-first.md)与[版式参数](skills/recto/references/styles.md)。
- [已完成的导出验证](docs/recto/validation/2026-10-19-exports.md)：区分编译、结构检查、LibreOffice 渲染和原生 Word 实测。
- [原型归档](archive/recto/book-styles/README.md)：保留被选中的两套风格、原始样张和验证脚本；正式改动不再写入这里。

本地历史样张现位于 `output/recto/reference/` 和 `output/recto/gbt9704/`。生成物不随源仓库提供；可用 skill 自带的 `assets/examples/` 输入重新导出。字体不随安装包分发。
