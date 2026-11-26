# 2026-11-26 PDF 降级交付

## 触发场景

读取三个指定 Web 会话的用户和助手消息。第 7–10 章自学讲义和模拟题首次均交付 Markdown，追问 PDF 后分别报告使用 XeLaTeX 得到 47 页讲义、30 页详解和 8 页题卷。Paper E 会话交付 Markdown 和两张积分区域图。三者均报告正式资源不可取得。消息未附失败命令的完整日志，本次没有在这些会话中执行命令或复核其中的成品。

走读普通讲义、严格版式、仅缺编译器及源稿缺图的分支。普通讲义直接尝试兼容 PDF，指定正式版时保留正式重建路径。选择源码时随稿提供本次使用的图片。原稿的内容缺项继续在原稿中处理。

## 本地执行

- macOS，XeTeX 0.999998（TeX Live 2026），Pandoc 3.9.0.2，Python 3.12。将轻量模板单独复制为 `main.tex`，在该目录用 XeLaTeX 编译。得到 1 页 A4 PDF，打开渲染页核对中文、积分上下限和分数。实际嵌入字体为 Songti SC。本次没有在 Linux、Windows 或 Web 编译该模板。
- 用带图片、脚注、表格、矩阵和多行推导的 `reference.md` 走兼容流程，以 Pandoc 生成独立 TeX。把 `main.tex` 和一张相对路径图片打成 ZIP，解压到含中文和空格的新目录，在此仅运行 XeLaTeX。检查了全部 3 页 A4 渲染，核对了图、图注、表格、脚注和公式。末轮日志没有缺字、越界或未解析引用。兼容版保留 Pandoc 默认的图表标签和分页。
- 用包内 doctor 和 export 对同一原稿按 `--style reference --formats tex --bundled-fonts` 执行正式源码导出，随后传入本轮报告复验。`template_verified` 为 true，输出格式为 tex。检查了工程内的构建命令、相对图片、字体和许可证。此项验证限于 TeX。
- 两个 skill 均通过 `scripts/skills.py check` 和 `package`。逐项比对两个 ZIP 与对应源文件的内容，确认轻量模板和降级说明随 Recto 分发，样例生成的 PDF、源码 ZIP 和日志未进入包。

## 只传技能 Markdown 的编译

本地模拟技能资源工具只返回 Markdown 的情况。从打好的插件中读取 `skills/recto/SKILL.md` 和其指向的 `references/pdf-fallback.md`，只把后者的 TeX 代码块写进空目录。编译目录中没有插件 ZIP、独立模板文件、插件脚本或随包字体。普通讲义入口直接选择这条路径，要求原字体或严格国标时走完整包流程。

- 用 XeLaTeX 的 `-no-shell-escape -halt-on-error -recorder` 编译模板内的积分例题，得到 1 页 A4。另在新目录对 `reference.md`、原稿的相对路径插图和取自同一模板的中文字体设置运行文档中的 Pandoc 命令，随后编译出 3 页 A4。只有长稿转换使用了 Pandoc。
- 逐页查看两份 PDF。核对了积分上下限、分数、多行推导、矩阵、表格、脚注和图注。两轮编译末次日志均无缺字和越界，PDF 嵌入了系统 Songti SC；两份 `.fls` 记录均没有读取技能目录或 ZIP。
- 新增回归测试以另一段中文和数学替换模板正文，在空目录编译并从 PDF 提取中文。该测试及插件打包测试通过。用 `scripts/plugin.py package --version 0.5.10` 打出的本地试用包与已测包逐项相同，唯一变化是清单版本号。

这次模拟验证了从纯文本到成品的过程。网页端对更新后插件的技能调用、资源读取及端到端编译有待在实际安装后验证。
