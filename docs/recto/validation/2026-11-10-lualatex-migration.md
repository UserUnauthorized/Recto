# LuaLaTeX 与 latexmk 迁移验收

日期：2026-11-10。基线：`48440fcc09c6242a87079cc5629debf94a767911`。实现位于 `codex/lualatex-migration`。本记录对应本地验收，不包含合并、发布或已安装插件替换。

## 最终行为

默认输出由 Markdown、Typst、PDF 改为 Markdown、`latex/document.tex`、PDF。PDF 统一由 `latexmk -norc -lualatex` 管理编译轮次；不读取自动 RC，仅显式载入随源交付的构建规则；不开启 shell escape 或 Lua socket，不维护固定两轮或其他引擎回退。编译总时限 480 秒，超时终止编译进程组；只有成功且最终日志无缺字、溢出及 LaTeX/package/font 警告时才替换旧 PDF。

`--formats tex` 和 `--formats docx` 不要求 LuaLaTeX、latexmk、kpsewhich 或 Typst。旧 `typ` 参数会明确提示改用 `tex`。两套样式、字体替代、共享图片、附录标签、奇偶页旋转与 Word 原生横向节继续保留。调用方 `study-notes`、插件元数据、安装指引、README 及行为场景同步更新，待发布版本号为 0.5.0。

## 环境与产物

macOS；Pandoc 3.9.0.2；LuaHBTeX 1.24.0 / TeX Live 2026 Basic；latexmk 4.89；DOCX 使用工作区捆绑 Python、python-docx/lxml 和 LibreOfficeDev 26.8.0.0.alpha0。依赖检测及仓库打包使用已有 Python/PyYAML，不修改系统 Python。

TeX 宏包和重建格式复用前次对照试验的隔离用户树。latexmk 的 TeX Live 包不能以用户模式安装，本次从官方镜像下载 4.89 包，对照 TeX Live 元数据验证 SHA-512 后解包至忽略目录，并仅对验证进程添加 PATH。没有改动系统 TeX 或永久 PATH；这些环境路径不写入正式源或发行包。

公开导出入口：`skills/recto/scripts/export.py`。导出报告、源码、校样和诊断均位于本地忽略目录 `output/recto/migration/`，不随 Git 提交；以下记录保留验收结论。

| 样例 | PDF | 逐页检查 | Word |
|---|---:|---|---|
| reference 原字体 | 4 页 | 通过 | 4 页 |
| reference 随包字体 | 4 页 | 通过 | 本行只测 PDF/TeX |
| gbt9704 原字体 | 5 页 | 通过 | 5 页 |
| gbt9704 随包字体 | 5 页 | 通过 | 本行只测 PDF/TeX |

检查了公式 (1.1)–(1.8)、积分与多行对齐、向量/范数/矩阵、图注、脚注、表格、四级标题、附录及单双页页码。所有源稿中文短语保留；讲义 66 个数学节点在规范化 Markdown 中逐项一致。最终 latexmk 输出与已检查的页面渲染字节一致。README 的四幅首页预览已更新。

本地产物：`output/recto/migration/reference/document.pdf`、`output/recto/migration/gbt9704/document.pdf` 与 `output/recto/migration/artifact-audit.json`。

## 独立验证

- 移动含空格的交付目录后，用源码顶部的 latexmk 命令重新编译，并从规范化 Markdown 再导出；图片只有一份，必要字体与许可证保留，编译中间文件不进入交付目录。
- 目录改变正文页码的 TeX 验证文档：直接运行 LuaLaTeX 两次后仍有交叉引用重跑警告；latexmk 运行三轮后稳定。`-norc` 也通过含有故意报错项目 RC 的用例验证。
- 并行导出曾因 LuaTeX-ja `extra_*.lua.gz` / `.luc` 字体缓存被不同任务改写而耗尽重跑次数；新增 `latex/latexmkrc` 只将这些派生缓存移出依赖列表，真实字体文件仍被跟踪。独立解包导出与回归测试并行运行，重现原先的争用条件验证修复。
- 50 行国标长表格分为 3 页，逐页查看通过；每页重复表头，50 条记录按顺序全部存在。
- 未定义数学命令、过高横向附录失败时，原 PDF 字节不变。横向附录先测自然高度，再装入固定版心，避免旋转后偏移。
- 中文表格结尾的“习”及附录标题中的 `%`、`&` 保留/转义正确。Lua 的本地化 `%s` 曾错误截去 UTF-8 尾字节，现只裁剪 ASCII 空白，并有源文件回归用例。
- 自包含 SVG 经显式 `rsvg-convert` 转成 PDF 资源，可随 TeX 重建；外部图片/样式引用会明确拒绝。修复前探针确实能无警告生成缺图资源，修复后公共导出入口拒绝同一输入。
- Word-only 在 PATH 中只有真实 Pandoc 的环境导出成功，讲义保留 66 个原生 OMML 对象。新旧两份 DOCX 的全部 12 个 `word/` 部件分别逐字节相同；两份新 DOCX 又通过捆绑 LibreOffice 重新渲染并逐页查看。

`checks/recto/` 最终整套运行 9 项全部通过，耗时 359.121 秒，日志见 `output/recto/migration/tests.log`。覆盖 LuaTeX-ja 缓存过滤后真实字体依赖仍在、移动目录重编译、SVG 外部图片与顶层样式引用拒绝，以及失败时旧 PDF 不变。此前的一次整套运行曾因 TeX 把错误提示的英文单词换行而误报，现按空白无关的诊断匹配；缓存争用问题也在修复后重跑，不将先前失败记录当作成功。

仓库的 `scripts/skills.py check`、两项 skill 打包、插件检查/打包、插件包测试及 `git diff --check` 通过。包不含试验运行时、QA、缓存或用户材料。另从独立解包目录运行公开入口验证发行物；包附 `dist/SHA256SUMS`，结果记录在 `output/recto/migration/package-consumer-report.json`。最后只更新说明文档后重新打包，9 个运行时文件与已解包实测包逐字节一致；插件 ZIP 中全部 skill 文件与正式源一致。

新增缓存规则经独立只读审查，未发现具体阻塞项；审查不冒充再次运行编译器。

## 边界

本轮是 macOS 本地迁移验收，不代表 ChatGPT 会话、Windows、WPS 或全新机器安装验收。没有重新进行原生 Word 编辑/保存往返；前次 Word for Mac 16.114.4 校样仍可作为相同 Word 内容部件的既有证据。

[Word Issue #4](https://github.com/UserUnauthorized/Recto/issues/4) 的多行对齐、最终数学字体设置和证明方框问题按用户决定保留后续处理。本次没有修改这些逻辑。GB/T 样式仍仅覆盖正文、表格和附录，不宣称完整公文标准认证。任意 TeX 宏包、复杂合并表格与其他文字系统未扩大支持范围。
