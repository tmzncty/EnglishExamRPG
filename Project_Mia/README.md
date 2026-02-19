# Project Mia: Cyber-Neko AI Exam RPG 🐱🎮✨

> **v1.0 Core Engine Stabilization Edition**
>
> *"Study, or lose HP. The choice is yours, Master."* — Mia

**Project Mia** 是一款结合了 **赛博猫娘人设**、**沉浸式 RPG 体验** 以及 **考研英语一真题** 的多模态 AI 辅导系统。
我们拒绝枯燥的刷题，用 ACG 的灵魂重塑备考体验。在这里，Mia 不仅仅是 AI，她是你的监考官、导师，也是与你共命运的伙伴。

---

## 🌟 核心特性 (Key Features)

### 🧠 AI 深度批改引擎 (Deep Grading Engine)
告别简单的 "Correct/Wrong"。
- **Translation & Writing**: 基于 **Gemini 2.0 Flash** 的深度语义分析。
- **评分标准**: 严格对照考研评分细则，提供从 0 到 Max 的精准打分。
- **逐句解析**: 哪里写得好，哪里是 Chinglish，Mia 一针见血。

### 👁️ 多模态视觉接入 (Multimodal Vision)
- **Writing Part B 读图**: 直接识别考研英语二/一的小作文/大作文图表。
- **OCR 与 意图识别**: 哪怕是模糊的扫描件，Mia 也能看懂图里的"终点"是在哪里，或者"手机入网"的趋势。

### 💬 Mia Shell (SSE 流式对话)
- **上下文记忆**: Mia 记得你刚刚做错的那道阅读题，和你正在聊天的内容无缝衔接。
- **视觉挂载**: 在对话中直接询问截图内容，Mia 瞬间不仅是聊天机器人，更是视觉助手。
- **SSE 流式响应**: 像真人打字一样，体验极速反馈，拒绝转圈圈。

### 🎮 RPG 状态系统 (Status System)
- **HP 惩罚机制**: 答错扣血，甚至会导致 Game Over（虽然我们还没做 Game Over 界面，但 Mia 会嘲笑你）。
- **持久化存档**: 你的等级、HP、EXP 全部存入 SQLite，刷新网页也能无缝继续。
- **沉浸式 UI**: 动态血条、粒子特效、根据状态变化的 Mia 表情。

---

## 🛠️ 技术栈 (Tech Stack)

### Frontend (The Cyber Interface)
- **Framework**: Vue 3 + Vite
- **Styling**: TailwindCSS (Cyberpunk & Glassmorphism)
- **State Management**: Pinia (Persisted State for RPG logic)
- **Network**: Axios (with specific 10s timeouts for long LLM thoughts)

### Backend (The Neural Core)
- **Runtime**: Python 3.9+
- **Framework**: FastAPI (High performance async framework)
- **Database**: SQLite (Optimized with connection pooling & WAL mode)
- **AI Client**: AsyncOpenAI (Compatible with Gemini/DeepSeek/OpenAI standards)
- **Network**: httpx (Async HTTP client)

---

## 🚀 环境配置与启动 (Getting Started)

### 1. 配置密钥 (`.env`)
在 `backend/` 目录下创建 `.env` 文件：
```ini
AI_PROVIDER=openai
OPENAI_API_KEY=your_sk_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-2.0-flash
```

### 2. 启动后端 (The Brain)
```bash
cd PROJECT_MIA/backend
# 确保安装了依赖: pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端 (The Face)
```bash
cd PROJECT_MIA/frontend
# 确保安装了依赖: npm install
npm run dev
# Access at http://localhost:5200
```

---

## ☠️ 避坑指南与废案记录 (Development History & Scrapped Ideas)

*致那些年我们踩过的坑和为了稳定性牺牲的脑洞。*

### 1. 幻觉的血量控制 (The HP Hallucination)
**Case**: 早期版本中，我们试图让 LLM 直接控制前端 HP。
**Result**: 模型经常发癫，在用户明明答对的时候，因为觉得"你可以做得更好"而强行扣除 10 点 HP。或者在未开启 RPG 模式时，在 JSON 里强行插入 `{ "hp_change": -50 }`。
**Fix**: 前后端严格分离。LLM 只负责评分，HP 扣减逻辑完全由前端/后端业务层根据分数计算，绝不让 AI 碰数据库。

### 2. 500 报错与 SQLite 死锁 (The Deadlock Nightmare)
**Case**: 为了图省事，我们在 FastAPI 的 dependency 里用了 `@contextmanager` 但没有正确处理 `yield` 后的关闭，甚至在 async 函数里混用同步锁。
**Result**: 只要并发超过 3 个，整个后端直接假死，SQLite 抛出 `database is locked`，控制台红成一片。
**Fix**: 引入 `timeout=20.0`，显式重构 DB 连接池，使用 `async with` 上下文管理器，并彻底移除了那个多余的装饰器。

### 3. 前端 UI 假死与焦点陷阱 (The Focus Trap)
**Case**: `SubjectiveInput.vue` 组件为了体验好，加了 `@focus` 自动全选。
**Result**: 甚至不需要点击，只要组件渲染，它就疯狂抢焦，导致用户根本无法点击提交按钮。配合 Axios 默认的短超时，用户刚写完作文点击提交，前端直接因为响应超时把连接断了，而后端还在傻傻地生成评分。
**Fix**: 移除了所有自动聚焦，Axios 超时延长至 60s+（为了等待思维链模型），并增加了 loading 遮罩层防止用户乱点。

---

## 📜 License
MIT License. Just don't use Mia to do bad things.
