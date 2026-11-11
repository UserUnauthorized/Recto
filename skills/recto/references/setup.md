# 首次安装与缺失依赖

只处理检查报告中缺少或过旧的项目，完成后回到原任务。不改写正文、不生成示例文档来冒充用户交付。不在每次导出时重装，也不向系统 Python 运行 `sudo pip`。

## 检查

把 `RECTO_ROOT` 设为当前 `SKILL.md` 所在目录。桌面有 `mcp__codex_app__load_workspace_dependencies` 时，先用它返回的 Python；没有该工具时选本地 Python 3.10+。

```sh
"$RECTO_PYTHON" "$RECTO_ROOT/scripts/doctor.py" --style reference --formats tex,pdf
```

检查不联网、不写入系统。退出码 0 表示所选格式依赖齐全；退出码 1 的 `issues` 指出缺项，`substitutions` 列出随包字体替代。只导出 TeX 或 Word 时相应传入 `--formats tex` 或 `--formats docx`：它们不要求 `latexmk` 或 TeX；PDF 要求 LuaLaTeX、`latexmk`、`kpsewhich` 和 TeX 包。替代不是错误，导出前简短告知即可。要求只用随包字体时加 `--bundled-fonts`。

## 安装缺项

1. **Python**：有 Codex 捆绑运行时就复用。没有可用 Python 时，使用现有系统包管理器安装 Python 3.10+；没有包管理器时，按 [Python 官方安装说明](https://www.python.org/downloads/) 完成后继续。
2. **Pandoc**：要求 ≥3.9。macOS 已有 Homebrew 时仅安装缺少的 `pandoc`，过旧的使用 `brew upgrade`。其他系统按 [Pandoc 安装说明](https://pandoc.org/installing.html)安装官方版本，并让当前进程的 PATH 包含其目录。
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
