# 共用源文件与导出

导出器使用 Pandoc ≥3.9、LuaLaTeX 与 `latexmk`；建议 TeX Live 2024 或更新版本。Python 需要 `python-docx` 和 `lxml`；优先使用工作区依赖加载器返回的运行时。缺项时先走[依赖检查与安装](setup.md)。导出离线执行；渲染 DOCX 优先使用捆绑的 LibreOffice。

## 输入

YAML 标题可选。原文没有标题且要求原样转换时省略 `title`，不自动生成封面或文档标题。

```markdown
---
title: "局部近似与误差控制"
subtitle: "Local Approximation and Error Control"
---

# 1.1 线性模型

这是正文，包含行内公式 $f'(a)$。

$$f(a+h)=f(a)+f'(a)h+o(h).\qquad\text{(1.1)}$$

**定理 1.1 可微性**

保留原文的条件与结论。参见式（1.1）。
```

- 标题与编号是内容的一部分：按原文显式写入，文内引用同样写清。当前脚本不自动编号公式或解析 `@eq:...`，修改编号时一起核对引用。
- 公式用受限 LaTeX 数学语法，如 `\frac`、`\int`、`aligned`、`pmatrix`。导出前逐个校验所有数学节点（包括标题中的公式），只允许数学符号、排版命令和数学环境；不展开自定义宏。遇到未知命令、非数学环境、TeX 字符编码或异常控制字符时停止，应等价转换并核对原式，不能自动安装宏包或丢弃公式。该校验也适用于仅交付源码，避免把可读取文件或执行 Lua 的命令带进后续编译；关闭 shell escape 本身不能隔离 TeX 文件访问。
- 支持段落、四级标题、粗体、列表、脚注、链接与文内锚点、行内代码、代码块、常规表格、图像与图注。合并单元格、复杂多栏、自动题目索引等需要额外实现和验证，不暗示通用支持。
- 图片使用相对本地路径。LuaLaTeX 可直接使用 PNG、JPEG 和 PDF。输入 SVG 时，导出器只在离线预处理中调用 `rsvg-convert` 生成共享 `media/` 下的同名 `.svg.pdf`，并保留原 SVG 给 Markdown 使用；PNG/JPEG/PDF 输入不需要 `rsvg-convert`。缺少该命令时，按提示安装 librsvg或改供 PNG/PDF。
- 不使用 raw HTML/TeX 片段混入共用源；脚本拒绝任意 raw 标记，防止某格式静默丢内容。

显式分页：

```markdown
::: pagebreak
:::
```

国标附件：

```markdown
::: {.appendix label="附件1" title="资料登记表"}
正文和 Markdown 表格。
:::

::: {.appendix .landscape label="附件2" title="资料对照表"}
较宽表格。
:::

::: {.appendix .landscape label="" title="资料对照表（续）"}
续表。
:::
```

原文为“附录 A”时原样写 `label="附录 A"`。附件应置于文末，不能嵌套；横向表格按一页容纳量明确分段，核对表头与行是否齐全。PDF 横表在纵向纸张内按奇偶页旋转；Word 为横向节，页码持续，不是同一版面几何。

SVG 必须自包含：引用旁边文件或外部样式时，先将资源嵌入 SVG；导出器会拒绝这些引用，避免搬移后静默丢图。

## 引用和代码

文内引用使用 Markdown 链接与显式锚点，可放在段落或证据索引表中：

```markdown
结论见 [\[S1\]](#source-s1)。

[S1]{#source-s1} 包内 `src/module.py`，第 354–368 行。
可核实的公开版本：[来源说明](https://example.com/source)。
```

源稿里的普通 `[S1]` 是文本，不会自动推断来源。PDF 与 Word 保留链接和目标；生成模式应主动建立这层关系，转换模式保留已有关系。外链应指向核对过的页面或固定版本；没有公开来源时仅保留文内跳转与材料内相对定位，不写本机绝对路径。

行内代码用反引号，如 `installation_id`。多行代码使用围栏；语言名称沿用 Pandoc 支持的名称（如 `python`、`json`、`bash`），未指定或未知语言按纯文本排版。源码摘录可使用以下属性：

````markdown
```{.python .numberLines startFrom="354"}
def snapshot(users):
    return {"users": users}
```
````

默认不编号；`numberLines` 开启显示行号，`startFrom` 指定原始起始行号。代码用 Liberation Mono 与 Fandol 仿宋，浅灰底、深色、低饱和的语法高亮；无需联网高亮服务或执行代码。PDF 长行按版心换行，长块可跨页；Word 保持原生可编辑文字。视觉折行和显示行号不改共同源；PDF 复制可能包含视觉换行或行号，Word 的可选行号也是显示文字，需精确复用时以 Markdown 代码为准。技术样例见 `assets/examples/technical.md`。

## 输出

```sh
"$RECTO_PYTHON" "$RECTO_ROOT/scripts/export.py" content.md \
  --style gbt9704 --formats tex,pdf,docx --output result \
  > /absolute/qa/export-attempt-1.json
```

`RECTO_ROOT` 是当前 Recto `SKILL.md` 所在目录。保存本次 stdout、检查退出码，再按 [导出与验证流程](../SKILL.md#4-导出) 使用同一来源、样式、格式、字体选项及输出目录追加 `--verify-report /absolute/qa/export-attempt-1.json` 复验；失败后仍走正式入口。

默认交付 Markdown、LaTeX 和 PDF：

```text
result/
  content.md
  document.pdf
  media/                 # 仅有图片时存在；Markdown 与 LaTeX 共用
  latex/
    document.tex
    latexmkrc            # 随源交付的构建规则
    fonts/               # 仅本次选用的开源字体族与许可证
```

`latex/document.tex` 内嵌版式与选定字体设置；`content.md` 是整理资源路径后的唯一交付正文源。要求 Word 时在 `--formats` 中加入 `docx`，根目录增加 `document.docx`。只要 PDF、TeX 或 Word 时分别用 `pdf`、`tex`、`docx`。旧 `typ` 格式被拒绝；收到该请求时提示迁移到 `tex`。Word 路径独立使用 Pandoc 生成 OMML，不需要 TeX 或 `latexmk`。

从交付根目录重建 PDF：

```sh
latexmk -norc -r latex/latexmkrc -lualatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build -latexoption=--no-shell-escape -latexoption=--nosocket latex/document.tex
```

`latexmk` 会创建并复用 `build/`，负责所需的多次编译；不要手写固定两遍。`-norc` 禁止自动读取环境中的构建配置，`-r` 只载入随源交付的规则，避免并行任务改写 LuaTeX-ja 字体缓存而不断重跑；字体文件本身仍参与依赖检查。导出器内部编译有 480 秒总超时。移动整个交付目录后仍可重建。系统专有字体不复制，重建机器仍需具备这些字体；使用随包字体时源文件通过 `latex/fonts/` 的相对路径直接读取，无需专用字体环境变量。Word 编辑端也须安装实际使用的字体。

标准输出中的 JSON 报告记录源哈希、导出器与模板指纹、请求选项、成品及资源哈希、引擎版本、配置字体、替代关系和数学数量。模板检查先核对生成的 TeX 包含正式样式和字体设置；`--verify-report` 再只读核对记录与当前文件，不需要 Pandoc 或 TeX，不在交付目录新增文件。报告默认不交付，不能鉴别伪造记录或替代视觉 QA。`word_visual_qa: pending` 表示导出器未执行视觉检查；`native_word_math_count` 仅证明 OMML 数量匹配。

`fonts.word_math` 是最终 DOCX 的 `settings.xml` 中配置的数学字体；`font_substitutions` 是导出时的字体选择，不是 Word／LibreOffice 实际使用字体的测量结果。`word_font_note` 说明编辑端可用性：随包字体不会嵌入 DOCX，未在系统字体中检测到时须在目标编辑器安装，实际回退需从渲染结果核对。多行对齐使用无边框的原生 OMML 分列，空列和显式空白保留；`\square` 使用普通空心方框 U+25A1。共同 Markdown 与 LaTeX 源不改写。

输出到独立的成品目录；若输入目录中已有同一正文的 Markdown，交付时仅保留需要的那一份并核对图片路径。导出器不推断既有目录中哪些文件可以删除；技能在验收后清理已确认的旧导出与中间文件，不能批量删掉未知用户文件。

渲染 DOCX 可调用：

```sh
"$RECTO_PYTHON" scripts/render_word.py result/document.docx --renderer /absolute/path/to/documents/render_docx.py --output /absolute/work/qa-word
```

随后打开每一张 `page-N.png` 检查。多行推导对齐和相邻上标仍应重点核对。

## 经验与限制

Word 的原生公式使用 OMML；字体由 Word 的数学排版支持决定。公式宏不受支持时脚本停止。固定行高可能剪切分式，讲义采用最小行高。表格不使用固定行高，并重复表头。Word 页面重排应在交付前渲染核验。

官方依据：[Pandoc 用户手册](https://pandoc.org/MANUAL.html)中 DOCX 的 OMML 数学输出、reference-doc 与 custom-style；项目示例补充了实际转换与渲染验证。
