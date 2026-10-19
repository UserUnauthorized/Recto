# 随包字体

以下字体以原始文件分发，未改字形、名称或子集化；许可证与版权信息随文件保留。`SHA256SUMS.json` 固定字体及上游许可文件的字节。字体授权分别适用，不改变用户正文的授权。

| 目录 | 字体 | 来源与许可 |
|---|---|---|
| `fandol/` | Fandol 宋体、黑体（常规／粗体）、楷体、仿宋 | [CTAN Fandol 0.3](https://ctan.org/pkg/fandol)，[完整原包](https://mirrors.ctan.org/fonts/fandol.zip)；GPL + font exception，见目录中的 README 与 COPYING |
| `liberation/` | Liberation Serif 常规、粗体、斜体、粗斜体 | [上游 2.1.5 发布](https://github.com/liberationfonts/liberation-fonts/releases/tag/2.1.5)；SIL OFL 1.1，见 LICENSE 与 AUTHORS |
| `newcm/` | New Computer Modern Math 常规／粗体 | 保留最初样张使用的本地原文件；内置版权声明为 Antonis Tsolomitis，GUST Font License。见 GUST-FONT-LICENSE.txt 与 LPPL.txt；[上游完整字体包及源文件](https://ctan.org/pkg/newcomputermodern) |

Fandol 仿宋在 Typst 中的 family 名称为 `FandolFang R`。国标标题缺少方正小标宋时使用 Fandol 宋体粗体，这不是小标宋的等同替代，需复核字形与分页。

不收录 Songti SC、Times New Roman、SimSun、Cambria Math 或方正字库文件。有这些本地字体时优先沿用，缺少时使用本目录字体，选择结果写入导出命令标准输出的 JSON 报告。

Typst 会直接读取本目录；Word 编辑端需安装相应字体。macOS 可用字体册安装，Windows 使用“为当前用户安装”，Linux 放到用户字体目录后刷新字体缓存。文档的 `typst/fonts/` 仅保留本次选用的开源字体族及其许可证，不复制整套字体库；插件与 skill 安装包仍包含完整字体库以供其他文档使用。
