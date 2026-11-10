# CI/CD

发布约定见 [标签决定发行版本](adr/0003-tag-driven-releases.md)。工作流为 `.github/workflows/ci.yml`，本地复用入口为 `scripts/ci.py`；打包和发布复用 `scripts/release.py`、`scripts/plugin.py` 与 `scripts/skills.py`。

## 日常检查

PR、`main` 推送和手动运行都在 Ubuntu 24.04 上检查。依赖由 `.github/actions/setup-recto/action.yml` 安装：Python 3.12、经 SHA-256 核对的 Pandoc 3.9.0.2、发行版 LuaLaTeX、中文和日文 TeX 支持、librsvg、Poppler，以及两个 requirements 文件。latexmk 固定为维护者提供的 4.89 归档并核对 SHA-512，因为导出器使用的 hook 接口在 4.84 才公开，不能依赖 Ubuntu 的较旧版本。pip 缓存按 requirements 更新；不依赖开发者机器或私有 documents skill。

`scripts/ci.py` 依次完成两套样式的依赖检查、两个 skill 与插件的结构检查、全部 Recto／插件／发布测试、三个安装包和校验文件生成。随后在新的消费者目录解压插件，用包内样例与公开入口导出两套样式的 TeX、PDF、DOCX，并复验报告。使用随包字体；缺少 SVG 转换工具会失败，不能把对应测试跳过当成全通过。

成功安装包保存在 `release-bundle` artifact，消费者 PDF、DOCX 与 JSON 报告保存在 `consumer-exports`，保留 7 天。CI 检查正文转换及结构、编译和交付链路，不等于原生 Word／WPS 的视觉验收。相关排版变更仍按仓库约定进行人工逐页检查。

备齐依赖后，本地可运行：

```sh
python -m pip install -r requirements-dev.txt -r skills/recto/requirements.txt
python scripts/ci.py
# 演练指定版本；本地和 Actions 手动运行均不会自动发布。
python scripts/ci.py --tag v0.5.2
```

入口要求 Git 跟踪文件干净，产物和证据位于忽略目录 `output/recto/ci/` 与 `dist/`。

## 标签发布

仅推送 `vX.Y.Z` 正式标签触发发布；不支持预发布后缀或带前导零的版本。标签必须仍指向本次验证的提交，该提交必须已合并进 `main`，版本不得低于已有正式 Release；相同版本仅用于重跑同一发布。所有发布任务串行，PR／main 上过时的检查可以取消。一次推送一个标签，避免 GitHub 的待运行并发任务替换规则取消中间版本。

标签会重新执行完整检查。发布 job 只下载同次工作流已验证的安装包，不另行打包。先创建草稿、上传三个 ZIP 和 `SHA256SUMS`，核对远端摘要与大小并下载逐字节比较，最后公开为最新正式 Release。说明由 GitHub 根据变更自动生成，全部检查失败都会阻止新的公开发布。

只有发布 job 获得 `contents: write`；其余 job 只读，PR 不获得发布权限。使用仓库自带 `GITHUB_TOKEN`，无需另配个人令牌。发布成功后通过 Contents API 仅更新 `main` 中 `plugin.json` 的版本，沿用 GitHub 令牌对应的提交身份，带当前文件 SHA 防止覆盖并发修改。使用该令牌产生的提交不会再触发 `push` 工作流，因此版本同步不会递归发布。参见 [GitHub 令牌事件规则](https://docs.github.com/en/actions/concepts/security/github_token)和 [Contents API](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents)。

现有 Marketplace 入口仍追踪 `main`。发布更新可被插件管理器发现，但不会替用户自动更新本机安装，也不会提交到 OpenAI 公共插件目录。

## 失败与重跑

- **验证失败**：修复代码后使用新标签；尚未公开的失败任务也可在输入未变时重跑。不要移动已推送的标签。
- **草稿上传或下载失败**：重跑会补齐草稿资产，核对后才公开。草稿可替换；已正式发布的资产不覆盖。
- **已公开但版本同步失败**：重跑发布 job，先核对原资产和下载结果，再补同步。不会再次上传正式资产；校验不一致则停止，避免把不同字节悄悄变成同一版本。
- **artifact 已过期**：重跑全部 jobs，重新验证和生成同版本包。若环境漂移使新包与正式资产不同，检查会停止；不能以覆盖正式资产解决。
- **main 增加了保护规则**：版本同步会遵守规则并明确失败，不绕过保护。需根据仓库的新维护流程调整同步方式。

发布标签不移动，源码清单不回写到标签提交。需要复现包时必须传入标签版本；GitHub 自动生成的源码归档不是带有新版清单的正式插件 ZIP。
