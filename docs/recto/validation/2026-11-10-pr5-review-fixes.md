# PR #5 审查问题修复验收

日期：2026-11-10。修复基线：`178380994a7bc93225d577acdf6b1e3052f61c06`。本轮处理两项 skill 文档问题与一项数学输入边界回归，Word Issue #4 继续单独跟踪。验证材料在本地忽略目录 `output/recto/pr5-fixes/`，不随 Git 提交。

## 修复与回归

1. **数学输入边界**：关闭 Pandoc 的 `latex_macros` 预展开，在公共导出入口校验所有 Math 节点，包括 YAML 标题。只允许数学符号、排版命令及显式数学环境；文件读取、Lua、命令构造、自定义宏、非数学环境和 `^^` 编码在交付 TeX 源或编译 PDF 前被拒绝。异常控制字符也被拒绝，避免交付不可编译的源码；正常空白、换行和制表符保留。`\text` 内仍检查命令，真正的 TeX 注释可保留，转义百分号不会隐藏后续命令。不把此检查称为任意 TeX 程序的沙箱。
2. **按格式验收**：PDF、DOCX、仅源码分别有完成条件。只有同时交付 PDF 与 LaTeX 源时才从成品位置重编译；Word-only 不再要求 TeX，TeX-only 缺引擎时明确标为未编译源。`checks/recto/scenarios.md` 走读了 PDF-only、TeX-only、Word-only 和完整交付，保留原生 Word 与 LibreOffice 验证的区别。
3. **安装包自包含**：移除版式说明中的仓库 ADR 裸路径，改为包内可理解的已知限制及直接指向 Issue #4 的外部链接。复用现有 Markdown 链接检查与实际包内容核对，没有增加依赖精确文案的测试。

输入边界回归从提交 `1783809` 的 Git 归档运行：10 个用例都因原实现接受了应拒绝的输入而失败，日志为 `red-math-final.log`。修复后同一测试通过，覆盖直接/标题中/转义百分号后的 `\input`、`\directlua`、`\csname`、编码命令、`filecontents*` 环境、宏定义、NUL 和 DEL，并核对既有 PDF、DOCX、Markdown、TeX 文件字节不变。控制字符用例证明了无效源码可被交付，不是已证实的文件读取绕过。

另从原始公开 PDF 复现入口验证真实存在的合成输入文件：现在退出码 1，报 `Unsupported math command: \input`，旧 PDF 保持原字节，记录在 `fixed-input/result.json`。测试未读取用户私有文件。

## 已完成检查

- Recto 整套 11 项测试通过，耗时 324.385 秒，见 `tests.log`。随后补上控制字符校验，重跑输入拒绝、正常公式、无 TeX 环境导出这 3 项相关测试，全部通过，耗时 38.271 秒，见 `tests-final-boundary.log`。新增正常公式用例覆盖 `aligned`、矩阵、希腊字母、分式、根号、极限、命名算子、注释、转义百分号及正常空白，并实际生成 PDF / TeX / 原生 OMML DOCX。
- 扩展已有 PATH 隔离测试：仅保留真实 Pandoc，分别完成 Word-only 和 TeX-only 导出，不生成 PDF、不要求 TeX/Typst；Word 保留 66 个原生数学对象。
- 讲义和国标样例各以原字体、随包字体重新导出；共 18 页 PDF 与先前逐页检查的渲染逐字节一致。中文内容、讲义 66 个数学节点保持一致，两份 DOCX 的全部 12 个 `word/` 部件各自与原基线逐字节相同，见 `artifact-audit.json`。
- 两项 skill 的结构检查/打包、插件检查/打包、插件包测试（1 项）与 `git diff --check` 通过。最终安装包内容与源码逐字节一致；独立解包的 skill 通过公开入口导出 PDF、TeX、DOCX，讲义保留 66 个 OMML，4 页 PDF 与已检查样例渲染一致，见 `package-consumer-report.json`。
- 独立代码复核未发现数学命令校验路径的剩余具体阻塞项；复核提出的异常控制字符问题已纳入最终修复和回归。

## 验证边界

本轮使用既有 macOS、Pandoc 3.9.0.2、LuaHBTeX 1.24.0 / TeX Live 2026 Basic、latexmk 4.89 与捆绑 Python。没有新做 ChatGPT、Windows/WPS 或原生 Word 编辑保存往返验收；skill 流程做了场景走读，没有声称完成模型 A/B 行为实验。数学命令采用有限支持集，未支持的命令会明确报错，不能把包内宏包可用等同于允许任意 TeX 扩展。
