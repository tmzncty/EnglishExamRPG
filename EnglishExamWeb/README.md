# 英语考试 RPG - ACG & AI Enhanced Edition

## 📌 项目概述

一个**二次元风格**的考研英语真题练习应用。将枯燥的刷题过程**游戏化**，并集成 **Google Gemini AI** 提供智能化的私教级辅导。

本项目完全**开源**，支持**纯前端运行**（GitHub Pages 友好），数据存储采用 **BYOC (Bring Your Own Cloud)** 模式，保障用户数据隐私与主权。

---

## ✨ 核心特性

### 1. 🎮 游戏化体验 (Gamification)
*   **RPG 升级系统**: 答题获得经验值 (EXP)，提升等级，解锁不同称谓（从"四级萌新"到"传说考生"）。
*   **HP 机制**: 答错扣血，模拟考试紧张感。
*   **ACG 视觉风格**: 精美的粉紫渐变 UI，Galgame 风格对话框。
*   **Phosphor Icons**: 全新引入的圆润可爱图标库，提升界面质感。

### 2. 🤖 AI 智能私教 (Gemini 2.0)
*   **流式输出 (Streaming)**: AI 解释单词和长难句时，文字像打字机一样实时流出，无需漫长等待。
*   **划词详解**: 在阅读文章时，选中任意单词或句子，AI 即刻提供释义、语法分析和例句。
*   **主观题批改**: 智能评分翻译和写作题，提供参考范文和改进建议。
*   **BYOK 模式**: 用户填入自己的 Google Gemini API Key，直接与 Google 服务器通信，无中间商赚差价。

### 3. ☁️ 多端同步 (WebDAV)
*   **数据主权**: 不依赖开发者服务器，使用你自己的网盘（如坚果云、Nextcloud）同步进度。
*   **跨设备无缝切换**:
    *   📱 **手机端**: 利用碎片时间背单词、刷小题。
    *   💻 **PC 端**: 沉浸式做整套试卷、阅读长难句。
*   **离线优先**: 支持本地 JSON 存档导入/导出。

### 4. 📚 完备的刷题功能
*   **全题型支持**: 完形填空、阅读理解、新题型、翻译。
*   **单词本系统**: 遇到生词一键收藏，支持 AI 辅助记忆。
*   **错题回顾**: 自动记录错题，随时复习。
*   **响应式布局**: 完美适配桌面端和移动端。

---

## 🛠️ 技术栈

*   **核心**: HTML5, CSS3, Vanilla JavaScript (ES6+)
*   **图标库**: [Phosphor Icons](https://phosphoricons.com/)
*   **AI 模型**: Google Gemini API (REST)
*   **数据存储**: LocalStorage + WebDAV
*   **构建**: 无需构建，静态文件直接运行

---

## 🚀 快速开始

### 方式一：直接运行 (推荐)
1.  下载本项目代码。
2.  使用 VS Code 的 "Live Server" 插件打开 `index.html`。
3.  在设置中填入你的 Gemini API Key。

### 方式二：部署到 GitHub Pages
1.  Fork 本仓库。
2.  在仓库 Settings -> Pages 中选择 `main` 分支。
3.  访问生成的网址即可使用。

---

## ⚙️ 配置指南

### 1. 获取 Gemini API Key
前往 [Google AI Studio](https://aistudio.google.com/) 免费申请 API Key。

### 2. 配置 WebDAV 同步 (以坚果云为例)
1.  登录坚果云网页版，进入"账户信息" -> "安全选项"。
2.  添加一个"第三方应用管理"，生成应用密码。
3.  在本项目设置中填入：
    *   **服务器地址**: `https://dav.jianguoyun.com/dav/`
    *   **账号**: 你的坚果云注册邮箱
    *   **密码**: 刚才生成的应用密码
4.  点击"上传进度"或"下载进度"即可同步。

---

## 📁 项目结构

```
EnglishExamWeb/
├── index.html              # 主入口
├── css/
│   ├── style.css           # 基础样式
│   └── theme-acg.css       # ACG 主题样式
├── js/
│   ├── app.js              # 核心逻辑
│   ├── gemini-service.js   # AI 服务 (含流式处理)
│   ├── storage-manager.js  # 存档与 WebDAV 同步
│   ├── ui-effects.js       # UI 交互与特效
│   ├── vocab-ui.js         # 单词本 UI
│   └── vocabulary-manager.js # 单词数据管理
├── data/
│   └── 2010.json           # 真题数据
└── assets/                 # 静态资源
```

## 📝 更新日志

### v1.1 (2024-12-02)
*   ✨ **新增**: 嵌入式 PDF 官方解析查看器，做完题目可直接查看原版官方解析。
*   ✨ **新增**: AI 解析本地缓存功能，相同题目只需调用一次 API，大幅节省成本。
*   ✨ **新增**: 响应式三栏布局，大屏用户可同时查看题目、文章和解析。
*   🐛 **修复**: 2015/2022 年 Writing Part B (Q52) 图片无法显示的问题。
*   🎨 **优化**: 强制使用系统中文字体（Microsoft YaHei/PingFang SC），解决部分设备字体乱码。
*   🎨 **优化**: 移动端响应式布局优化，解析面板自适应屏幕大小。

### v1.0 (2024-12-01)
*   ✨ **新增**: WebDAV 云同步功能，支持多端进度互通。
*   ✨ **新增**: AI 解释单词支持流式输出 (Streaming)，体验更丝滑。
*   🎨 **优化**: 全面替换为 Phosphor Icons 图标库。
*   🗑️ **移除**: 移除了 Live2D 看板娘功能（因兼容性问题及精简需求）。

---

**Enjoy Learning!** 🌟
