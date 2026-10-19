# Recto · 课程讲义与国标正文

本目录是已冻结的设计原型，用于追溯用户选定版式；后续排版与维护使用 [Recto skill](../../../skills/recto/SKILL.md)。这里的样式快照不与正式实现同步。

原型保留两套 Typst 样式。清爽课程讲义为用户已选定版本；国标正文为新样张。此前另外三个探索方向的源代码分支、PDF、预览和旧检查产物均已删除。

| 样式 | 用途 | 主要参数 | 样张 |
| --- | --- | --- | --- |
| 清爽课程讲义 | 数学与中英文课程材料 | A4；12pt 宋体 / Times；18pt 基础行距；上下 12mm；底部居中页码 | 4 页，Taylor 近似与误差估计 |
| 国标正文 | 参照 GB/T 9704-2012 的文字、表格、附件 | A4；156 × 225mm 版心；三号仿宋；二号小标宋；国标单双页页码 | 5 页，正文层次、纵表、附件和单双页横表 |

对比页为 `index.html`。数字键 1、2 或左右方向键切换样式，顶部按钮切换页码；图片全部来自最终 PDF 的渲染。`?v=1` 对应课程讲义，`?v=2` 对应国标正文。刷新已打开的页面即可加载更新。

## 文件

- `specimen.typ`：课程讲义样文，使用 `styles/reference.typ`。
- `gbt9704.typ`：国标正文样文，使用 `styles/gbt9704.typ`。
- `reference-style.md`：课程讲义的字体、尺寸与参考关系。
- `gbt9704-style.md`：国标条款与本次实现范围。
- `output/pdf/`：两套最终 PDF。
- `output/recto-book-styles.zip`：上述源文件、PDF、预览、脚本与说明的完整包。

原型阶段交付的是模板及样张；正式 skill 现位于 `skills/recto/`。默认忠实排版：给定正文时保留原意、公式和论证；当前样文为展示版式而原创，未改写或拼接参考文件正文。

## 重建

使用 Typst 0.15.1。字体不随文件分发，需在本机安装：

- 讲义：Songti SC、Times New Roman、New Computer Modern Math。
- 国标正文：FZFangSong-Z02、FZXiaoBiaoSong-B05、FZHei-B01、FZKai-Z03、SimSun。
- 缩略图标签：Noto Sans CJK SC；可用 `PREVIEW_FONT` 指定替代字体路径。

```sh
typst compile specimen.typ output/pdf/reference.pdf
typst compile gbt9704.typ output/pdf/gbt9704.pdf
```

完整重建：

```sh
sh build.sh
python3 verify_artifacts.py
python3 preview.py
python3 package.py
```

`build.sh` 使用 Poppler 生成预览与检查数据；Python 依赖 Pillow、pdfplumber、pypdf。验证脚本会生成独立的 22 行 × 28 字测试页，位于 `.qa/gbt9704/`，不放入成品包。讲义引用的 SVG 已生成，重编译不依赖 Matplotlib。

## 本轮验证

2026-10-19：新国标样张全部 5 页已查看；讲义 4 页与选定版本逐页进行像素比较，全部一致。

- 两套 PDF 均无编译诊断，字体全部嵌入，关键正文存在，无页面外文字。
- 国标版验证了 A4 和版心、四级字体与缩进、标题居中、附件标题第三行、连续页码、一字线距版心下缘 7mm，以及横排表格单双页朝向。
- 纯中文测试页为 22 行，每行 28 字。含标题、表格的页面按实际内容排布，不强行声称每页都等于 22 行正文。
- 对比页完成脚本静态语法检查，嵌入图片与最终渲染逐页比对。浏览器工具的 `file://` 访问限制仍存在，本轮未做浏览器交互复验或自动刷新。
- 这不是纸张、实体印刷装订或百页长文的验收。国标版按用户范围提供正文、表格和附件，不加入红头、署名、日期、印章或版记。

打包时只收录两套样式；参考 PDF、本机字体、历史快照和测试页面均不随包分发。
