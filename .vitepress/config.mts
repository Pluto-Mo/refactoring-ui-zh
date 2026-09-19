import fs from 'node:fs'
import path from 'node:path'
import { defineConfig } from 'vitepress'
import { imageSize } from 'image-size'
import type { Plugin } from 'vite'

/**
 * The site is built straight from the repository root, so the chapter files,
 * their relative ``assets/…`` image links and everything in ``tools/`` keep
 * working exactly as they do on GitHub — the website adds no second copy of
 * the translation.
 *
 * Chapter titles are read from the chapter file names, the same source of
 * truth the Python pipeline uses (``tools/chapters.py``), so the navigation
 * cannot drift from the files on disk. The table below carries only the part
 * that is not stored anywhere yet: the English segment of each chapter URL.
 */
const rootDir = process.cwd()

const CHAPTER_FILE = /^(\d\d) (.+)\.md$/

const CHAPTER_SLUGS: Record<string, string> = {
  '01': 'starting-from-scratch',
  '02': 'hierarchy-is-everything',
  '03': 'layout-and-spacing',
  '04': 'designing-text',
  '05': 'working-with-color',
  '06': 'creating-depth',
  '07': 'working-with-images',
  '08': 'finishing-touches',
  '09': 'leveling-up',
}

const chapters = fs
  .readdirSync(rootDir)
  .filter((name) => CHAPTER_FILE.test(name))
  .sort()
  .map((name) => {
    const [, number, title] = CHAPTER_FILE.exec(name) as RegExpExecArray
    const slug = CHAPTER_SLUGS[number] ?? `chapter-${number}`
    return { name, number, title: `${number} · ${title}`, url: `/${slug}/`, out: `${slug}/index.md` }
  })

if (chapters.length === 0) {
  throw new Error(`no chapter file matching "NN 标题.md" was found in ${rootDir}`)
}

const REPO = 'https://github.com/Pluto-Mo/refactoring-ui-zh'

// Published at https://github.mytemos.com/refactoring-ui-zh/ (a project site
// keeps its path under an account-level custom domain). Local dev uses the same
// base on purpose: a link that works locally then works deployed too.
// Set DOCS_BASE=/ when the site is served from a domain root.
const base = (process.env.DOCS_BASE ?? '/refactoring-ui-zh/').replace(/\/?$/, '/')

/**
 * Chapter files carry no H1 on purpose — the title lives in the file name (see
 * ``tools/cleanup_chapters.py``). VitePress does not hand the page path to
 * Markdown renderers, so the heading goes in while the file is still Markdown:
 * that keeps the translation files on disk untouched, puts the title inside the
 * article where ``.vp-doc h1`` styles it, and gets the chapter name into the
 * search index for free.
 */
function chapterTitlePlugin(): Plugin {
  return {
    name: 'refactoring-ui-zh:chapter-title',
    enforce: 'pre',
    transform(code, id) {
      const file = id.split('?')[0].split(/[\\/]/).pop() ?? ''
      const match = CHAPTER_FILE.exec(file)
      if (!match) return
      if (code.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '').trimStart().startsWith('# ')) return
      return { code: `# ${match[1]} · ${match[2]}\n\n${code}`, map: null }
    },
  }
}

/**
 * Intrinsic size of an illustration, so the page can reserve its space before
 * the file arrives. Chapter images are all referenced as ``assets/…`` from the
 * repository root, which is also the site root.
 */
function illustrationSize(src: string) {
  if (!src || /^(?:[a-z][a-z0-9+.-]*:|\/)/i.test(src)) return undefined
  try {
    const { width, height } = imageSize(fs.readFileSync(path.resolve(rootDir, src)))
    return width && height ? { width, height } : undefined
  } catch {
    return undefined
  }
}

export default defineConfig({
  lang: 'zh-CN',
  title: 'Refactoring UI（中文版）',
  description: '《Refactoring UI》中文翻译（非官方）：9 章、284 张插图，按章节在线阅读。',

  // VitePress prefixes page links with `base` itself, but not the entries in
  // `head`, so the icon path is built from it by hand.
  head: [['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}favicon.svg` }]],
  base,

  // tools/ and docs/ are written for translators, README.md for the repository
  // home page; none of them belong in the book.
  srcExclude: ['tools/**', 'docs/**', 'README.md'],

  rewrites: Object.fromEntries([
    ...chapters.map((chapter) => [chapter.name, chapter.out]),
    ['book.md', 'book/index.md'],
    ['NOTICE.md', 'notice/index.md'],
  ]),

  // NOTICE.md links to the plain-text LICENSE file, which is not a site page.
  ignoreDeadLinks: ['./LICENSE'],

  vite: { plugins: [chapterTitlePlugin()] },

  markdown: {
    config(md) {
      const renderImage = md.renderer.rules.image
      if (!renderImage) return
      // 284 illustrations, most of them far below the fold: declare their size
      // (no layout shift while reading) and only fetch what is scrolled into view.
      md.renderer.rules.image = (tokens, idx, options, env, self) => {
        const token = tokens[idx]
        const size = illustrationSize(token.attrGet('src') ?? '')
        if (size) {
          token.attrSet('width', String(size.width))
          token.attrSet('height', String(size.height))
        }
        token.attrSet('loading', 'lazy')
        token.attrSet('decoding', 'async')
        return renderImage(tokens, idx, options, env, self)
      }
    },
  },

  themeConfig: {
    nav: [
      { text: '整本阅读', link: '/book/' },
      { text: '分章阅读', link: chapters[0].url },
      { text: '版权与授权', link: '/notice/' },
      { text: 'GitHub', link: REPO },
    ],

    sidebar: chapters.map((chapter) => ({ text: chapter.title, link: chapter.url })),

    outline: { level: [2, 3], label: '本页目录' },

    search: {
      provider: 'local',
      options: {
        miniSearch: {
          options: {
            // Chinese has no spaces: without segmentation the whole sentence
            // becomes one token and search quietly stops working.
            tokenize: (text: string) => {
              const segmenter = new Intl.Segmenter('zh-CN', { granularity: 'word' })
              return Array.from(segmenter.segment(text))
                .filter((part) => part.isWordLike)
                .map((part) => part.segment)
            },
          },
        },
        locales: {
          root: {
            translations: {
              button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
              modal: {
                displayDetails: '显示详细列表',
                resetButtonTitle: '清除查询条件',
                backButtonTitle: '关闭搜索',
                noResultsText: '没有找到结果',
                footer: {
                  selectText: '选择',
                  selectKeyAriaLabel: '输入',
                  navigateText: '切换',
                  navigateUpKeyAriaLabel: '上箭头',
                  navigateDownKeyAriaLabel: '下箭头',
                  closeText: '关闭',
                  closeKeyAriaLabel: 'esc',
                },
              },
            },
          },
        },
      },
    },

    docFooter: { prev: '上一章', next: '下一章' },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    skipToContentLabel: '跳到正文',
    notFound: {
      title: '页面不存在',
      quote: '这个地址没有对应的章节。',
      linkLabel: '回到首页',
      linkText: '返回首页',
    },
    footer: {
      message: '译文与插图版权归 Adam Wathan 与 Steve Schoger 所有',
      copyright: '站点与工具链采用 MIT 许可',
    },
  },
})
