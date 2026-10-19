# 共用源文件与导出

脚本经 Pandoc 3.9.0.2、Typst 0.15.1 验证。Python 需要 python-docx 和 lxml；使用工作区依赖加载器返回的运行时。渲染 DOCX 时使用该运行时的 LibreOffice，不回退到系统桌面版。导出不触网。

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

`document.typ` 已内嵌样式；有图片时连同 `assets/` 保存。`document.pdf` 是 Typst 编译结果；`document.docx` 含可编辑内容。`content.md` 是资源路径整理后的共同源，`source-and-exports.zip` 包含这些文件。可运行 `typst compile document.typ` 重编译。

`export-report.json` 记录源哈希和数学数量。`word_visual_qa: pending` 表示导出器未执行视觉检查；渲染与检查完成后另存 QA 记录，不把这项自动改成已通过。`native_word_math_count` 仅证明 OMML 数量匹配，不能替代符号或渲染核对。

渲染检查可调用：

```sh
"$RECTO_PYTHON" scripts/render_word.py result/document.docx --renderer /absolute/path/to/documents/render_docx.py --output result/qa-word
```

在 macOS 上该包装脚本让渲染器显式读取系统与用户字体目录，避免临时 HOME 导致汉字消失或变成方框；不复制或分发字体。随后打开每一张 `page-N.png` 检查。数学对齐标记与上标相邻符号分别经过 OMML 和 Typst 输出修正，仍应重点核对多行推导。

## 经验与限制

直接使用 Pandoc 的 Typst reader 转本项目旧样张，会出现计数器、交叉引用、图注信息丢失，因此生产流程使用共同 Markdown 分别生成。导出的 Typst 仍可手动精调；若有多格式需求，内容编辑回到 Markdown。

Word 的原生公式使用 OMML；字体由 Word 的数学排版支持决定。公式宏不受支持时脚本停止。固定行高可能剪切分式，讲义采用最小行高。表格不使用固定行高，并重复表头。Word 页面重排应在交付前渲染核验。

官方依据：[Pandoc 用户手册](https://pandoc.org/MANUAL.html) 中 DOCX 的 OMML 数学输出、reference-doc 与 custom-style；项目示例补充了实际转换与渲染验证。
