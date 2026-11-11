# 2026-11-12：引用跳转与代码排版

## 范围与根因

基于 `bb494cb`，工作分支 `codex/citations-code`。修改正式 `skills/recto/`，没有修改已安装插件副本。

AutoTD 报告的共同源将 `[S1]` 至 `[S10]` 写为普通文字；原 6 页 PDF 仅有 1 个 GitHub 外链，没有文内引用链接。用标准 Markdown 链接与 Span 锚点即可通过现有 Pandoc 链路生成 PDF 跳转与 DOCX 书签；生成流程现在明确要求建立这层关系，不自动猜测普通编号的目标。

修改前，用含中文行内代码与代码块的样例从公开入口导出，出现 `Unknown CJK family \CJKttdefault` 并失败。原模板没有代码中文字体与长行策略；Word 的代码段还会继承国标正文两端对齐，表格后处理会覆盖代码字体。

## 实现与取舍

- 复用 Pandoc 的语义链接、代码与高亮；`fvextra` 负责长行折行和安全的行内转义，`framed` 提供可跨页浅底。基础环境已使用 `fancyvrb`，增加两个宏包用于已复现的换行／跨页需要；无需 shell escape、代码执行或外部高亮服务。
- 随包增加原版 Liberation Mono 2.1.5，保留 OFL 许可、作者说明与新增哈希；中文代码使用已有 Fandol 仿宋。PDF 从相对字体路径读取；Word 仍需编辑端可用字体。
- 两格式使用同一小型配色主题。未沿用 Pandoc 黑白主题的下划线 token，因为它会使 JSON 引号在 PDF 中变形；回归核对导出文本中的直引号。
- Word 使用原生代码文字与左对齐代码段。Pandoc DOCX 写出器忽略代码行号，因此只在 Word 的显示副本中加原始行号；共同源不添加行号。
- 独立审查复现了字体文件变化可绕过旧报告复验的问题。模板指纹现在包含实际随包字体与许可文件字节；新增 DOCX-only 回归，不依赖交付目录是否有字体副本。
- 这些取舍可局部替换，无新增持久化状态、独立服务或不可逆迁移；未新增 ADR。

## 验证

本机 macOS，Python 3.12、Pandoc 3.9.0.2、LuaHBTeX 1.24.0 / TeX Live 2026、latexmk 4.89。缺失宏包安装在忽略的测试目录，LaTeX 格式在同目录重建以匹配已有宏包；未修改系统安装。

- `python3 scripts/skills.py check recto`、`python3 scripts/plugin.py check`、`git diff --check` 通过。
- `checks/recto` 16 项、`checks/plugin` 1 项、`checks/release` 6 项通过，未跳过。字体指纹修复后另运行 `test_template.py` 三项回归。
- 新增公开入口回归覆盖两套样式、中文与特殊字符、JSON 直引号、制表符、70 行跨页代码、长 URL、原始起始行号、PDF 文本与引用目标、DOCX 字体／书签／左对齐以及共同源保真。
- `python3 scripts/skills.py package recto` 通过；实际 `recto-skill.zip` 解压到干净消费者目录，使用包内技术样例导出 TeX、PDF、DOCX，并通过 `--verify-report`。包内包含代码主题、4 个 Mono 字体文件和许可证。
- `technical.md`：两套样式的 PDF 共 5 页逐页检查；捆绑 LibreOfficeDev 配合显式字体配置渲染 Word，共 5 页逐页检查。系统 LibreOffice 包装命令退出 134，改用捆绑二进制完成；没有把失败渲染算作通过。
- 压力样例另含长行与连续跨页代码；检查末行保留、缩进、行号、中文和视觉折行。PDF 复制可能含视觉换行，Word 的可选行号是显示文字；精确复用代码以共同 Markdown 为准。
- 人工走读新增 G 场景：生成建立引用、转换保留语义、不猜无来源目标、不将代码改成普通文本、不执行代码。

## 原报告复验

从原报告共同源生成修订副本，保留分析内容与来源边界；补齐 57 处正文引用、10 个证据锚点，恢复已有结构示例与命令的代码排版。仍为 6 页，逐页检查通过。57 个 PDF 链接的标签与文末相应条目坐标逐一匹配，保留原有 1 个 GitHub 外链，没有为本地源码伪造网络地址。

检查 Markdown、TeX、图源、PDF 正文／元数据及解压对象，未发现本机绝对路径标记。从交付目录重编译，6 页渲染逐页匹配；完整性报告通过。本次仅验证排版与链接，未重新进行遥测联网实验或服务端调查。

## 未验证

未用原生 Microsoft Word、WPS、Windows 或手机 PDF 阅读器验收，也未替换本地安装版本。字体替代与 PDF 文本选择行为仍以实际阅读器为准。合并、发布状态以 PR 与 Release 为准。

## PR CI 的跨版本分页复验

[PR #10 的首轮 CI](https://github.com/UserUnauthorized/Recto/actions/runs/43062200806) 在两套样式的跨页代码回归中报告约 3–4pt 的纵向溢出。仅将本机 fvextra 换成上游 1.5 就能复现相同诊断；Ubuntu 24.04 / LuaHBTeX 1.17 环境也复现。

`framed` 分割代码块时允许末行保留字深，随后又将它重新装入零字深盒子，可能超出分页时预留的高度。正式模板在 `Shaded` 环境内设置 `splitmaxdepth=0pt`，使分割时就计入末行字深；没有放宽溢出诊断或改短测试代码。

修复后，本机 fvextra 1.14 的公开导出入口回归通过，两套样式同时覆盖 PDF 与 Word。另从正式入口生成 TeX，在隔离的 Ubuntu 24.04 环境编译两套压力样例：共 9 页逐页检查，70 行代码全部保留，无字体、引用或溢出警告。Linux 环境与诊断副本均在忽略的 QA 输出中，未加入发行包。
