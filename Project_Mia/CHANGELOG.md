# CHANGELOG

## [v2.0] — The Peaceful Garden Update 🌸 - 2026-03-02

Welcome to the Milestone Release **v2.0 "The Peaceful Garden Update"**.
After an intensive series of refactoring phases (v20.0 to v26.0), Project Mia has been elevated to a robust, pro-level AI-driven spaced repetition and study platform. 

### ✨ 核心亮点 (Key Highlights)

#### 1. 多存档自定义 (Infinite Custom Saves)
- **Unlimited Save Slots:** RPG 系统不再局限于单一进度！新增多存档机制，一键无缝切换不同的备考轮回。
- **Full Customization:** 每个存档可自定存档名称、**每日新词上限 (Daily Limits)** 以及 **自定义跨夜刷新时间 (Custom UTC+8 Reset Time)**。

#### 2. 专业级词汇引擎 (Pro-Level SRS Engine)
- **Database Migration:** 彻底废弃脆弱的本地 JSON 数据源，全面迁移至 SQLite 驱动的坚固词库。
- **Mastery Algorithms:** 引入精确的 Mastery Level (0-7) 与连击暴击系统 (Success Streak)，算法更懂你的记忆曲线。
- **Seamless Leveling:** 修复了溢出经验丢失的问题，现在支持经验值无损向后顺延升级。

#### 3. 诚实反馈机制 (Honest Deferred Grading)
- **Anti-Cheat SRS:** 坚决杜绝假阳性！将“认识/不认识”的评判权力后置于“卡片翻转”之后，只有看完释义，你才能对自己进行诚实打分。一旦撒谎，你就是在欺骗算法。

#### 4. 语境溯源与全局联动 (Context & Exam Routing)
- **Contextual Tracing:** 重新恢复真题原卷例句渲染，背单词不再孤立。
- **Cross-Routing:** 新增 `[🔗 去原卷看看]` 按钮，让你随时可以一键从单词花园穿越到对应真题的上下文中。
- **Global Mia Chat:** 深度整合全局 AI 对话，在单词页面能随时唤出 Mia，针对特定真题例句进行词根词缀和翻译的讲解。

#### 5. 现代化 UI 体验 (Modern Learner UX)
- **Global Dictionary Drawer:** 新增全局 `[📚 我的词库]` 抽屉，内置前端全量搜索与分页，实时观察你对数千个单词的 Mastery 点亮进度。
- **Dynamic ETA:** 词库抽屉加入了人性化的“预计背完天数 (ETA)”计算，结合你的每日上限预估登顶时间。
- **Polished Visuals:** 修复了卡片例句的滚动条溢出问题，大幅加宽并重新设计了更具游戏成就感的 EXP 进度条效果。

#### 6. 全域健壮性 (Rock-Solid Stability)
- **Routing & State:** 修复了无尽的路由 404 死锁问题。
- **Persistence First:** 引入 `pinia-plugin-persistedstate`，即使刷新页面或异常关机，也不会丢失你当前背到一半的词汇进度。
- **Codebase Cleanups:** 大规模的安全审计与仓库瘦身。清理了所有敏感的历史 debug 文件并加强了 `.gitignore` 防护。

---
Enjoy the peaceful garden, User. Keep studying, and don't lose your HP. 🎮🐱
