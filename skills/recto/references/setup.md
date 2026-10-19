# 首次安装与缺失依赖

只处理检查报告中缺少或过旧的项目，完成后回到原任务。不改写正文、不生成示例文档来冒充用户交付。不在每次导出时重装，也不向系统 Python 运行 `sudo pip`。

## 检查

把 `RECTO_ROOT` 设为当前 `SKILL.md` 所在目录。桌面有 `mcp__codex_app__load_workspace_dependencies` 时，先用它返回的 Python；没有该工具时选本地 Python 3.10+。

```sh
"$RECTO_PYTHON" "$RECTO_ROOT/scripts/doctor.py" --style reference
```

检查不联网、不写入系统。退出码 0 表示导出依赖齐全；退出码 1 的 `issues` 指出缺项，`substitutions` 列出随包字体替代。替代不是错误，导出前简短告知即可，不重新询问已确定的样式。明确要求原字体时不能自动换字库。

## 安装缺项

1. **Python**：有 Codex 捆绑运行时就复用。没有可用 Python 时，使用现有系统包管理器安装 Python 3.10+；没有包管理器时，按 [Python 官方安装说明](https://www.python.org/downloads/) 完成后继续。不要为此安装完整 TeX 发行版。
2. **Pandoc / Typst**：要求 Pandoc ≥3.9、Typst ≥0.15.1。macOS 已有 Homebrew 时仅安装缺少的 `pandoc` 或 `typst`，过旧的使用 `brew upgrade`。其他系统使用 [Pandoc 安装说明](https://pandoc.org/installing.html) 与 [Typst 官方发布](https://github.com/typst/typst/releases) 的对应系统版本。发行版仓库版本过旧时用官方预编译版本，并让当前导出进程的 PATH 包含其目录。安装需要联网；网络或权限受限时保留具体失败和继续方式，不能声称已安装。
3. **Python 包**：若现有运行时缺少 `python-docx` 或 `lxml`，新建专属虚拟环境，随后一直用其 Python 检查和导出，不修改 Codex 的捆绑运行时。macOS／Linux 示例：

   ```sh
   python3 -m venv "$HOME/.local/share/recto/venv"
   RECTO_PYTHON="$HOME/.local/share/recto/venv/bin/python"
   "$RECTO_PYTHON" -m pip install -r "$RECTO_ROOT/requirements.txt"
   ```

   已有这个环境时直接复用；升级只补缺项。Windows 可在 `%LOCALAPPDATA%\Recto\venv` 建环境，解释器在 `Scripts\python.exe`。

4. **字体**：Typst 直接读取随包 `assets/fonts/`，不再下载字体。有原字体就沿用；缺少时使用 Fandol、Liberation Serif 和原来的 New Computer Modern Math。Word 编辑需要让编辑器找到这些字体：macOS 把随包 `.otf`／`.ttf` 复制到 `~/Library/Fonts/Recto/`，Linux 复制到 `~/.local/share/fonts/Recto/` 后运行 `fc-cache -f`；Windows 使用系统“为当前用户安装”字体。保留许可证，遇到同名不同内容的现有文件先保留旧副本，不直接覆盖。重启已打开的 Word／LibreOffice。不要复制或发布用户系统中的专有字体。

## 复查与返回

用最终选定的 Python 和 PATH 重跑 `doctor.py`，退出码为 0 后继续原来的文档任务。用户只要求安装／运行插件 onboarding 时，到这里结束，报告实际版本和字体选择，不凭空生成内容。

首次使用某种格式仍需真实导出并查看页面。DOCX 优先使用桌面依赖加载器返回的 LibreOffice 和文档技能渲染器；没有这些能力时可安装 LibreOffice，用 `soffice --headless --convert-to pdf --outdir qa document.docx` 导出检查 PDF。渲染器不可用时只报告导出成功与视觉验收待办，不称为已完成 QA。Windows 安装路径未在本项目实机验收。
