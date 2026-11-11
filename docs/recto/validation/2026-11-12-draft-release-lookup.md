# 2026-11-12：首次标签发布的草稿查询

v0.5.2 的[标签运行](https://github.com/UserUnauthorized/Recto/actions/runs/43068441419)通过 `Full validation`、消费者导出和 artifact 往返校验，但首次 `Publish verified tag` 在上传四个资产后返回 404，Release 留在草稿状态。

实际 API 复现：发布列表能返回 v0.5.2 草稿与全部资产，而 `releases/tags/v0.5.2` 返回 404。[GitHub 的接口说明](https://docs.github.com/en/rest/releases/releases#get-a-release-by-tag-name)将按标签查询限定为已公开 Release；有推送权限的调用者可从发布列表读取草稿。

发布脚本在上传后复用已有 `preflight`，从包含草稿的发布列表取得最新资产。公开之后仍用按标签接口复验。标签、版本递增、远端摘要、下载字节比较和已公开资产不可覆盖等门禁不变。

扩展既有首次发布失败测试，使按标签查询草稿真实返回 404，同时模拟创建后草稿在发布列表可见。修改前，新建与已有草稿两种情况都在查询处失败；修改后都进入下载完整性检查，损坏下载仍阻止公开与主分支版本同步。全部 6 项发布测试通过，`git diff --check` 通过。

这是发布工具修复，不改变插件中的排版代码或安装包内容。v0.5.2 标签保持原提交；恢复现有草稿前须将其四个资产与该运行的 `release-bundle` 逐字节核对，再公开并重跑失败的发布 job，以完成原流水线的远端复验与版本同步。恢复结果以标签运行的最新 attempt 与 Release 为准。
