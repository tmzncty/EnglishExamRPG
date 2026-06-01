import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
    allowedHosts: true,  // 允许所有域名访问（Nginx 已做 auth_request 验证）
      host: '0.0.0.0',
      port: 18006,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:18005',
          changeOrigin: true,
          // SSE 流式响应 + AI 批改最长约 35s，给足 3 分钟余量
          timeout: 180000,       // 连接超时 3min
          proxyTimeout: 180000,  // 等待上游响应超时 3min
          // rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
})
