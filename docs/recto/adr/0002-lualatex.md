# 迁移 LuaLaTeX

日期：2026-11-10

状态：已接受

Recto 的默认固定版面链路从 Typst 迁移到 LuaLaTeX，交付共同 Markdown、`latex/document.tex` 与 PDF。用户在本地对照后决定迁移：即使当前两套样张没有明显视觉优势，LuaLaTeX 能直接使用既有中文排版宏包、TeX 字体机制和更成熟的印刷生态，也让源文件符合明确要求 LaTeX 引擎的任务。保留 Pandoc 到 DOCX 的独立 OMML 路径；Word 不经 TeX 生成，也不要求 Typst。

生产 PDF 使用 `latexmk` 驱动 LuaLaTeX，并传给引擎 `--no-shell-escape --nosocket`。实际探针确认 `--safer` 会让 luaotfload 退到 OT1 后在字体载入处失败，因此不使用、也不建议把它叠加到该链路。这不是放宽源码权限：共同 Markdown 仍是语义化受限源，raw HTML/TeX 被拒绝，宏不在当前数学包支持集内时直接失败，不自动安装或静默展开。编译离线执行，缺少 TeX 时进入依赖安装流程，不以其他引擎兜底编译。

首个本地探针在 macOS TeX Live 2026 Basic、LuaHBTeX 1.24 下完成，`latexmk -latexoption` 得到确认。后续正式实现的本地验收见 [迁移记录](../validation/2026-11-10-lualatex-migration.md)。已知对齐、数学字体和方块字符缺陷由 [Issue #4](https://github.com/UserUnauthorized/Recto/issues/4) 跟踪，本次迁移不宣称修复。

`-norc` 禁止自动 RC，仅显式载入 Recto 随源交付的 `latex/latexmkrc`。并行验证复现了 LuaTeX-ja 的 `extra_*` 缓存不断互相覆盖，造成 latexmk 达到最大轮次而失败。构建规则通过 latexmk 的 `after_xlatex_analysis` hook 排除这些派生缓存，继续跟踪真实字体、正文、图片与辅助引用文件，不扩大忽略范围到所有 Lua 文件。

交付源内嵌版式与选定字体，`latex/fonts/` 只带必要的开源字体和许可证；系统原字体优先，缺失时用随包开源字体替代，替代关系写入导出报告。LuaLaTeX 通过文件路径直接读取随包字体；Word 编辑端仍需安装同一字体。Markdown 与 LaTeX 共用根目录 `media/`。输入 SVG 时导出器在离线步骤显式调用 `rsvg-convert` 生成同名 `.svg.pdf` TeX 资源，并保留原 SVG；PNG/JPEG/PDF 输入不需要该工具。缺 `rsvg-convert` 时给出安装 librsvg 或改供 PNG/PDF 的处理建议。

历史 DOCX 样张曾在 Word for Mac 16.114.4 实测；这不等于新 LuaLaTeX 交付链路已完成同一轮 Word 验收。旧 Typst 历史与归档不回写，只由 ADR 0001 的状态指向本决策。
