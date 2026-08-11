export default defineNuxtConfig({
  compatibilityDate: '2026-08-11',
  devtools: { enabled: true },
  modules: ['@nuxt/eslint'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/v1',
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'ko' },
      meta: [
        { name: 'theme-color', content: '#173c36' },
        {
          name: 'description',
          content: '레버 한 번으로 오늘의 점심을 결정하는 개인화 추천기',
        },
      ],
    },
  },
})

