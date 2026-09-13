# 工具链

把一本排版规整的英文 PDF 变成「每章一个 Markdown 文件 + assets/ 图片」的中文译文，用到的脚本都在这里。

这些脚本是为《Refactoring UI》这份 PDF 写的，但除了 `chapters.py` 里的章节名和
`pdf_to_markdown.py` 里的字号阈值之外，没有别的硬编码内容，换个排版结构类似的 PDF 改一改就能用。

## 依赖

```bash
pip install pymupdf
```

Python 3.9 以上。脚本之间通过 `chapters.py` 共享章节文件名，避免同一份列表在多个文件里各写一遍。

## 流程

### 1. PDF → Markdown + assets

```bash
python pdf_to_markdown.py input.pdf -o out/ --name "Refactoring UI"
```

产出 `out/Refactoring UI.md` 和 `out/assets/`。要点：

- 文字按字号分类成章标题（28pt）、节标题（22pt）、小标题（12pt）、正文（10pt），页眉页码（8pt）直接剔除
- 图片按在页面上的纵向位置与正文交错插入，**原样提取嵌入的图片流**，不重新渲染、不重新压缩
- 段落按行间距切分（超过 19pt 视为新段落），跨页断开的段落会自动合并，行尾连字符按原样保留
- 印刷版目录页自动跳过（用点线引导符识别）

```bash
python pdf_to_markdown.py input.pdf -o out/ --pages 8-30   # 先跑十几页试效果
```

### 2. 按章拆分

```bash
python split_markdown.py --book out/Refactoring\ UI.md --out-en work/en --out-zh work/zh
```

每个一级标题一个文件，文件名取自 `chapters.py`。`--out-zh` 会顺便把 `assets/` 复制过去，
这样分章文件和图片的相对路径就是对的。

### 3. 翻译

这一步没有脚本，是把每章英文源文件分发给译者（人或 agent），配上一份统一的
[翻译规范与术语表](../docs/翻译规范与术语表.md)，各自产出 `work/zh/NN 章节名.md`。

分章并行翻译能大幅提速，但**跨章的用词一致完全依赖术语表**——所以术语表要在开译前定好，不能边翻边补。

### 4. 结构校验

```bash
python verify_translation.py --en work/en --zh work/zh
```

逐章比对二级标题、三级标题、图片引用、段落数、列表项数，必须完全一致；另外检查全书里
相互竞争的译法（比如「留白/空白」「色阶/色调」有没有混用）和残留的未翻译英文段落。

一级标题和页码注释只作为参考信息列出——它们在成品里会被下一步删掉。

### 5. 清理（可选）

```bash
python cleanup_chapters.py --dir work/zh --dry-run   # 先看会改什么
python cleanup_chapters.py --dir work/zh
```

删掉每章开头的一级标题（章节名已经在文件名里）和正文中的 `<!-- pN -->` 页码注释，
并压掉因此产生的多余空行。

### 6. 合并（可选）

```bash
python merge_book.py --dir work/zh --cover assets/p001-01.png
```

把 9 章拼成一个文件，目录从章节文件实时生成，保证标题措辞和正文一致。不需要单文件版就不用跑。

## 关于 `pdf_to_markdown.py` 的阈值

顶部这几个常量是按这本书的排版定的，换 PDF 时先改这里：

```python
HEADER_SIZE = 8.0      # 页眉页码字号
HEADER_BAND = 60.0     # 页眉所在的纵向区间（pt）
CODE_MAX_SIZE = 8.5    # 等宽代码字号上限
H3_MIN_SIZE = 11.5     # 小标题
H2_MIN_SIZE = 18.0     # 节标题
H1_MIN_SIZE = 24.0     # 章标题
PARA_GAP = 19.0        # 超过这个行距（pt）就算新段落
```

调阈值之前建议先做一次结构探查：把每页的 fontSize、字体名、y 坐标导出来看一眼，
确认标题层级和页眉能用字号区分开。排版是单栏、图片是独立块、字体层级规整的 PDF 效果最好；
多栏排版、公式、扫描件不在这个脚本的适用范围里，那种情况更适合 BabelDOC 一类的工具。
