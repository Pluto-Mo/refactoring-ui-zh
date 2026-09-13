import { h, nextTick, onMounted, watch } from 'vue'
import mediumZoom from 'medium-zoom'
import DefaultTheme from 'vitepress/theme'
import { useRoute } from 'vitepress'
import cover from '../../assets/p001-01.png'
import './custom.css'

export default {
  extends: DefaultTheme,

  Layout() {
    return h(DefaultTheme.Layout, null, {
      'home-hero-image': () =>
        h('img', { class: 'book-cover', src: cover, alt: '《Refactoring UI》封面' }),
    })
  },

  setup() {
    const route = useRoute()
    let zoom: ReturnType<typeof mediumZoom> | undefined

    // The book is 284 screenshots of UI details; being able to click an
    // illustration open is the difference between readable and not.
    const attachZoom = () => {
      zoom?.detach()
      zoom = mediumZoom('.vp-doc img:not(.book-cover)', {
        background: 'var(--vp-c-bg)',
        margin: 24,
      })
    }

    onMounted(attachZoom)
    watch(() => route.path, () => nextTick(attachZoom))
  },
}
