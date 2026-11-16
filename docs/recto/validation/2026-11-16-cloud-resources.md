# Web 端随包资源读取流程

基线：`fb69788`（插件 0.5.4）。本次仅修改技能指令、README 和行为场景，未修改导出脚本、模板、字体或插件清单。

## 问题与证据

- 用户提供的 Web 会话出现搜索词 `UserUnauthorized Recto github plugin skill pdf export scripts`；浏览器页面确认了该活动，但会话接口与页面均未提供完整工具参数或执行环境文件清单。
- 实际云端插件详情显示版本 0.5.4、两个技能；Recto 技能正文及附带的 43 个资源可见，包含 `scripts/export.py`、`scripts/doctor.py`、模板和字体。该列表可排除上传包缺少这些文件，不能证明它们已挂载到该会话的执行环境。
- 旧指令直接假定 `SKILL.md` 有本地路径，缺少云端资源取得步骤；study-notes 的“不得复制导出器、模板或字库”也可能阻碍原样落盘。搜索的直接原因仍未从运行轨迹证实。
- [OpenAI 技能文档](https://learn.chatgpt.com/docs/build-skills)确认按需读取技能及随包资源的设计；具体云端工具用法来自当前宿主提供的技能说明。`skills.list` / `skills.read` 仅在宿主实际提供时使用，不宣称所有 Web 会话都暴露相同接口或具备文件传输能力。

## 修正与行为走读

入口先确定当前包来源，再以宿主提供的文件目录或资源工具读取；完整资源准备只在运行脚本前进入 setup。运行目录核对后复用原 doctor、export 和复验入口，Word 渲染示例也改为使用已确认的绝对 skill 路径。

走读 `checks/recto/scenarios.md` 的 J 和 `checks/study-notes/scenarios.md` 的 AD，并复查原有首次安装、缺失依赖及两技能交接场景：

| 场景 | 指令要求的结果 |
|---|---|
| Web 或本地已有挂载目录 | 在实际 Python 环境确认可读后复用 |
| 云端入口、相对参考和同名多包 | 使用返回的资源标识，保持本次所选包来源 |
| 完整下载或逐文件传输 | 原字节落盘并保留目录结构；核对文件及字体哈希 |
| 单技能 ZIP 与完整插件 ZIP | 分别取 `recto/` 和 `skills/recto/` 作为实际根目录 |
| 只有预览、字体缺字节、目录在其他主机或没有执行能力 | 保留源稿并报告具体缺项，停止导出，不搜索公开仓库补实现 |
| 包完整而系统依赖缺少 | 按所需格式补依赖、复查并继续 |
| 更新授权或正文事实研究 | 保留原有授权边界，不把插件来源约束扩大为禁止研究 |
| study-notes 直接调用及往返交接 | 读取云端参考；由 Recto 准备执行目录，允许当前包原样落盘 |

这是指令走读，不是模型遵从率测试。

## 本地检查

- `python3 scripts/skills.py check recto`：通过，45 文件。
- `python3 scripts/skills.py check study-notes`：通过，6 文件。
- `python3 scripts/plugin.py check`：通过，55 文件。
- 两个 skill 的 `package` 均成功；`python3 -m unittest discover -s checks/plugin -p 'test_*.py'` 通过，检查插件 ZIP 中的资源与正式源逐字节一致。
- 将单技能 ZIP 和完整插件 ZIP 分别解到新的任务工作目录，逐文件确认 Recto 的 45 个文件与 ZIP 及正式源一致。从 skill 目录以外运行绝对路径的 `doctor.py --style reference --formats tex --bundled-fonts`，两者均退出 0；Python 3.12、Pandoc 3.9.0.2。两个目录的 `render_word.py --help` 均可运行。
- 既有 `RuntimeTests.test_font_files_and_licenses_match_recorded_bytes` 通过，核对字体与许可证的 SHA-256。

## 推送前的验证边界

本记录覆盖提交前的本地验收：此阶段未上传或更新云端插件、未安装到用户技能目录、未发布；本地候选包清单仍为基线 0.5.4。后续 CI、合并和发行状态以对应提交的检查及 Release 为准。没有在真实 Web 会话中执行新流程，无法保证特定会话提供完整文件或执行能力；本地也未新做 PDF／Word 导出、视觉验收或完整 CI。已有 Web 安装需要更新插件包才会获得新规则。
