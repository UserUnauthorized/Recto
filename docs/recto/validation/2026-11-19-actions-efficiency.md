# GitHub Actions 耗时验收 · 2026-11-19

使用 `gh run list --limit 50` 取样时，GitHub 返回仓库全部 22 次运行。逐次读取 jobs API 的所有 attempt，包括失败、取消、跳过以及局部重跑时沿用的结果。下表使用秒，成功全量 PR 的历史中位数来自 9 次运行，范围 161–343 秒。

| 运行 | 工作流墙钟 | Runner 合计 |
|---|---:|---:|
| 优化前成功全量 PR 中位数 | 207 | 204 |
| [最近一次成功基线 PR](https://github.com/UserUnauthorized/Recto/actions/runs/44341132311) | 196 | 193 |
| [第一轮，冷 TeX、系统 APT 安装](https://github.com/UserUnauthorized/Recto/actions/runs/44346172320) | 291 | 461 |
| [第二轮，热 TeX、按 runner 镜像缓存 deb](https://github.com/UserUnauthorized/Recto/actions/runs/44347518008) | 221 | 332 |
| [固定 Ubuntu 二进制，热 TeX、冷 deb](https://github.com/UserUnauthorized/Recto/actions/runs/44348908664) | 141 | 213 |
| [轻量门禁与发行物往返重叠，全热](https://github.com/UserUnauthorized/Recto/actions/runs/44349930242) | 127 | 194 |
| [最终代码，全热 PR](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777) | 77 | 125 |
| [同一代码，干净分支手动演练，冷 TeX 和 deb](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186) | 159 | 297 |
| [纯文档 PR](https://github.com/UserUnauthorized/Recto/actions/runs/44346443702) | 14 | 11 |

最终版本的两个成功分片日志与基线逐项核对，23 个测试 ID 完全相同，每个 ID 均只执行一次。

最终代码样本 `b0d2028` 的全热 PR 比基线中位数缩短 130 秒（62.8%），Runner 合计变化 -79 秒。冷启动演练复用已有的默认分支 pip 缓存。Runner 型号、网络、镜像和队列影响单次实测，表内数值未按分钟计费取整。

## 耗时来自哪里

- 原全量 PR 的 job 分配等待中位数为 2 秒，开始执行测试前准备中位数为 103 秒。`Test and validate distribution` 及远端产物核验步骤合计中位数为 103 秒。各列中位数独立计算。
- 最近一次成功基线下载 284 MB Ubuntu 归档，安装后新增约 906 MB。系统依赖步骤用时 83 秒，其中生成 TeX 格式约 39 秒。同一内容合并到 main 后改用 us-east-2 镜像，首次运行约 16 分钟后取消，测试尚未开始。[首次 main 日志](https://github.com/UserUnauthorized/Recto/actions/runs/44342011498/attempts/1) 第一轮改用安装 action 自带的 TeX Live 2023 缓存后，第二轮同一 PR 的一次命中只用 2.5 秒。
- 另一台 runner 安装 5.8 MB 的 SVG、Poppler Debian 包仍花了 101 秒。两台 Ubuntu 24.04 runner 的镜像版本不同，生成了两份几乎相同的缓存。最终配置直接下载并复核 Ubuntu 快照里的四个二进制包，缓存键随包摘要变化。一次冷测中 Ubuntu 快照服务返回 503，[两组依赖失败后最终门禁也失败](https://github.com/UserUnauthorized/Recto/actions/runs/44350831150)。随后加入限时的 Azure 镜像、Ubuntu 主站及快照回退，保留相同 SHA-256。本地用真实包和替代下载命令注入 503、错误字节及正常快照，确认回退顺序。所有源都给出损坏内容时步骤以非零状态退出。TeX 约 205 MiB，pip 约 7 MiB，deb 约 6 MiB。构建产物通过 7 天 artifact 传输。
- 两台 Ubuntu runner 分摊 16 个 Recto 测试，并分别运行 6 个发布测试和 1 个插件测试。包结构、两套字体和样式依赖、消费者 TeX/PDF/DOCX 导出、报告复验、三个 ZIP 的 SHA-256 和下载往返均保留。状态汇总依赖两组全部成功。

## 触发与产物

[旧 PR 运行](https://github.com/UserUnauthorized/Recto/actions/runs/44345641428) 在新提交推送后自动取消。[纯文档 PR](https://github.com/UserUnauthorized/Recto/pull/17) 的路径检查成功，两个测试 job 和 `Full validation` 返回 skipped。仓库当时没有强制状态检查。根 README 与 `docs/` 下的 Markdown 命中筛选，随包 skill、截图和混合改动均运行完整校验。路径判断失败会使最后的检查失败。

PR #15 合并后的旧 main 运行前三次取消，[第四次](https://github.com/UserUnauthorized/Recto/actions/runs/44342011498/attempts/4) 的全量 job 用时 256 秒，并于北京时间 00:48:39 成功。后续三次 attempt 在基线取样之后发生。

每次 main 推送以自己的 run ID 验收该 push 的最终 SHA。手动演练独立运行，正式标签维持串行发布。发布机器人回写版本号沿用现有流程。本次在非 main 分支演练全量路径，未推正式标签。

本地连续两次运行 `python3 scripts/release.py build --tag v0.5.5`，原实现用时 2.496 / 2.482 秒，优化后用时 2.512 / 0.125 秒。源码变更、归档损坏的重建回归通过。GitHub 的发行包始终重新构建并验证。交付的 reference TeX 连续运行 latexmk 用时 38.256 / 0.117 秒，第二次调用 LuaLaTeX 0 次。两项本地计时均来自 macOS。

与最近成功基线比较，最终版本的三个发行 ZIP 构建 SHA-256 一致。对照基线与 44348908664 的 consumer-exports 样例，reference 为 4 页、gbt9704 为 5 页。两份 PDF 的提取文本及全部页面的 96 DPI 栅格像素一致，两份 DOCX 的规范化 `word/document.xml` 一致。

## 逐 job 时间

等待从 job 创建算到分配 runner。准备从 runner 开始算到首次测试、发布、产物校验或路径判断。执行至结束含后续传输与收尾。核心步骤另列 GitHub 记录的测试、发布或验证 step 秒数。工作流墙钟从 run 创建算到完成，包含 job 依赖等待。跳过和复用结果不重复计算 runner 用时。

<details>
<summary>优化前的 22 次运行，共 46 条 job 记录</summary>

| Run / attempt | Job | 结果 | 等待 | 准备 | 执行至结束 | 核心步骤 | Runner |
|---|---|---|---:|---:|---:|---:|---:|
| 44342011498/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/44342011498/job/134934259983) | cancelled | 2 | 994 | 0 | 0 | 994 |
| 44342011498/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/44342011498/job/134945883561) | cancelled | 0 | 0 | 0 | 0 | 0 |
| 44341132311/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/44341132311/job/134931089250) | success | 2 | 94 | 99 | 85 | 193 |
| 44341132311/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/44341132311/job/134933299700) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43860240435/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43860240435/job/133274836094) | success | 2 | 107 | 139 | 129 | 246 |
| 43860240435/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43860240435/job/133276913068) | success | 2 | 6 | 15 | 13 | 21 |
| 43859452841/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43859452841/job/133272113711) | success | 2 | 102 | 127 | 120 | 229 |
| 43859452841/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43859452841/job/133274047939) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43858682680/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43858682680/job/133269488434) | success | 3 | 82 | 91 | 84 | 173 |
| 43858682680/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43858682680/job/133270935023) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43428322148/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43428322148/job/131895181798) | success | 2 | 100 | 132 | 119 | 232 |
| 43428322148/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43428322148/job/131896974702) | success | 3 | 7 | 15 | 13 | 22 |
| 43427729321/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43427729321/job/131893208086) | success | 2 | 101 | 119 | 112 | 220 |
| 43427729321/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43427729321/job/131894963426) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43426968024/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43426968024/job/131890652554) | success | 2 | 116 | 140 | 134 | 256 |
| 43426968024/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43426968024/job/131892673175) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43152354222/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43152354222/job/130964294282) | success | 2 | 100 | 115 | 105 | 215 |
| 43152354222/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43152354222/job/130965610610) | success | 2 | 6 | 19 | 17 | 25 |
| 43151635440/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43151635440/job/130961954905) | success | 2 | 110 | 138 | 126 | 248 |
| 43151635440/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43151635440/job/130963409775) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43151111600/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43151111600/job/130960202761) | success | 1 | 92 | 112 | 107 | 204 |
| 43151111600/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43151111600/job/130961435444) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43071117215/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43071117215/job/130698923853) | success | 2 | 153 | 131 | 124 | 284 |
| 43071117215/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43071117215/job/130701635232) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43070301268/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43070301268/job/130696057407) | success | 2 | 103 | 127 | 108 | 230 |
| 43070301268/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43070301268/job/130698221288) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43068441419/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43068441419/job/130689558316) | success | 2 | 107 | 119 | 113 | 226 |
| 43068441419/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43068441419/job/130691718970) | failure | 2 | 6 | 7 | 5 | 13 |
| 43068441419/2 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43068441419/job/130697157974) | success | 2 | 5 | 9 | 7 | 14 |
| 43068441419/2 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43068441419/job/130697214194) | reused | 0 | 0 | 0 | 0 | 0 |
| 43067062117/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43067062117/job/130684738718) | success | 2 | 252 | 147 | 136 | 399 |
| 43067062117/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43067062117/job/130688590359) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43065933888/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43065933888/job/130680750065) | success | 2 | 195 | 145 | 132 | 340 |
| 43065933888/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43065933888/job/130684073504) | skipped | 0 | 0 | 0 | 0 | 0 |
| 43062200806/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/43062200806/job/130667471273) | failure | 2 | 425 | 91 | 88 | 516 |
| 43062200806/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/43062200806/job/130672474772) | skipped | 0 | 0 | 0 | 0 | 0 |
| 42869032234/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/42869032234/job/130015002485) | success | 3 | 118 | 122 | 108 | 240 |
| 42869032234/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/42869032234/job/130017379306) | skipped | 0 | 0 | 0 | 0 | 0 |
| 42867819716/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/42867819716/job/130010777440) | success | 1 | 103 | 93 | 85 | 196 |
| 42867819716/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/42867819716/job/130012709481) | skipped | 0 | 0 | 0 | 0 | 0 |
| 42866977130/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/42866977130/job/130007822341) | success | 1 | 80 | 78 | 70 | 158 |
| 42866977130/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/42866977130/job/130009375630) | skipped | 0 | 0 | 0 | 0 | 0 |
| 42865512394/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/42865512394/job/130002681816) | success | 1 | 115 | 109 | 103 | 224 |
| 42865512394/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/42865512394/job/130004955572) | skipped | 0 | 0 | 0 | 0 | 0 |
| 42864486537/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/42864486537/job/129999043169) | success | 2 | 105 | 98 | 92 | 203 |
| 42864486537/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/42864486537/job/130001112528) | skipped | 0 | 0 | 0 | 0 | 0 |

</details>

<details>
<summary>最终代码的热 PR 与冷启动演练</summary>

| Run / attempt | Job | 结果 | 等待 | 准备 | 执行至结束 | 核心步骤 | Runner |
|---|---|---|---:|---:|---:|---:|---:|
| 44351687777/1 | [Select PR checks](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777/job/134968744721) | success | 3 | 5 | 3 | 1 | 8 |
| 44351687777/1 | [Packages and consumer exports](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777/job/134968871332) | success | 1 | 18 | 38 | 32 | 56 |
| 44351687777/1 | [Recto export tests](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777/job/134968871615) | success | 1 | 11 | 45 | 43 | 56 |
| 44351687777/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777/job/134969534479) | success | 3 | 2 | 3 | 0 | 5 |
| 44351687777/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/44351687777/job/134969626608) | skipped | 0 | 0 | 0 | 0 | 0 |
| 44351777186/1 | [Packages and consumer exports](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186/job/134969084859) | success | 2 | 98 | 49 | 33 | 147 |
| 44351777186/1 | [Recto export tests](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186/job/134969086274) | success | 2 | 95 | 52 | 48 | 147 |
| 44351777186/1 | [Select PR checks](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186/job/134969087265) | skipped | 0 | 0 | 0 | 0 | 0 |
| 44351777186/1 | [Full validation](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186/job/134970796600) | success | 3 | 1 | 2 | 0 | 3 |
| 44351777186/1 | [Publish verified tag](https://github.com/UserUnauthorized/Recto/actions/runs/44351777186/job/134970865802) | skipped | 0 | 0 | 0 | 0 | 0 |

</details>
