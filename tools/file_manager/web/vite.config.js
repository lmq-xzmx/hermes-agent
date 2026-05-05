// vite.config.js - Vite 开发服务器配置
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue()],
  root: '.',
  base: './',
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // 构建时注入全局变量
  define: {
    __DEV__: JSON.stringify(process.env.NODE_ENV !== 'production'),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    // TASK-006: 构建时注入 API_BASE
    // 策略: 默认使用 /api/v1 (相对路径)
    // - Web dev: Vite proxy 转发到 localhost:8080
    // - Tauri dev: 需要通过 Vite devServer proxy 或配置 Tauri CSP
    // - Vercel/Netlify: rewrite 到真实 API
    // - 生产自部署: 可配置 VITE_API_BASE 环境变量
    __API_BASE__: JSON.stringify(
      process.env.VITE_API_BASE || '/api/v1'
    ),
    // TASK-006: 构建时注入运行模式
    // 使用 'web' 会在运行时通过 window.__TAURI__ 检测真实环境
    __TAURI_MODE__: JSON.stringify('web'),
    // TASK-006: 构建时注入 WebSocket 基础 URL
    __WS_BASE__: JSON.stringify(
      process.env.VITE_WS_BASE || 'ws://localhost:8080'
    ),
  },
  build: {
    outDir: 'dist',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      input: {
        vue: resolve(__dirname, 'vue.html'),
        floating: resolve(__dirname, 'floating-vue.html'),
      },
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'echarts': ['echarts', 'vue-echarts'],
          'marked': ['marked'],
          'api': ['./src/services/api.js'],
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    open: false,
    index: 'vue.html',  // Vue SPA 为默认入口
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})