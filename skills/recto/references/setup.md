# 首次安装与缺失依赖

只处理检查报告中缺少或过旧的项目，完成后回到原任务。不改写正文、不生成示例文档来冒充用户交付。不在每次导出时重装，也不向系统 Python 运行 `sudo pip`。

## 准备运行目录

先按 [读取随包资源](../SKILL.md#读取随包资源) 确定本次包来源，再选择当前执行环境支持的分支；Web 端也可能已经挂载文件，按实际能力判断。

1. **已有文件目录**：使用宿主返回的 Recto skill 路径，在将要运行 Python 的环境中确认文件可读。确认通过后直接复用；浏览器或另一台主机上的路径不能代替执行环境中的路径。
2. **只有云端资源**：查看当前技能资源工具的说明，优先使用它提供的包挂载或完整下载能力。需要落盘时，在本轮非交付工作目录中新建独立目录，原样保存同一包的文件与目录结构，包括 `SKILL.md`、`scripts/`、`references/`、`assets/` 和 `requirements.txt`；只含单个 skill 的包或含 `skills/recto/` 的插件包均取实际 skill 根目录。若只支持逐文件取得，按该包文件清单保存全部随包文件。保留脚本、Lua 过滤器、模板、字体二进制和许可证；正文预览、截断文本或只有文件名的清单不足以恢复可执行文件。原样落盘用于运行当前包，不是重写导出器或维护另一份实现。
3. **清单可读但字节取不到**：若字体读取返回 `Resource not readable` 或脚本只有预览，先查本会话已提供的同包 ZIP，或宿主能按当前插件及 release ID 取得的完整归档。在实际运行 Python 的环境打开归档。若宿主没有这条通道，但已从所选插件的元数据确认来源为 `UserUnauthorized/Recto` 的正式版本 `X.Y.Z`，可从 `https://github.com/UserUnauthorized/Recto/releases/download/vX.Y.Z/` 取 `recto-skill.zip` 和 `SHA256SUMS`。用同一标签清单中该文件的 SHA-256 校验下载字节，匹配后才解到新的工作目录。没有网络时，可请用户把同版正式包与校验文件附到当前会话。版本未知时先索取所选插件的版本或宿主原包；不要猜版本、取 latest 或把单个文件混入现有目录。
4. **确认可运行**：将 `RECTO_ROOT` 设为上述执行环境中实际包含 `SKILL.md` 的绝对目录。按包文件清单核对文件齐全、可读、相对结构未变；有大小或校验值时核对一致，随包字体另按 `assets/fonts/SHA256SUMS.json` 校验。只有资源标识、下载成功提示或读到了 `export.py` 的文字，都不能算这一步完成。同一会话复用已核对目录；包来源变化时使用新目录，避免混合版本。

平台没有脚本执行能力，或以上途径仍无法在执行环境取得可核验的包时，保留源稿，明确标注 PDF 待导出。指出失败的资源相对路径或命令、实际错误，以及恢复需要的文件或能力。若执行环境可运行命令但无法联网，先用 `pandoc --version` 核对下方的版本要求，需要 PDF 时也检查 `latexmk` 和 `lualatex`。一次列出已知的离线补件，包到位后仍须运行 doctor，再从现有源稿继续。

## 检查

沿用已确认的 `RECTO_ROOT`。有 `mcp__codex_app__load_workspace_dependencies` 时使用它返回的 Python，否则使用当前执行环境中的 Python 3.10+，将其可执行路径记为 `RECTO_PYTHON`。依赖检查、安装和导出始终在同一执行环境中运行。

```sh
"$RECTO_PYTHON" "$RECTO_ROOT/scripts/doctor.py" --style reference --formats tex,pdf
```

检查不联网、不写入系统。退出码 0 表示所选格式依赖齐全；退出码 1 的 `issues` 指出缺项，`substitutions` 列出随包字体替代。只导出 TeX 或 Word 时相应传入 `--formats tex` 或 `--formats docx`：它们不要求 `latexmk` 或 TeX；PDF 要求 LuaLaTeX、`latexmk`、`kpsewhich` 和 TeX 包。替代不是错误，导出前简短告知即可。要求只用随包字体时加 `--bundled-fonts`。

## 安装缺项

1. **Python**：有 Codex 捆绑运行时就复用。没有可用 Python 时，使用现有系统包管理器安装 Python 3.10+；没有包管理器时，按 [Python 官方安装说明](https://www.python.org/downloads/) 完成后继续。
2. **Pandoc**：PDF 和 TeX 先用系统版本（最低 3.1.11.1），直接运行同一导出器。它从本机帮助信息选择代码高亮参数。若 reference 稿含表题，必须能把表题置于表下；缺少 `--table-caption-position` 时导出器会指出这项限制。GB/T 的 LaTeX 模板自行处理表题。旧版 Pandoc 的 LuaLaTeX 模板可能需要 TeX 宏包 `selnolig`，缺它时补该宏包即可。只在缺少可用 Pandoc、实际文稿需要系统版本不提供的功能、或 DOCX 所需的 3.9 尚未满足时，按 [Pandoc 安装说明](https://pandoc.org/installing.html)选择可用版本。
3. **TeX / latexmk**：PDF 需要 LuaLaTeX（建议 TeX Live 2024+）和 `latexmk`。优先用已安装的 TeX Live/MacTeX 管理器安装 `latexmk` 及缺失宏包；`latexmk` 依赖 Perl，macOS/Unix 通常已具备，Windows 通常随 Strawberry Perl 提供。TeX Live 的非重定位安装不能用 `tlmgr --usermode` 安装 `latexmk`。安装后确认 `lualatex`、`latexmk`、`kpsewhich` 都在 PATH。
4. **TeX 包**：需要 `ctex luatexja lualatex-math fontspec unicode-math titlesec caption needspace eso-pic float tools booktabs graphics geometry hyperref xcolor fancyvrb fvextra framed bookmark footnotehyper etoolbox microtype lm`。`fvextra` 要求 ≥1.5（2022-11-30），负责代码长行换行，`framed` 提供可跨页的浅底代码块；不需要 Python 高亮器或 shell escape。doctor 用 `kpsewhich` 逐项探测；安装报告中的具体缺项后重跑同一 doctor 命令。只有 LaTeX 格式与宏包版本不匹配时才重建对应格式（例如 `fmtutil-user --byfmt lualatex`）；字体缓存问题另按 luaotfload 诊断处理，不作为例行操作。
5. **Python 包**：若现有运行时缺少 `python-docx` 或 `lxml`，新建专属虚拟环境，随后一直用其 Python 检查和导出，不修改 Codex 的捆绑运行时。macOS／Linux 示例：

   ```sh
   python3 -m venv "$HOME/.local/share/recto/venv"
   RECTO_PYTHON="$HOME/.local/share/recto/venv/bin/python"
   "$RECTO_PYTHON" -m pip install -r "$RECTO_ROOT/requirements.txt"
   ```

   已有这个环境时直接复用；升级只补缺项。Windows 可在 `%LOCALAPPDATA%\Recto\venv` 建环境，解释器在 `Scripts\python.exe`。

6. **可选 SVG 转换**：仅当输入 SVG 时需要 `rsvg-convert`（librsvg）。PNG/JPEG/PDF 输入和仅 Word 导出不需要它；生成含 SVG 的 TeX 源也需要转换该图像资源。缺少命令时按安装提示处理，或改供 PNG/PDF。
7. **字体**：有原字体就沿用；缺少时使用 Fandol、Liberation Serif 和 New Computer Modern Math。代码使用随包 Liberation Mono 与 Fandol 仿宋。LuaLaTeX 直接读取随包 `assets/fonts/`。Word 编辑需要让编辑器找到这些字体：macOS 把随包 `.otf`／`.ttf` 复制到 `~/Library/Fonts/Recto/`，Linux 复制到 `~/.local/share/fonts/Recto/` 后运行 `fc-cache -f`；Windows 使用系统“为当前用户安装”字体。保留许可证，遇到同名不同内容的现有文件先保留旧副本，不直接覆盖。重启已打开的 Word／LibreOffice。不要复制或发布用户系统中的专有字体。

## 复查与返回

用最终选定的 Python 和 PATH 重跑 doctor，退出码为 0 后继续原来的文档任务。用户只要求安装／运行插件 onboarding 时，到这里结束，报告实际版本和字体选择，不凭空生成内容。

首次使用某种格式仍需真实导出并查看页面。DOCX 优先使用桌面依赖加载器返回的 LibreOffice 和文档技能渲染器；没有这些能力时可安装 LibreOffice，用 `soffice --headless --convert-to pdf --outdir qa document.docx` 导出检查 PDF。渲染器不可用时只报告导出成功与视觉验收待办，不称为已完成 QA。Windows 安装路径未在本项目实机验收。
