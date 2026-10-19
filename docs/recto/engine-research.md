# 排版引擎调研

核对日期：2026-10-19。状态：Typst 路线已确认；课程讲义风格已选定，新增国标正文样式。

## 用户已确认

- 面向讲义、教材，电子版阅读或自行打印。
- 使用方式与 Kami 一样，由 skill 接收内容并负责排版。
- 首版统一 Typst，交付 PDF 和可重新编译的源文件。
- 默认忠实排版；不自行修订数学论证。
- 经过样张比较，用户选定「清爽课程讲义」，另外三个探索方向已删除。
- 用户反馈初版文字过密，随后提供物理和化学两份课程 PDF，要求合并参考其版式。新增「清爽课程讲义」：宋体 / Times、12pt 正文、18pt 基础行距、A4 窄页边距、黑白细线分节。参数与取舍记录在 [课程讲义原型记录](../../archive/recto/book-styles/reference-style.md)。
- 用户已选定「清爽课程讲义」，进一步要求上下页边距稍增、底部加页码；模板调整为上下各 12mm、底部居中阿拉伯数字页码。
- 新增 GB/T 9704-2012 正文、表格和附件样式，不含红头与署名。以用户提供的标准全文为依据，本机已有小标宋、仿宋、黑体、楷体和宋体，继续使用 Typst 实现；不改变既定引擎路线。

## 选型判断

| 路线 | 可核查的能力与取舍 | 本项目定位 |
| --- | --- | --- |
| Typst | 原生数学、多行对齐、公式编号与引用；中西文自动间距、按字符覆盖选择字体；内外页边距和页眉页脚 | 已选首版引擎 |
| XeLaTeX / LuaLaTeX + CTeX | CTeX 提供中文文档类与 CJK 支持，适合已有 TeX 源稿和特定出版模板 | 后续按实际兼容需求评估 |
| HTML/CSS + WeasyPrint | Kami 的主要 PDF 路线；官方支持分页与矢量 SVG，但本次文档查询没有建立原生 MathML 能力证据 | 可以借鉴工作流，不作为本次数学书籍样张引擎 |

以上“本项目定位”是针对当前用途的工程判断，不是所有出版项目的引擎排名。

## 值得从 Kami 继承的流程

明确内容与交付合约 → 选择样式 → 检查字体和资料 → 套用模板 → 编译 → 结构检查与逐页视觉检查 → 交付源文件与成品。书籍的视觉规则须重新设计，不沿用暖纸色、营销文档密度要求或“一页纸”布局。

## 正式实现必须处理的边界

- Typst 数学语法不等于 LaTeX 语法。接收带 TeX 公式的 Markdown 时，需要逐式转换和核对；不能声称任意宏包无损迁移。
- 长公式须按语义选择断行点。块公式默认不跨页，可单独配置 breakable；这不等于自动解决横向溢出。
- 中文字体、拉丁正文字体和数学字体应配套验证。缺字、字体回退、标点位置与行内公式基线都不能只靠“编译成功”验收。
- 双面页边距、标题与正文黏连、孤行、定理跨页、图表题与引用均需样张验证。
- 固定编译器与字体版本后再建立视觉基准；目前不承诺商业印刷生产线合规，也不需要为当前用途引入此范围。

## 本机核查

当前目录起初为空且不是 Git 仓库，因此本轮样张放在独立原型目录（现归档于 `archive/recto/book-styles/`），无现有主分支或生产代码需要隔离。

- 初次检查 `typst --version` 为 0.14.2；用户随后授权更新，已通过 Homebrew 更新并回读为 0.15.1。
- XeLaTeX、LuaLaTeX：TeX Live 2026；本机能找到 ctexbook.cls 与 unicode-math.sty。
- 已发现 Source Han Serif SC、Noto Serif CJK SC、STIX Two Text / Math、New Computer Modern / Math 等字体。
- 官方已发布 0.15.1；0.15.0 涉及混排间距和数学排版变更。此次原型统一使用更新后的 0.15.1。

## 一手资料

- [Typst 字体、覆盖范围与中西文间距](https://typst.app/docs/reference/text/text/)
- [Typst 数学排版](https://typst.app/docs/reference/math/)
- [公式编号、引用与跨页行为](https://typst.app/docs/reference/math/equation/)
- [书籍页面、装订方向与内外边距](https://typst.app/docs/reference/layout/page/)
- [Typst 0.15.0 变更](https://typst.app/docs/changelog/0.15.0/)
- [Typst 0.15.1 变更](https://typst.app/docs/changelog/0.15.1/)
- [CTeX 维护者文档](https://github.com/ctex-org/ctex-kit/blob/master/README-en.md)
- [WeasyPrint API 与支持特性](https://doc.courtbouillon.org/weasyprint/stable/api_reference.html)

研究先使用 Context7，补充查询使用 Exa；Exa 报告配额限制后，改用内置浏览访问上述官方来源。尚未根据这些能力描述承诺成品已经达到出版质量，最终以样张为准。
