---
title: 引用与代码排版示例
subtitle: 可点击的证据索引与可编辑代码
---

# 1. 字段与命令

字段 `installation_id`、中文值 `关闭遥测` 使用行内代码。结论的来源见 [\[S1\]](#source-s1)，格式说明见 [\[S2\]](#source-s2)。

代码中的直引号、下划线、百分号与反斜线保留：`a_b="50%" # {x} ~ ^ \path`。

```bash
example telemetry disable
example telemetry status
```

# 2. 数据与源码摘录

以下数据和代码仅用于展示排版，不代表真实采集记录。

```json
{
    "enabled": false,
    "message": "关闭遥测",
    "users": []
}
```

摘录的起始行号为 354；可再次点击 [\[S1\]](#source-s1) 查看来源位置。

```{.python .numberLines startFrom="354"}
def snapshot(users):
    # 保留中文与四空格缩进
    return {"users": users}
```

没有语言标记的内容仍按代码排版，不作为命令执行：

```
literal = "a  b"
\end{verbatim} \input{not-a-file} ^^41
```

| 字段 | 含义 |
|---|---|
| `current_user_count` | 当前用户数 |
| `message` | `中文值` |

::: pagebreak
:::

# 3. 证据索引

[S1]{#source-s1} 示例文件 `src/example.py`，第 354–356 行；仅演示材料内相对定位，没有虚构公开源码链接。

[S2]{#source-s2} [Pandoc 用户手册](https://pandoc.org/MANUAL.html)，关于链接和代码块的格式说明。
