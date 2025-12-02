# English Exam RPG & Web (ACG & AI Enhanced)

> **Version 1.1**  
> 这是一个结合了 **ACG 游戏化体验** 与 **AI 辅助解析** 的考研英语真题练习项目。

本项目旨在通过游戏化的方式（RPG 元素、经验值、等级系统）提升考研英语的学习乐趣，并利用 Google Gemini AI 模型对历年真题进行深度结构化解析，生成包含词汇、长难句分析、题目解析等维度的结构化数据。

**注意：本项目目前仅包含【考研英语一】的真题数据。**

## 🚀 项目特性

*   **Web 端核心体验**:
    *   现代化的响应式网页应用，支持 2010-2025 年真题切换。
    *   **沉浸式答题**: 包含背景音乐、音效和动态背景。
    *   **AI 深度解析**: 点击文章任意单词/句子即可查看详细解析。
    *   **游戏化系统**: 经验值 (EXP)、等级、HP 机制。
*   **AI 驱动数据**:
    *   集成 Google Gemini 2.0 Flash/Vision 模型。
    *   支持处理扫描版 PDF (如 2025 年真题)。
    *   自动生成结构化 JSON 数据。
*   **官方解析集成** (v1.1 新增):
    *   嵌入式 PDF 解析查看器。
    *   AI 解析本地缓存，节省 API 调用。
    *   响应式三栏布局，大屏体验更佳。

## 📂 项目结构

```
├── EnglishExamWeb/          # 核心 Web 应用程序
│   ├── index.html           # 主入口
│   ├── css/                 # 样式文件
│   ├── js/                  # 前端逻辑
│   ├── data/                # 历年真题 JSON 数据 (2010-2025)
│   └── assets/              # 静态资源 (背景图、PDF解析等)
│
├── scripts/                 # 数据处理脚本
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

## 🛠️ 如何使用

### 1. 快速开始 (Web 版)

本项目是一个纯静态的 Web 应用，您可以直接部署到任何静态服务器（如 GitHub Pages, Vercel）。

本地预览：
```bash
python -m http.server 8080
```
访问: `http://localhost:8080/EnglishExamWeb/`

### 2. 数据生成 (开发者)

如果您需要重新生成数据：

1.  安装依赖: `pip install -r requirements.txt`
2.  配置 `.env` 文件 (GEMINI_API_KEY)。
3.  将真题放入 `DOCX/` 和 `PDF/` 目录。
4.  运行 `python scripts/pdf_to_json.py` 生成数据。
5.  运行 `python scripts/extract_all_images.py` 提取图片。
6.  运行 `python scripts/deploy_data.py` 将数据部署到 Web 目录。

## 📅 未来计划

*   [ ] 支持考研英语二数据。
*   [ ] 增加更多 RPG 元素（如道具、技能）。
*   [ ] 引入更多 ACG 主题包。

## 📝 更新日志

### v1.1 (2025-12-02)
*   ✨ **新增**: 嵌入式 PDF 官方解析查看器，答题后可直接查看原版解析。
*   ✨ **新增**: AI 解析本地缓存功能，同一题目只需调用一次 API。
*   ✨ **新增**: 响应式三栏布局，适配大屏/平板/手机。
*   ✨ **新增**: 所有年份 (2010-2024) Writing Part B 图片支持。
*   🐛 **修复**: 字体强制使用系统中文字体，解决乱码问题。
*   📁 **整理**: Python 脚本统一移至 `scripts/` 目录。

### v1.0 (2025-12-01)
*   🎉 初始发布版本。
*   ✨ 支持 2010-2025 年考研英语一真题。
*   ✨ WebDAV 云同步功能。
*   ✨ AI 划词解释（流式输出）。
*   ✨ 游戏化 RPG 系统。

## ⚠️ 版权与免责声明

*   本项目代码开源 (MIT License)。
*   **注意**: 项目中包含的历年真题原文及解析内容的版权归原作者或考试机构所有。本项目仅提供处理工具和展示框架。
*   `.env` 文件包含敏感密钥，请勿上传。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request！
