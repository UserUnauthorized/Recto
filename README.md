# Recto · 文档 Skills

用于中英文数学讲义、教材和正式文字材料的排版 skills。给出 Markdown、正文或资料，由 skill 完成排版，交付 **Typst 源文件、PDF 和可编辑 Word**。

当前提供 [Recto](skills/recto/SKILL.md) 一个 skill、两套风格。生成内容时按需配图和去 AI 腔；转换已有内容时保留原文、公式、标题和编号。以后新增文档 skill 放在各自的 `skills/<name>/` 中。

## 两套风格预览

下图来自当前 skill 自带样例导出的 PDF，点击图片可查看原尺寸。

<table>
  <tr>
    <th width="50%">清爽课程讲义 · reference</th>
    <th width="50%">国标正文 · gbt9704</th>
  </tr>
  <tr>
    <td><a href="docs/recto/previews/reference.png"><img src="docs/recto/previews/reference.png" width="420" alt="清爽课程讲义首页：中英文标题、宋体正文、Taylor 公式、脚注和底部页码"></a></td>
    <td><a href="docs/recto/previews/gbt9704.png"><img src="docs/recto/previews/gbt9704.png" width="420" alt="国标正文首页：小标宋标题、仿宋正文、四级标题层次和外侧页码"></a></td>
  </tr>
  <tr>
    <td>A4，12pt 宋体与 Times，中英文和数学混排，上下 12mm，底部居中页码。</td>
    <td>A4，三号仿宋，二号小标宋标题，国标正文边距和单双页页码；不含红头和署名。</td>
  </tr>
</table>

讲义风格适合课程笔记、数学教材和复习资料；国标风格适合正文、表格、附件／附录。完整参数见 [版式约定](skills/recto/references/styles.md)。

## 安装到 Codex

以下终端命令适用于 macOS／Linux，需要 Git 和 Python 3.10+。安装 skill 与安装排版引擎是两步；本节只安装 skill。

```sh
git clone https://github.com/UserUnauthorized/Recto.git
cd Recto
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/skills.py check recto
python scripts/skills.py install recto --dest "$HOME/.agents/skills"
```

上面显式安装到 Codex 的用户技能目录 `~/.agents/skills/recto/`。安装后在 Codex 中提及 `$recto` 即可调用；未出现时重启客户端。技能目录与调用方式见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。

**已有安装时沿用原目录。** 本仓库安装脚本未传 `--dest` 时使用 `$CODEX_HOME/skills`，未设置则使用 `~/.codex/skills`；这是已有本地安装的默认路径。若之前安装在这里，把上面及更新命令的 `--dest` 改为原目录，避免出现两份同名 skill。也可用 `--dest /path/to/skills` 指定其他技能目录。

### 更新

在克隆的仓库目录中执行；`--dest` 必须与首次安装一致：

```sh
git pull --ff-only
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/skills.py check recto
python scripts/skills.py install recto --dest "$HOME/.agents/skills" --replace
```

内容相同则不改动。已有版本不同时，不带 `--replace` 会停止；带上后先将旧版保存到本仓库的 `output/install-backups/`，再整体更新。修改始终回到 `skills/`，然后重新安装。

## 准备排版依赖

首次生成文档前，需要让导出进程找到下列依赖。项目当前验证版本为 Pandoc **3.9.0.2**、Typst **0.15.1**；升级后可用下方样例检查。

| 依赖 | 用途与安装 |
|---|---|
| Pandoc | 将共同 Markdown 转为 Typst 与 DOCX；[安装说明](https://pandoc.org/installing.html) |
| Typst CLI | 编译 PDF、检查本地字体；[安装说明](https://github.com/typst/typst#installation) |
| Python：`python-docx`、`lxml` | 导出脚本处理 Word 的样式、原生公式和表格 |
| 对应字体 | 见下表；安装到系统字体目录，或通过 `TYPST_FONT_PATHS` 指向字体目录 |

macOS 已安装 Homebrew 时，可运行：

```sh
brew install pandoc typst
pandoc --version
typst --version
```

手动运行导出脚本时，在已激活的 `.venv` 中补充 Python 依赖：

```sh
python -m pip install python-docx lxml
```

在 Codex 桌面环境中，skill 优先使用工作区依赖加载器提供的 Python。上面的 `.venv` 供仓库管理和手动导出使用，不会自动替换 Codex 的捆绑运行时。

| 风格 | 所需字体名称 |
|---|---|
| `reference` | `Songti SC`、`Times New Roman`、`New Computer Modern Math` |
| `gbt9704` | `FZFangSong-Z02`、`FZXiaoBiaoSong-B05`、`FZHei-B01`、`FZKai-Z03`、`SimSun` |

用 `typst fonts` 检查字体是否被识别。字体不随仓库分发，需自行准备；缺少字体时导出器会报错，不静默替换。更换字体需要调整样式并重新核对分页。通过 `TYPST_FONT_PATHS` 提供的目录只保证 Typst 可读；Word／LibreOffice 仍需能访问相应字体。

## 使用方式

安装后把文件或正文交给 Codex，并说明用途和需要的格式。无需手写 Typst。

**原样转换为 PDF 和 Word：**

```text
用 $recto 把这份 Markdown 原样排成 PDF 和 Word，采用清爽课程讲义样式。
保留原文、公式和编号，同时交付 Typst 源文件。
```

**按国标正文排版：**

```text
用 $recto 的 gbt9704 样式排版这份材料，导出 PDF 和 Word。
只保留文字、表格和附录，不要红头和署名。
```

**根据资料生成内容：**

```text
用 $recto 根据这些资料写一份 Taylor 公式复习讲义，面向大学一年级学生。
采用清爽课程讲义样式，补充例题；有助于解释方法选择时加入流程图。
导出 Typst、PDF 和 Word。
```

**只改指定部分：**

```text
用 $recto 排版这份讲义，只把第 3 节改得更好懂，并给该节算法加流程图。
其他部分保持原样，导出 PDF。
```

纯转换不启用扩写、补充研究、自动配图或去 AI 腔改写；只有明确要求生成／改写的范围才启用这些步骤。默认交付 `.typ` 和 `.pdf`，要求 Word 时增加 `.docx`。

### 不通过对话，直接运行样例

在仓库根目录、激活 `.venv` 并备齐上述依赖后执行：

```sh
python skills/recto/scripts/export.py skills/recto/assets/examples/reference.md \
  --style reference --formats typ,pdf,docx --output output/recto/demo-reference

python skills/recto/scripts/export.py skills/recto/assets/examples/gbt9704.md \
  --style gbt9704 --formats typ,pdf,docx --output output/recto/demo-gbt9704
```

换成自己的 Markdown 路径即可排版。只需 Typst 与 PDF 时，将 `--formats` 改为 `typ,pdf`。输入语法、公式、图片、显式分页和附录写法见 [源文件与导出](skills/recto/references/export.md)。

输出目录包含：

| 文件 | 作用 |
|---|---|
| `document.typ` | 已内嵌样式的 Typst 源文件，可编辑、重新编译 |
| `document.pdf` | 固定版面的阅读与打印版本 |
| `document.docx` | 选择 `docx` 时生成；文字、公式和普通表格可编辑 |
| `content.md`、`assets/` | 整理资源路径后的共同源与所需图片；无图片时没有 `assets/` |
| `source-and-exports.zip` | 源文件与所选成品的完整包 |
| `export-report.json` | 源哈希、输出清单和数学数量；不代表已完成视觉检查 |

三种输出共用 Markdown 源，不从 PDF 反转生成 Word。Word 的换行、分页和数学字体可能与 PDF 不同；国标横表在 PDF 中旋转排入纵向纸张，在 Word 中使用横向节。编译后仍需逐页检查；已有 DOCX 样张经 LibreOffice 渲染核验，原生 Microsoft Word 尚未实测。国标风格只覆盖正文相关版式，不是完整机关公文认证。

## 仓库维护

```text
skills/<name>/     可安装的 skill；唯一的正式源文件
scripts/skills.py  检查、打包与本地安装入口
checks/<name>/     维护者使用的行为检查场景，不随 skill 安装
docs/<name>/       设计依据、精选预览、决策与验证记录
archive/<name>/    已冻结的设计原型，不参与正式打包
output/<name>/     本地导出、渲染与试验产物，忽略版本控制
dist/             可分发安装包，忽略版本控制
```

```sh
python scripts/skills.py list
python scripts/skills.py check
python scripts/skills.py package recto  # dist/recto-skill.zip
```

`check` 只检查元数据、skill 内相对链接和 Python 语法。改动导出脚本、模板或字体后，要运行真实样例并逐页检查受影响格式。精选 README 预览保存在 `docs/recto/previews/`；其余大体积渲染、转换探针与缓存留在 `output/`。必要输入样例、图片和模板随 skill 保留。

- [维护约定](AGENTS.md)与[行为检查场景](checks/recto/scenarios.md)
- [引擎决策](docs/recto/adr/0001-typst-first.md)与[版式参数](skills/recto/references/styles.md)
- [已完成的导出验证](docs/recto/validation/2026-10-19-exports.md)
- [原型归档](archive/recto/book-styles/README.md)
