# VocabWeb - 智能词汇学习系统

> 基于遗忘曲线的考研英语词汇学习 Web 应用，采用 ACG 风格设计。

**这是 [EnglishExamRPG](https://github.com/tmzncty/EnglishExamRPG) 项目的词汇学习子系统。**

完整文档请查看：[主 README](../README.md)

---

## ⚡ 快速开始

### 直接使用（推荐）

```bash
# 在项目根目录启动服务器
python -m http.server 8080

# 访问 http://localhost:8080/VocabWeb/
```

**首次访问会自动加载预构建数据库（6131 个单词，1882 条例句）**

### 重新生成数据（可选）

```bash
# 1. 从真题中提取词汇
python extract_vocab.py

# 2. 预构建数据库
python prebuild_database.py
```

---

## ✨ 核心功能

### 1. 智能记忆算法 🧠
- **SuperMemo 2** 间隔重复算法
- 根据答题质量动态调整复习间隔
- 科学的遗忘曲线管理

### 2. 智能错题本 📋
- 答错自动进入错题本
- 连续答对 **3 次**才移出
- 错题自动混入每日学习（占比 20%）
- 实时追踪连续正确次数

### 3. AI 智能讲解 🤖
- **Gemini 2.0 Flash** 驱动
- 自动缓存讲解（节省 API 成本）
- 提供词根词缀、记忆技巧、常见搭配
- 离线也能查看已缓存的讲解

### 4. 真题语境学习 📚
- 所有例句来自 2010-2025 年考研真题
- 包含年份、题型、section 等元数据
- 学以致用，印象深刻

### 5. 灵活学习计划 📅
- 可设置每日最低目标（5-100 词）
- 支持超额完成（可多学不可少学）
- 自定义学习提醒
- 上一题回顾功能

---

## 📊 数据统计

- ✅ **6131 个单词**
- ✅ **1882 条真题例句**
- ✅ 完整题目元数据
- ✅ 预构建数据库 1.19 MB

---

## 🎯 使用流程

```
打开 index.html
    ↓
系统自动加载预构建数据库
    ↓
查看真题例句
    ↓
从 4 个选项中选择正确释义
    ↓
查看答案 → AI 讲解（可选）
    ↓
上一题 / 下一题
    ↓
完成每日目标 → 查看统计
```

---

## ⚙️ 设置选项

点击右上角"⚙️ 设置"按钮：

- **每日新词数量**：5-100 个（最低目标，可多学）
- **睡眠时间**：一天结束的时间点
- **学习提醒**：启用/禁用浏览器通知
- **提醒时间**：每日提醒时间
- **Gemini API Key**：AI 讲解功能（可选）

---

## 📖 错题本机制

```
第1次: 答错 → 进入错题本 (连续正确: 0/3)
第2次: 答对 → 仍在错题本 (连续正确: 1/3)
第3次: 答对 → 仍在错题本 (连续正确: 2/3)
第4次: 答对 → 移出错题本 ✅ (连续正确: 3/3)

注意：中途答错会重置计数器
```

---

## 🛠️ 技术栈

- **前端**: 纯原生 JavaScript（无框架）
- **数据库**: SQL.js（浏览器端 SQLite）
- **AI**: Gemini 2.0 Flash Exp
- **存储**: LocalStorage（完全本地化）
- **算法**: SuperMemo 2 间隔重复算法

---

## 🔧 常见问题

### Q: 数据加载失败？
```javascript
// 在浏览器控制台执行
localStorage.clear()
// 刷新页面
```

### Q: AI 讲解不工作？
1. 检查 API Key 是否正确
2. 确认网络能访问 Google API
3. 查看浏览器控制台错误信息

### Q: 如何清空错题本？
在设置中点击"清空数据库"（⚠️ 会删除所有学习记录）

---

## 📁 项目文件

```
VocabWeb/
├── index.html              # 学习界面
├── import_data.html        # 数据导入工具（已弃用）
├── css/
│   └── style.css           # 样式文件
├── js/
│   ├── app.js              # 主应用逻辑
│   ├── db.js               # 数据库操作
│   ├── ai-service.js       # AI 服务
│   └── learning-algorithm.js  # 记忆算法
├── data/
│   ├── exam_vocabulary.json    # 词汇源数据
│   └── vocab_prebuilt.txt      # 预构建数据库
├── extract_vocab.py        # 从真题提取词汇
└── prebuild_database.py    # 生成预构建数据库
```

---

## 📝 更新日志

### v2.0 (2025-12-13)
- 🎉 正式发布
- ✨ 智能错题本系统
- ✨ AI 讲解缓存
- ✨ 上一题回顾
- ✨ 预构建数据库
- 🐛 修复大数据导入问题

---

## 📚 相关文档

- [主项目 README](../README.md) - 完整项目说明
- [NEW_FEATURES.md](NEW_FEATURES.md) - 新功能详解
- [PREBUILT_DATABASE.md](PREBUILT_DATABASE.md) - 预构建数据库说明

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 到主项目！

**主仓库**: [https://github.com/tmzncty/EnglishExamRPG](https://github.com/tmzncty/EnglishExamRPG)

---

<div align="center">

**⭐ 如果有帮助，请给主项目一个星标！**

Made with ❤️ for English learners

</div>
