# English Exam RPG & VocabWeb (ACG & AI Enhanced)

> **Version 2.0**  
> 这是一个结合了 **ACG 游戏化体验** 与 **AI 辅助解析** 的考研英语全方位学习项目。

本项目包含两大核心系统：
1. **EnglishExamWeb** - 真题练习与解析系统
2. **VocabWeb** - 智能词汇记忆系统

通过游戏化的方式（RPG 元素、经验值、等级系统、错题本）提升考研英语的学习乐趣，并利用 Google Gemini AI 模型进行深度解析。

**注意：本项目目前仅包含【考研英语一】的真题数据。**

---

## 🎯 双系统概览

### 📝 EnglishExamWeb - 真题练习系统
- ✅ 2010-2025 年完整真题
- ✅ 沉浸式答题体验（背景音乐、音效、动态背景）
- ✅ AI 深度解析（划词查看单词/句子分析）
- ✅ RPG 游戏化系统（经验值、等级、HP）
- ✅ 嵌入式 PDF 官方解析查看器
- ✅ AI 解析本地缓存

### 📚 VocabWeb - 智能词汇系统
- ✅ **多设备数据同步** - 手机、电脑协同学习，进度实时同步 🔄
- ✅ **API Key 配置优化** - 电脑配置后，手机一键同步 🔑
- ✅ 基于遗忘曲线的记忆算法（SuperMemo 2）
- ✅ 真题例句学习（从真题中提取）
- ✅ AI 智能讲解（Gemini 2.0 Flash）
- ✅ 智能错题本（三次答对才消除）
- ✅ 错题自动混入每日学习
- ✅ 灵活每日目标（可多学不可少学）
- ✅ 上一题回顾功能
- ✅ AI 讲解缓存（节省 API 成本）
- ✅ Flask 服务器支持（跨设备同步）

---

## 📂 项目结构

```
├── EnglishExamWeb/          # 🎮 真题练习系统
│   ├── index.html           # 主入口
│   ├── css/                 # 样式文件
│   ├── js/                  # 前端逻辑
│   ├── data/                # 历年真题 JSON 数据 (2010-2025)
│   └── assets/              # 静态资源 (背景图、PDF解析等)
│
├── VocabWeb/                # 📚 词汇学习系统
│   ├── index.html           # 学习界面
│   ├── server.py            # Flask 服务器（多设备同步）
│   ├── start.bat            # Windows 一键启动
│   ├── clear.html           # 缓存清理工具
│   ├── test.html            # 服务器测试页面
│   ├── test-api-key.html    # API Key 同步测试
│   ├── css/                 # 样式文件
│   ├── js/                  
│   │   ├── app.js           # 主应用逻辑
│   │   ├── db.js            # 数据库操作（支持同步）
│   │   ├── ai-service.js    # AI 服务集成
│   │   └── learning-algorithm.js  # 记忆算法
│   ├── data/                
│   │   ├── exam_vocabulary.json    # 词汇数据
│   │   └── vocab_prebuilt.txt      # 预构建数据库
│   ├── fonts/               # 霞鹜文楷等宽字体
│   ├── extract_vocab.py     # 从真题提取词汇
│   ├── prebuild_database.py # 预构建数据库
│   ├── README.md            # 完整使用指南
│   ├── API_KEY_SETUP.md     # API Key 配置教程
│   ├── CHANGELOG.md         # 更新日志
│   └── RELEASE_NOTES_v2.1.0.md  # 发布说明
│
├── scripts/                 # 🛠️ 数据处理脚本
│   ├── pdf_to_json.py       # 核心：DOCX/PDF → JSON
│   ├── extract_all_images.py # 从 DOCX 批量提取图片
│   ├── deploy_data.py       # 部署数据到 Web 目录
│   └── ...                  # 其他辅助脚本
│
├── DOCX/                    # 原始真题 Word 文档
├── PDF/                     # 原始真题 PDF 文档
├── *_full.json              # 生成的完整数据文件
└── requirements.txt         # Python 依赖
```

---

## 🚀 快速开始

### 方式一：直接使用（推荐）

两个系统都是纯静态 Web 应用，可直接部署到任何静态服务器。

**本地预览**：

**真题系统**：
```bash
# 在项目根目录启动简单服务器
python -m http.server 8080

# 访问真题系统
# http://localhost:8080/EnglishExamWeb/
```

**词汇系统（推荐使用 Flask 服务器）**：
```bash
# 进入 VocabWeb 目录
cd VocabWeb

# 安装依赖（仅需一次）
pip install flask flask-cors

# 启动服务器
python server.py
# 或 Windows 用户双击 start.bat

# 访问应用
# 💻 电脑: http://localhost:8080
# 📱 手机: http://你的电脑IP:8080
```

**在线部署**：
- GitHub Pages
- Vercel
- Netlify
- 或任何静态托管服务

### 方式二：完整开发环境

如果需要重新生成数据或自定义功能：

#### 1. 环境准备

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 GEMINI_API_KEY
```

#### 2. 生成真题数据

```bash
# 将真题文档放入 DOCX/ 和 PDF/ 目录

# 生成 JSON 数据
python scripts/pdf_to_json.py

# 提取图片
python scripts/extract_all_images.py

# 部署到 Web 目录
python scripts/deploy_data.py
```

#### 3. 生成词汇数据

```bash
cd VocabWeb

# 从真题中提取词汇
python extract_vocab.py

# 预构建数据库（可选，优化首次加载）
python prebuild_database.py
```

---

## 📖 系统详细说明

### 一、EnglishExamWeb - 真题练习系统

#### 核心功能

1. **真题练习**
   - 完整收录 2010-2025 年考研英语一真题
   - 按年份切换，支持各题型（阅读、完型、翻译、写作）
   - 实时答题，即时反馈

2. **AI 智能解析**
   - 点击任意单词：查看词义、词根词缀、用法
   - 点击句子：长难句分析、语法讲解
   - 流式输出，体验流畅
   - 本地缓存，避免重复调用 API

3. **RPG 游戏化**
   - 经验值系统：答对获得 EXP
   - 等级系统：随学习进度提升
   - HP 机制：答错扣血，增加紧张感
   - 成就系统（规划中）

4. **沉浸式体验**
   - 背景音乐（可自定义）
   - 答题音效
   - 动态樱花背景
   - ACG 风格界面

5. **官方解析**
   - 嵌入式 PDF 查看器
   - 答题后可对照官方解析
   - 响应式三栏布局

#### 使用流程

```
打开 EnglishExamWeb/index.html
    ↓
选择年份（2010-2025）
    ↓
选择题型（Reading / Cloze / Translation / Writing）
    ↓
开始答题
    ↓
点击单词/句子 → AI 解析
    ↓
提交答案 → 查看官方解析
    ↓
获得 EXP，升级！
```

---

### 二、VocabWeb - 智能词汇系统

#### 核心功能

##### 1. 智能记忆算法 🧠

采用 **SuperMemo 2** 间隔重复算法：

- **首次学习**：当天复习
- **答对**：间隔逐渐拉长（1天 → 3天 → 7天 → 15天...）
- **答错**：重置间隔，重新开始
- **动态调整**：根据答题质量自动调整难度系数

##### 2. 智能错题本系统 📋

**工作原理**：
```
答错 → 进入错题本 (连续正确: 0/3)
  ↓
再次遇到，答对 → 计数 +1 (连续正确: 1/3)
  ↓
再次答对 → 计数 +1 (连续正确: 2/3)
  ↓
第三次答对 → 移出错题本 ✅ (连续正确: 3/3)

注意：中途答错会重置计数器
```

**特点**：
- ✅ 答错自动标记
- ✅ 错题自动混入每日学习（占比最多 20%）
- ✅ 连续答对 3 次才彻底掌握
- ✅ 实时统计错题数量

##### 3. AI 智能讲解 🤖

集成 **Gemini 2.0 Flash** 模型：

**讲解内容**：
- 📖 **基础释义**：简单明了的中文解释
- 🎯 **例句用法**：在真题句子中的含义
- 💡 **记忆技巧**：词根词缀、联想、谐音等
- 📝 **常见搭配**：2-3 个常用短语

**智能缓存**：
- 同一个词的讲解只生成一次
- 自动保存到本地数据库
- 节省 API 调用成本
- 离线也能查看已缓存的讲解

##### 4. 灵活学习计划 📅

- **每日目标**：可设置 5-100 个词
- **灵活完成**：可多学，不可少学
- **错题混入**：自动安排错题复习
- **上一题回顾**：可返回查看之前的题目

##### 5. 详细统计 📊

右侧统计面板实时显示：
- ✨ **今日学习**：新学单词数
- 📚 **今日复习**：复习单词数
- 🎯 **累计学习**：总学习词数
- 📈 **正确率**：当日答题正确率
- 📋 **错题本**：待复习错题数（红色标注）

#### 使用流程

**首次使用（多设备同步模式）**：
```
1. 启动服务器
   python server.py  (或双击 start.bat)

2. 电脑端配置
   打开 http://localhost:8080
   设置 → 输入 API Key → 保存
   ↓ 自动保存到服务器

3. 手机端同步
   打开 http://你的IP:8080
   设置 → 点击"🔄 同步配置" → 完成！
```

**日常学习（多设备协同）**：
```
早上地铁 (手机): 学习 20 词
  ↓ 自动同步到服务器
中午休息 (手机): 复习 10 词  
  ↓ 自动同步
晚上回家 (电脑): 继续学习 20 词
  ↓
进度完美累加: 50 词 ✅

系统分配内容:
├─ 新词（根据每日目标）
├─ 需要复习的词（根据遗忘曲线）
└─ 错题（自动混入，占比 20%）
```

详细教程：[VocabWeb/README.md](VocabWeb/README.md)

#### 数据来源

所有词汇和例句均从 `EnglishExamWeb/data` 中的真题 JSON 提取：

- **6131 个单词**
- **1882 条例句**
- 包含年份、题型、section 等元数据
- 完全真题语境，学以致用

---

## ⚙️ 配置说明

### EnglishExamWeb 配置
### VocabWeb 配置

在应用的"设置"页面可配置：
- **每日新词数量**：5-100 个（每个设备可单独设置）
- **睡眠时间**：一天结束的时间点
- **学习提醒**：启用/禁用通知（各设备独立）
- **提醒时间**：每日提醒时间
- **Gemini API Key**：AI 讲解功能必需
  - 💡 电脑端配置后，手机端点击"同步配置"即可
  - 📖 详细教程：[API_KEY_SETUP.md](VocabWeb/API_KEY_SETUP.md)

在应用的"设置"页面可配置：
- **每日新词数量**：5-100 个
### 前端
- **纯原生 JavaScript**（无框架依赖）
- **SQL.js**：浏览器端 SQLite
- **Fetch API**：与 Gemini API 通信
- **LocalStorage**：本地配置存储
- **CSS3 动画**：流畅的界面效果

### 后端
- **Flask 3.0**：跨设备同步服务器
- **Python 3.8+**：数据处理脚本
- **python-docx**：解析 Word 文档
- **PyMuPDF (fitz)**：解析 PDF
- **Pillow**：图片处理
- **Google Generative AI**：AI 数据生成
- **LocalStorage**：数据持久化
- **CSS3 动画**：流畅的界面效果

### 后端（数据生成）
- **Python 3.8+**
- **python-docx**：解析 Word 文档
- **PyMuPDF (fitz)**：解析 PDF
- **Pillow**：图片处理
- **Google Generative AI**：AI 数据生成

### AI 模型
- **Gemini 2.0 Flash Exp**：文本解析
- **Gemini 1.5 Pro Vision**：图片处理（2025 年真题）

---

## 📊 数据统计

### EnglishExamWeb
- ✅ 16 年真题（2010-2025）
- ✅ 完整题型覆盖
- ✅ 所有图片已提取
- ✅ PDF 官方解析已整合

### VocabWeb
- ✅ 6131 个单词
- ✅ 1882 条真题例句
- ✅ 完整题目元数据
- ✅ 预构建数据库 1.19 MB

---

## 🔧 常见问题

### Q1: 如何获取 Gemini API Key？

1. 访问 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 登录 Google 账号
### Q2: VocabWeb 数据加载失败？

**解决方案 1 - 使用清理工具**：
```
访问 http://localhost:8080/clear.html
点击"清除缓存"按钮
```

**解决方案 2 - 手动清理**：
```javascript
// 在浏览器控制台执行
localStorage.clear()
// 然后刷新页面，会重新加载预构建数据库
```在浏览器控制台执行
localStorage.clear()
// 然后刷新页面，会重新加载预构建数据库
```

### Q3: 如何自定义词汇数据？

编辑 `VocabWeb/data/exam_vocabulary.json`，然后：
```bash
cd VocabWeb
python prebuild_database.py  # 重新生成数据库
```
### Q5: 错题本如何清空？

在 VocabWeb 设置中点击"清空数据库"（⚠️ 会删除所有学习记录）

或仅清空错题本：
```javascript
// 在浏览器控制台执行
await db.init();
db.db.run("UPDATE learning_records SET is_mistake = 0, consecutive_correct = 0");
db.save();
```

### Q6: 手机端如何配置 API Key？

**推荐方法（最简单）**：
1. 在电脑上打开 VocabWeb，配置 API Key 并保存
## 📝 更新日志

### v2.1.0 (2025-12-13) - 多设备协同学习 🔥

**核心更新**：
*   🎉 **新增**: 多设备数据同步（手机+电脑协同学习）
*   🔑 **新增**: API Key 配置优化（电脑配置+手机同步）
*   🔄 **新增**: Flask 服务器支持跨设备同步
*   👁️ **新增**: 显示/隐藏密码功能
*   ⚙️ **优化**: 配置与数据分离（灵活个性化）
*   🐛 **修复**: 数据库加载验证机制
*   📚 **文档**: 完整的配置指南和技术文档

**详细说明**：[VocabWeb/RELEASE_NOTES_v2.1.0.md](VocabWeb/RELEASE_NOTES_v2.1.0.md)  
**更新日志**：[VocabWeb/CHANGELOG.md](VocabWeb/CHANGELOG.md)

### v2.0 (2025-12-13)
*   🎉 **新增**: VocabWeb 词汇学习系统
*   ✨ **新增**: 智能错题本（三次答对消除机制）
*   ✨ **新增**: 错题自动混入每日学习
*   ✨ **新增**: AI 讲解缓存功能
*   ✨ **新增**: 上一题回顾功能
*   ✨ **新增**: 灵活每日目标（可多学不可少学）
*   ✨ **新增**: 预构建数据库（首次加载更快）
*   🐛 **修复**: 大数据导入栈溢出问题
*   📖 **文档**: 完善双系统说明文档80
3. 学习数据自动同步，配置各设备独立

**详细说明**：[VocabWeb/DATA_SYNC.md](VocabWeb/DATA_SYNC.md)
在 VocabWeb 设置中点击"清空数据库"（⚠️ 会删除所有学习记录）

## 🎯 未来计划

### v2.2.0（进行中）
- [x] ✅ 多设备数据同步
- [x] ✅ API Key 配置优化
- [ ] 二维码配置功能
- [ ] PWA 离线支持

### 短期目标
- [ ] 错题本导出/导入功能
- [ ] 单词本自定义标签
- [ ] 学习数据可视化图表
- [ ] 数据加密传输（HTTPS）

### 中期目标
- [ ] 支持考研英语二数据
- [ ] 增加更多 RPG 元素（道具、技能）
- [ ] 移动端 APP（PWA）
- [ ] 多用户系统

### 长期目标
- [ ] 云端同步（可选）
- [ ] 社区分享功能
- [ ] AI 智能推荐学习路径
- [ ] 引入更多 ACG 主题包目标（可多学不可少学）
*   ✨ **新增**: 预构建数据库（首次加载更快）
*   🐛 **修复**: 大数据导入栈溢出问题
*   📖 **文档**: 完善双系统说明文档

### v1.1 (2025-12-02)
*   ✨ **新增**: 嵌入式 PDF 官方解析查看器
*   ✨ **新增**: AI 解析本地缓存功能
*   ✨ **新增**: 响应式三栏布局
*   ✨ **新增**: 所有年份 Writing Part B 图片支持
*   🐛 **修复**: 字体乱码问题
*   📁 **整理**: Python 脚本统一移至 scripts/ 目录

### v1.0 (2025-12-01)
*   🎉 初始发布版本
*   ✨ 支持 2010-2025 年考研英语一真题
*   ✨ WebDAV 云同步功能
*   ✨ AI 划词解释（流式输出）
*   ✨ 游戏化 RPG 系统

---

## 🎯 未来计划

### 短期目标
- [ ] 错题本导出/导入功能
- [ ] 单词本自定义标签
- [ ] 学习数据可视化图表
- [ ] 多设备云同步（WebDAV）

### 中期目标
- [ ] 支持考研英语二数据
- [ ] 增加更多 RPG 元素（道具、技能）
- [ ] 移动端 APP（PWA）
- [ ] 离线模式增强

### 长期目标
- [ ] 多语言学习支持
- [ ] 社区分享功能
- [ ] AI 智能推荐学习路径
- [ ] 引入更多 ACG 主题包

---

## ⚠️ 版权与免责声明

*   本项目代码开源 (MIT License)
*   **注意**: 项目中包含的历年真题原文及解析内容的版权归原作者或考试机构所有
*   本项目仅提供处理工具和展示框架，用于个人学习研究
*   请勿用于商业用途
*   `.env` 文件包含敏感密钥，请勿上传

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request！

**贡献指南**：
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📧 联系方式

- GitHub: [@tmzncty](https://github.com/tmzncty)
- Issues: [GitHub Issues](https://github.com/tmzncty/EnglishExamRPG/issues)

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星标！**

Made with ❤️ for English learners

</div>
