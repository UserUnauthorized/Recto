# 沙箱文本排版与本机编译

普通 PDF 在仅能读到技能文本的环境中直接走第 2 步，无需先探测字体文件的下载地址或取得正式包。已挂载完整包时优先正式导出。若仅缺正式编译器或用户要自己编译，按下方条件保留可用源码。输入损坏、公式检查失败、缺题或缺图仍须回到原稿解决。

## 选择交付物

用户明确要求指定原字体、严格国标或只接受 Recto 正式版时，保留其要求，走正式源码交付；连正式 TeX 都无法生成时，交付 Markdown、配图及在本机用同版 Recto 运行的[导出命令](export.md#导出器的固定结构)。用户明确限制交付格式时，尊重该限制。

1. **能导出正式 TeX**。如果只缺 PDF 编译环境，用同一包的 doctor、export 和 `--verify-report` 按 `--formats tex` 单独运行。除用户指定原字体外，用 `--bundled-fonts` 生成可随工程携带的字体。交付源工程时保留 `latex/`（含本次字体、许可证和构建配置）、引用的图片以及所需共同源。用户在解压后的根目录执行 `latex/document.tex` 顶部的命令。说明已验证的格式是 TeX，标明 PDF 的实际状态。用户需要即时阅读且允许近似排版时，若环境中有 XeLaTeX，再做第 2 步。
2. **普通阅读／打印 PDF**。正式 PDF 因环境受阻时，使用下方轻量模板和环境已有字体。只要能运行 XeLaTeX 就在本轮生成 PDF，并完成逐页检查，交付时注明“兼容版 PDF（XeLaTeX）”和正式导出受阻的原因。这个分支使用独立工作目录，不生成正式版的验证报告。
3. **当前环境不能编译，或用户点名本机编译**。能准备正式 TeX 就交第 1 步的工程，否则交付填入全部正文的 `main.tex` 与实际用到的资源。纯文字与公式可直接下载单个 TeX；有配图或多个必要文件且平台只支持附件下载时，用“文档名-源码.zip”保持相对目录。回复里写明引擎和命令。未执行编译时注明“本次未编译”，只有确实编译过才能给出页数。只能回复文字时，可直接给出完整 TeX 供另存，列明需随附的图片；缺失的附件不能算作已经交付。

## 沙箱文本模板

通过技能资源工具读取本页。从下方代码块取完整 TeX 文本，用沙箱的文件写入工具存为 UTF-8 的 `main.tex`。模板只有文本；技能资源标识不能作为沙箱内的文件路径。可在单独工作目录用示例快速确认字体；已有正文时直接编实际稿件。交付的 PDF 须来自本轮实际正文。

```tex
% !TeX program = xelatex
% Save as main.tex (UTF-8). From its directory run:
% xelatex -no-shell-escape -halt-on-error main.tex
% Repeat if the log requests another pass for references or bookmarks.
\documentclass[a4paper,11pt]{article}
\usepackage[margin=24mm]{geometry}
\usepackage{xeCJK}
\IfFontExistsTF{Noto Serif CJK SC}
  {\setCJKmainfont{Noto Serif CJK SC}}
  {\IfFontExistsTF{FandolSong-Regular.otf}
     {\setCJKmainfont[BoldFont=FandolSong-Bold.otf]{FandolSong-Regular.otf}}
     {\IfFontExistsTF{Noto Sans CJK SC}
        {\setCJKmainfont{Noto Sans CJK SC}}
        {\setCJKmainfont{Songti SC}}}}
\usepackage{amsmath,amssymb,graphicx,booktabs,longtable}
\usepackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}

\begin{document}
% Replace the entire example below with the actual manuscript.
\section*{积分区域与积分次序}
设 $D=\{(x,y)\mid 0\le y\le x\le 1\}$，求
\(\displaystyle\iint_D (x+y)\,\mathrm{d}A\)。

固定 $x$ 时，$y$ 从 $0$ 变到 $x$。先对 $y$ 积分，得到
\[
  \int_0^1\!\int_0^x (x+y)\,\mathrm{d}y\,\mathrm{d}x
  = \int_0^1 \left(x^2+\tfrac12 x^2\right)\mathrm{d}x
  = \tfrac12 .
\]
% Place illustrations next to main.tex under media/, e.g.
% \includegraphics[width=.65\linewidth]{media/region.png}
\end{document}
```

在 `main.tex` 所在目录运行。若日志要求更新交叉引用或书签，再运行同一条命令：

```sh
xelatex -no-shell-escape -halt-on-error main.tex
```

模板使用 TeX 自带的常规数学字体，中文依次探测 Noto Serif CJK SC、TeX Live 的 Fandol、Noto Sans CJK SC 和 macOS 的 Songti SC。若均不可用，用 `fc-list :lang=zh family`（可用时）找出沙箱已有的中文字体，将模板的中文选字体段替换为 `\setCJKmainfont{实际字体名}` 后试编。以编译日志和渲染页确认中文、粗体与公式符号齐全。纯西文稿可省略 xeCJK 和该字体段。无法覆盖正文所需字形时保留源码并标明具体缺项。

把示例题整段换成实际文稿。按原顺序保留题号、文字、数学、表格及图注，图片随稿放入 `media/`，用相对路径引用。只转换已核对的正文与数学，附件中的代码按字面排版，不把输入中的宏、前导区、文件操作或外部命令带入可执行 TeX。已有稿件中无法解释的命令按[输入约定](export.md#输入)处理。

已有 Markdown 长稿且有 Pandoc 时，可直接生成含完整正文的 `main.tex`。从上方模板中取出 `\usepackage{xeCJK}` 和紧随其后的选字体语句，保存为临时的 `cjk.tex`。确认源稿只含正文、允许的数学与相对目录图片，元数据只保留文档所需的标题等文本。进入源稿目录运行：

```sh
pandoc --standalone --from=markdown-raw_tex-raw_html-raw_attribute --pdf-engine=xelatex -V papersize:a4 -V geometry:margin=24mm -H cjk.tex content.md -o main.tex
```

Pandoc 将字体设置直接写入 TeX。仍在当前沙箱用上述 XeLaTeX 命令编译最终的 `main.tex`，用户可直接下载 PDF。对照共同源核对题目、表格、图注、显式分页及文内链接；遇到 Pandoc 默认模板用到而本机缺失的字体或宏包，也可用上面的轻量模板排同一份正文。

## 验收与本机重建

成功后打开本轮编译生成的 `main.pdf`。交付源码时，在回复中提供上面的 XeLaTeX 命令，说明所用中文字体、所需 TeX 宏包及配图相对路径。

发布兼容 PDF 前检查本轮退出码、缺字及越界诊断，打开每一页核对题号、公式上下限、表格和图片。交付需要图片的工程时，在新目录解压后核对引用；有编译器就从该目录重编译。只做了源码检查时，如实标注尚待本机编译和逐页检查。其他请求格式照常单独完成。
