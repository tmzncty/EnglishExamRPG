# Project Mia: 赛博猫娘 AI 考研陪练 🐱🎮✨

> **v3.3 — The SRS Debt Collector Update**
>
> *"Review what you owe, learn only what you can afford."* — Mia

**Project Mia** 是一款结合了 **赛博猫娘人设**、**沉浸式 RPG 体验** 与 **考研英语一真题** 的多模态 AI 辅导系统。
拒绝枯燥的刷题，用 ACG 的灵魂重塑备考体验。

---

## 🌟 核心特性

| 功能          | 说明                                                                        |
| ------------- | --------------------------------------------------------------------------- |
| 🧠 AI 批改引擎 | 翻译 / 写作 由 Gemini 2.0 深度语义打分，1:1 扣血                            |
| 👁️ 多模态视觉  | Writing B 图表题直接识图，无需 OCR                                          |
| 💬 Mia Shell   | SSE 流式对话，带上下文题目记忆，语境感知 AI 讲解                            |
| 🎮 RPG 系统    | HP / EXP / Level 无损溢出升级，支持多存档 (Infinite Slots) 与自定义跨夜时间 |
| 🌱 单词花园    | **True SRS 动态配额**：复习欠债全量偿还，新词坑位按剩余预算动态分配         |
| 🔗 全局联动    | 语境溯源，真题例句一键跨路由无缝跳转至原卷，并调用全局 AI 讲解              |
| � 答题报告    | 考试结束后生成完整答题报告：每题得分、AI 批改评语、正确答案对照             |
| �🔄 二刷机制   | 一键重置当前面板，历史轨迹永久保留                                          |
| � 数据面板    | 全局交叉过滤看板，多维度分析答题数据（省份 / 年份 / 题型）                  |
| 🔴 答题进度条  | 实时显示当前试卷完成度                                                      |

---

## 🚀 快速开始 (Quick Start — 本地部署)

> ✅ 无需 Docker，无需数据库安装，跑起来只需两个终端。

### 1. 克隆项目

```bash
git clone https://github.com/tmzncty/EnglishExamRPG.git
cd EnglishExamRPG/Project_Mia
```

### 2. 后端启动 — The Brain 🧠

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置 AI 密钥（复制模板，填入你的 Key）
cp .env.example .env
# 用任意编辑器打开 .env，填入 GEMINI_API_KEY 或 OPENAI_API_KEY

# 启动服务（首次运行会自动创建 data/femo_profile.db 玩家存档）
python -m uvicorn app.main:app --reload --port 8000
```

> 💡 **首次启动说明**：系统会自动在 `backend/data/` 下生成 `femo_profile.db` 作为你的个人存档数据库，**无需手动建表**，全自动迁移。

### 3. 前端启动 — The Face 🖥️

```bash
# 新开一个终端
cd frontend

npm install
npm run dev
# 默认访问地址：http://localhost:5200
```

### 4. 开始使用！

浏览器打开 `http://localhost:5200`，你会看到：
- **考卷大厅**：历年考研英语一真题卡片，点击"开始"进入答题
- **单词花园**：点击底部"🌱 Garden"导航进入词汇复习
- **Mia 对话**：右下角 Mia 头像，随时唤出 AI 导师

---

## 🛠️ 技术栈

### Frontend
- **Vue 3 + Vite** — 响应式 UI
- **TailwindCSS** — Cyberpunk & Glassmorphism 风格
- **Pinia** — 状态管理（RPG 数据持久化）

### Backend
- **FastAPI** — 高性能异步框架
- **SQLite × 2** — `static_content.db`（题库）+ `femo_profile.db`（玩家存档，不上 Git）
- **AsyncOpenAI** — 兼容 Gemini / DeepSeek / OpenAI 任意 v1 接口
- **Playwright** — E2E 浏览器测试

---

## 📂 数据说明

```
backend/data/
├── static_content.db      ← 题库 (Git 追踪，随代码分发)
├── exam_vocabulary.json   ← 词库 (Git 追踪，随代码分发) #已去除，直接用数据库就行了
└── femo_profile.db        ← 玩家存档 (已加入 .gitignore，绝不上云)
```

> ⚠️ `femo_profile.db` 包含你的 HP、EXP、答题记录和词汇进度，属于个人隐私数据，请勿分享。

---

## 📜 版本历史 (Changelog)

### v3.3 — The SRS Debt Collector Update *(2026-03-08)*

**核心架构升级**

- 🔁 **True SRS 动态配额引擎**（`Stage 35.4`）：
  - 移除复习队列的 `LIMIT 20` 上限，到期词汇**无限全量返还**
  - 动态配额公式：`new_word_quota = max(0, daily_limit - due_reviews)`
  - 复习欠债 > 每日上限时，自动停发新词，先清债务
  - 最终任务列表经由 Seeded Shuffle 稳定混排（复习词 + 新词交错）

**前端修复**

- 🐛 **词汇花园路由修复**：`goToExam` 函数正确生成 `paper_id` 格式，修复跳题空白
- 📜 **例句 overflow 修复**：单词卡正面例句区域添加最大高度 + 滚动条，防止内容溢出
- 💾 **状态持久化**：离开词汇花园后返回页面，当前单词下标正确恢复（不再从头开始）
- ⚠️ **错误反馈**：查题 404 时有 Toast 提示，不再静默失败
- 🔗 **Mia Chat 语境修复**：AI 讲解时正确传递当前题目的例句到提示词

**新功能**

- 📊 **ExamReport 考试报告页**：完成卷子后可查看完整答题报告，包含每题得分、AI 批改内容、正确答案对照
- 🌐 **全局交叉过滤看板**：Dashboard 支持多维度联动筛选（题型 / 年份 / 省份），图表和地图实时响应

---

### v3.2 — Drawing Board & Context Fix *(2026-03-07)*

- ✏️ Drawing Board 画图功能修复（绘图上下文正确传递给 Mia）
- 🧠 Mia Chat 上下文修复：对话时携带当前题目原文
- 🎨 Galgame UI 优化：对话界面视觉调整
- 🔒 `.gitignore` 清理：排除本地开发文件和冗余缓存

---

### v3.1 — Complete Bilingual Story Database *(2026-03-06)*

- 📚 831 道题全部完成中英双语故事补录
- 🌱 单词花园初版上线（SRS 闪卡 + 连击暴击系统）
- 🔗 语境溯源：真题例句一键跳转原卷

---

### v3.0 — AI Galgame Story System *(2026-03-05)*

- 🎭 Galgame 故事系统：每道题结束后触发世界观剧情叙述
- 🎮 RPG 核心系统完整实装（HP / EXP / Level / 多存档）
- ⏰ 自定义跨夜时间（daily_reset_time），不再被强制凌晨重置

---

### v2.0 — The Peaceful Garden *(2026-02-28)*

- 🌱 VocabWeb 独立词汇学习系统（已合并进 Project Mia）
- 📱 多设备协同学习支持
- 🔑 API Key 配置优化

---

### v1.0 — First Release *(2026-02-19)*

- 🏗️ 项目初始化，考卷大厅 + AI 批改引擎 MVP

---

## ☠️ 避坑指南与废案记录

### 1. 幻觉的血量控制
**Case**: 早期让 LLM 直接控制 HP。  
**Result**: 模型经常擅自扣 50 点血。  
**Fix**: LLM 只负责评分，HP 扣减完全由业务层按分数计算。

### 2. SQLite 死锁噩梦
**Case**: `@contextmanager` + async 混用，并发 > 3 时假死。  
**Fix**: 引入 `timeout=20.0`，改用 `async with` 上下文管理器。

### 3. 前端 UI 焦点陷阱
**Case**: `@focus` 自动全选导致提交按钮无法点击。  
**Fix**: 移除自动聚焦，Axios 超时延长至 60s+，增加 loading 遮罩。

### 4. SRS 配额陷阱
**Case**: 复习队列 `LIMIT 20` 导致到期词汇无法全量返还，积攒"隐形债务"。  
**Fix**: 移除 LIMIT，改用动态配额公式，复习欠债 > 每日上限时停发新词。

---

## 📜 License

MIT License. Just don't use Mia to do bad things.
