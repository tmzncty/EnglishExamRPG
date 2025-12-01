# English Exam RPG & Web (ACG & AI Enhanced)

这是一个结合了 **ACG 游戏化体验** 与 **AI 辅助解析** 的考研英语真题练习项目。

本项目旨在通过游戏化的方式（RPG 元素、经验值、等级系统）提升考研英语的学习乐趣，并利用 Google Gemini AI 模型对历年真题进行深度结构化解析，生成包含词汇、长难句分析、题目解析等维度的结构化数据。

## 🚀 项目特性

*   **双端支持**:
    *   **Web 端**: 现代化的响应式网页应用，支持年份选择、答题交互、实时反馈、单词本等功能。
    *   **Ren'Py 端** (EnglishExamRPG): 视觉小说形式的沉浸式体验 (开发中)。
*   **AI 驱动数据**:
    *   使用 Python 脚本批量处理历年真题 (DOCX/PDF)。
    *   集成 Google Gemini 2.0 Flash/Vision 模型进行多模态解析。
    *   自动提取文章、题目、选项，并生成详细的中文解析和词汇表。
    *   支持处理扫描版 PDF (通过 Vision API)。
*   **游戏化学习**:
    *   经验值 (EXP) 与等级系统。
    *   HP (生命值) 机制，答错扣血。
    *   ACG 主题 UI 设计。

## 📂 项目结构

*   `EnglishExamWeb/`: Web 端应用程序源码。
    *   `data/`: 存放处理好的历年真题 JSON 数据 (2010-2025)。
    *   `js/`: 前端逻辑 (App, UI, Storage, Gemini Service 等)。
    *   `css/`: 样式文件 (包含 ACG 主题)。
*   `EnglishExamRPG/`: Ren'Py 游戏工程文件。
*   `scripts/` (根目录下的 Python 脚本):
    *   `pdf_to_json.py`: 核心处理脚本，将 DOCX/PDF 转换为 JSON。
    *   `process_2025_from_images.py`: 针对 2025 扫描版真题的视觉处理脚本。
    *   `deploy_data.py`: 将生成的 JSON 数据部署到 Web 目录。

## 🛠️ 如何使用

### 1. 环境准备

本项目依赖 Python 3.x 和 Node.js (可选，仅用于 Web 开发工具)。

安装 Python 依赖:
```bash
pip install -r requirements.txt
```

你需要一个 Google Gemini API Key，并将其配置在 `.env` 文件中:
```ini
GEMINI_API_KEY=your_api_key_here
```

### 2. 数据生成 (可选)

如果你需要重新生成数据或添加新年份的真题：

1.  将真题 DOCX 文件放入 `DOCX/` 目录。
2.  将解析 PDF 文件放入 `PDF/` 目录。
3.  运行处理脚本:
    ```bash
    python pdf_to_json.py
    ```
4.  部署数据到 Web 端:
    ```bash
    python deploy_data.py
    ```

### 3. 启动 Web 应用

在根目录下运行简单的 HTTP 服务器即可预览:

```bash
python -m http.server 8080
```

访问: `http://localhost:8080/EnglishExamWeb/`

## ⚠️ 版权与免责声明

*   本项目代码开源 (MIT License)。
*   **注意**: 项目中包含的历年真题原文及解析内容的版权归原作者或考试机构所有。本项目仅提供处理工具和展示框架，不直接提供版权内容的分发。在使用本项目时，请确保你拥有合法的使用权限。
*   `.env` 文件包含敏感密钥，请勿上传到公共仓库。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来改进这个项目！
