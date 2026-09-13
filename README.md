# Refactoring UI（中文版）

《Refactoring UI》— Adam Wathan & Steve Schoger 著 — 的中文翻译，按章节拆分存放。

原书面向**开发者**：会写代码、想让自己做出来的界面变好看，但没有设计背景。

## 目录结构

```
.
├── 01 从零开始.md
├── 02 层级就是一切.md
├── 03 布局与间距.md
├── 04 文字设计.md
├── 05 色彩的运用.md
├── 06 营造层次感.md
├── 07 图片的运用.md
├── 08 收尾打磨.md
├── 09 持续进阶.md
├── index.md           网站首页
├── assets/            原书插图（284 张）
├── tools/             PDF → Markdown → 中文译文 的完整工具链
├── docs/
│   └── 翻译规范与术语表.md
├── .vitepress/        VitePress 站点配置与主题
├── .github/workflows/ GitHub Pages 自动部署
├── package.json       站点构建依赖（包管理器为 pnpm）
├── pnpm-lock.yaml     锁文件
├── pnpm-workspace.yaml pnpm 设置（允许 esbuild 的 postinstall）
├── LICENSE            MIT，仅覆盖原创代码（tools/、docs/、README）
└── NOTICE.md          译文与插图的版权归属
```

每章一个文件，正文中的图片用相对路径 `assets/xxx.png` 引用，直接在仓库里预览即可正常显示。

## 在线阅读（网站）

仓库根目录同时是一个 VitePress 站点：章节文件、图片和工具链都留在原处，网站只是多了一层渲染，不产生第二份译文。

```bash
pnpm install
pnpm dev      # http://localhost:5173/refactoring-ui-zh/
pnpm build    # 产物在 .vitepress/dist
pnpm preview  # 用本地服务器预览构建产物
```

包管理器是 pnpm（版本写在 `package.json` 的 `packageManager` 字段里，用 Corepack 可直接 `corepack enable`）。

- 线上地址是 `https://<用户名>.github.io/refactoring-ui-zh/`，所以站点默认带 `base: /refactoring-ui-zh/`，本地开发也走同一个前缀，免得出现「本地能跑、线上 404」。换成自定义域名时用 `DOCS_BASE=/` 构建。
- 章节的标题和顺序直接来自文件名，和 `tools/chapters.py` 是同一份事实；只有章节 URL 的英文段写在 `.vitepress/config.mts` 的 `CHAPTER_SLUGS` 里。
- 章节正文不含 H1（见 `tools/cleanup_chapters.py`），站点渲染时按文件名补回标题，Markdown 文件保持工具链产出的原样。
- 推送到 `main` 由 `.github/workflows/deploy-pages.yml` 自动构建发布；首次需要在仓库 Settings → Pages 里把 Source 设为 GitHub Actions。
- `tools/`、`docs/` 和 `README.md` 不发布到站点（见 `srcExclude`），它们只服务翻译流程。

## 翻译说明

- 由机器翻译流程生成：先按章拆分，再分章翻译，全程使用统一的术语表（hierarchy → 层级、
  white space → 留白、shade → 色阶、depth → 层次感 等），最后做全书一致性与结构校对。
- Markdown 结构与原书逐段对应，标题层级、列表项数量、图片位置均与原书一致。
- 界面示例文案、字体名、产品名保留英文原样。

## 工具链

`tools/` 里是这次翻译用到的全部脚本，从 PDF 一直走到中文 Markdown：

```bash
pip install pymupdf

python tools/pdf_to_markdown.py input.pdf -o out/ --name "Refactoring UI"   # PDF → Markdown + assets/
python tools/split_markdown.py --book "out/Refactoring UI.md" --out-en work/en --out-zh work/zh
# ... 按 docs/翻译规范与术语表.md 分章翻译 ...
python tools/verify_translation.py --en work/en --zh work/zh               # 结构一致性校验
python tools/cleanup_chapters.py --dir work/zh                             # 去掉 h1 与页码注释
python tools/merge_book.py --dir work/zh                                   # 可选：合成单文件
```

详见 [tools/README.md](tools/README.md)。脚本本身是通用的，换一本排版类似的 PDF 只需调整
`pdf_to_markdown.py` 顶部的字号阈值。

**工具链不包含原书 PDF 和英文全文**，跑通它需要你自己准备源文件。

## 版权声明

本仓库的材料分两类，授权状态不同，详见 [NOTICE.md](NOTICE.md)：

**译文与插图** —— 版权归原作者 **© Adam Wathan & Steve Schoger**，保留所有权利。
中文译文是个人学习用途的非官方翻译，`assets/` 的插图来自原书，本仓库对二者**不授予任何许可**。
请通过 <https://www.refactoringui.com/> 购买正版；原作者或权利人若提出移除请求，我们会照办。

**工具链与文档** —— `tools/` 的脚本和 `docs/`、`README.md`，是为本仓库原创的内容，
采用 [MIT 许可证](LICENSE)，**Copyright (c) 2026 Jeffrey Chen**。

许可证只能由权利人授予。译文和插图的版权在原作者手里，本仓库无权对它们授权，
所以没有一份覆盖全仓库的统一许可证——`LICENSE` 开头写明了它只适用于原创代码。
