# Project Mia Frontend

Vue 3 前端应用，提供游戏化学习界面。

## 技术栈

- **框架**: Vue 3
- **构建工具**: Vite 7
- **样式**: Tailwind CSS 4
- **状态管理**: Pinia
- **路由**: Vue Router

## 快速启动

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 端口配置

- 开发端口: 18006
- API 代理: http://127.0.0.1:18005

## 目录结构

```
src/
├── App.vue           # 根组件
├── main.js           # 入口文件
├── style.css         # 全局样式
├── assets/           # 静态资源
├── components/       # 组件
│   ├── Layout.vue    # 布局组件
│   ├── GameHUD.vue   # 游戏 HUD
│   ├── DialogBox.vue # 对话框
│   └── exam/         # 考试相关组件
├── views/            # 页面视图
├── stores/           # Pinia 状态管理
├── router/           # 路由配置
├── config/           # 配置文件
└── utils/            # 工具函数
```

## 主要功能

- 🎮 游戏化学习界面
- 📝 考试系统
- 📚 词汇学习
- 💬 AI 对话 (Mia)
- ❤️ HP/等级系统

## 日志

- Supervisor 日志: /var/log/project-mia-frontend.log

## 注意事项

- 需要 Node.js 20+ (已安装 v20.20.2)
- 开发模式下热更新已启用
