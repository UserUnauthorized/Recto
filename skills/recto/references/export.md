# 共用源文件与导出

脚本经 Pandoc 3.9.0.2、Typst 0.15.1 验证。Python 需要 python-docx 和 lxml；优先使用工作区依赖加载器返回的运行时。缺项时先走 [依赖检查与安装](setup.md)。渲染 DOCX 优先使用捆绑的 LibreOffice；没有桌面运行时的环境按安装流程准备渲染工具。导出不触网。

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
- 公式用 LaTeX 数学语法。优先 `\frac`、`\int`、`aligned`、`pmatrix` 等 Pandoc 可转换的写法；不支持的宏会报错，应等价转换并核对原式，不能丢弃。
- 支持段落、四级标题、粗体、列表、脚注、常规表格、图像与图注。合并单元格、复杂多栏、自动题目索引等需要额外实现和验证，不暗示通用支持。
- 图片使用相对本地路径。跨格式首选足够清晰的 PNG；不要把数学公式作为图片。PDF 专用图可使用 SVG；DOCX 若对 SVG 有警告须先生成图像兼容版本。
- 不使用 raw HTML/TeX/Typst 片段混入共用源；脚本拒绝它们，以防某格式静默丢内容。

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

## 输出

```sh
"$RECTO_PYTHON" scripts/export.py content.md --style gbt9704 --formats typ,pdf,docx --output result
```

默认交付 Markdown、Typst 和 PDF，目录如下：

```text
result/
  content.md
  document.pdf
  media/                 # 仅有图片时存在；Markdown 与 Typst 共用
  typst/
    document.typ
    fonts/               # 仅本次选用的开源字体族与许可证
```

`typst/document.typ` 已内嵌样式与本次字体选择；`content.md` 是整理资源路径后的唯一交付正文源。默认不生成 ZIP、`REBUILD.txt`、报告文件或预览目录。要求 Word 时在 `--formats` 中加入 `docx`，根目录增加 `document.docx`。用户明确只要 PDF 时可用 `--formats pdf`，只要 Word 时用 `--formats docx`；它们不保留编译中间稿或字体副本，仍保留 Markdown 与必要图片。

在交付根目录运行 `.typ` 顶部注释中的命令，通常为 `typst compile --root . --font-path typst/fonts typst/document.typ document.pdf`。`--root .` 允许 Typst 读取同级 `media/`；移动整个目录后仍可编译。系统专有字体不复制，重编译机器仍需具备这些字体；希望全用开源字体时，在检查、导出和重编译命令前设置 `TYPST_IGNORE_SYSTEM_FONTS=true` 与 `TYPST_IGNORE_EMBEDDED_FONTS=true`，并移除自定义 `TYPST_FONT_PATHS`。Word 编辑端也须有实际使用的字体。

标准输出中的 JSON 报告记录源哈希、引擎版本、配置字体、替代关系和数学数量，不在交付目录写入 `export-report.json`。需要留存日志或 QA 记录时放到外部工作目录，完成验收后按任务要求清理。`word_visual_qa: pending` 表示导出器未执行视觉检查；`native_word_math_count` 仅证明 OMML 数量匹配，不能替代符号或渲染核对。DOCX 的数学字体设置供编辑器读取，LibreOffice 可能使用自身的数学字体替代，不保证与 Typst 一致。

输出到独立的成品目录；若输入目录中已有同一正文的 Markdown，交付时仅保留需要的那一份并核对图片路径。导出器不推断既有目录中哪些文件可以删除；技能在验收后清理已确认的旧导出与中间文件，不能批量删掉未知用户文件。

渲染检查可调用：

```sh
"$RECTO_PYTHON" scripts/render_word.py result/document.docx --renderer /absolute/path/to/documents/render_docx.py --output /absolute/work/qa-word
```

在 macOS 上该包装脚本让渲染器显式读取系统、用户和随包字体目录，避免临时 HOME 导致汉字消失或变成方框。随后打开每一张 `page-N.png` 检查。数学对齐标记与上标相邻符号分别经过 OMML 和 Typst 输出修正，仍应重点核对多行推导。

## 经验与限制

直接使用 Pandoc 的 Typst reader 转本项目旧样张，会出现计数器、交叉引用、图注信息丢失，因此生产流程使用共同 Markdown 分别生成。导出的 Typst 仍可手动精调；若有多格式需求，内容编辑回到 Markdown。

Word 的原生公式使用 OMML；字体由 Word 的数学排版支持决定。公式宏不受支持时脚本停止。固定行高可能剪切分式，讲义采用最小行高。表格不使用固定行高，并重复表头。Word 页面重排应在交付前渲染核验。

官方依据：[Pandoc 用户手册](https://pandoc.org/MANUAL.html) 中 DOCX 的 OMML 数学输出、reference-doc 与 custom-style；项目示例补充了实际转换与渲染验证。
