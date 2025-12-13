# 更新日志

所有重要的更改都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [2.1.0] - 2025-12-13

### 🎉 新增

#### 多设备数据同步
- Flask 服务器实现跨设备数据同步
- 自动保存机制（30秒 + 答题后立即保存）
- LocalStorage 离线备份
- 服务器状态监控页面

#### API Key 配置优化
- 电脑配置 + 手机同步功能
- 显示/隐藏密码按钮（👁️/🙈）
- 配置同步 API（`/api/save-config`, `/api/get-config`）
- 配置测试页面（`test-api-key.html`）

#### 工具页面
- `clear.html` - 清除本地缓存
- `test.html` - 服务器连接测试
- `test-api-key.html` - API Key 同步测试
- `start.bat` - Windows 一键启动脚本

#### 文档完善
- `API_KEY_SETUP.md` - API Key 配置完整指南
- `CONFIG.md` - 配置文件详细说明
- `DATA_SYNC.md` - 数据同步技术文档
- `USAGE_GUIDE.md` - 详细使用教程
- `QUICK_REFERENCE.md` - 快速参考卡片
- `RELEASE_CHECKLIST.md` - 发布检查清单
- `RELEASE_NOTES_v2.1.0.md` - 完整发布说明

### 🔧 修改

#### 数据库管理（db.js）
- 配置存储从 SQLite 迁移到 localStorage
- 添加数据库验证机制（大小检查 + SQL 测试）
- 实现服务器同步功能
- 优化数据库加载流程

#### 用户界面
- `index.html`: 添加同步配置按钮和显示密码按钮
- `css/style.css`: API Key 输入组样式，按钮图标样式
- `js/app.js`: 配置同步逻辑，`syncConfig()` 和 `saveConfigToServer()` 方法

#### 服务器（server.py）
- 添加配置同步 API 接口
- 优化错误处理
- 添加详细的启动信息

### 🐛 修复

- 修复服务器返回 0 KB 数据库导致加载失败的问题
- 修复配置在 SQLite 中存储导致的同步冲突
- 修复手机端密码输入困难的问题
- 修复数据库重复调用 `ensureSchemaUpgrades()` 的问题

### 📚 文档

- 更新 README.md，添加多设备使用说明
- 添加 .gitignore 排除敏感数据
- 创建完整的 API Key 配置教程
- 添加数据同步技术文档

### 🔒 安全

- 将 `user_config.json` 添加到 .gitignore
- API Key 存储在本地服务器而非浏览器
- 数据仅在局域网内传输

---

## [2.0.0] - 2025-12-12

### 🎉 新增
- 预构建数据库（6131 个单词，1882 条例句）
- SuperMemo 2 间隔重复算法
- 智能错题本（连续答对 3 次移出）
- Gemini 2.0 Flash AI 讲解
- ACG 风格界面设计
- 浏览器通知提醒

### 🔧 核心功能
- SQL.js 浏览器端数据库
- LocalStorage 数据持久化
- 真题语境学习
- 每日学习目标设置
- 学习统计面板

---

## 版本说明

### 语义化版本
- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 发布周期
- **稳定版**：经过充分测试的正式版本
- **预览版**：包含新特性的测试版本

### 支持策略
- 最新版本：完整支持
- 上一个大版本：安全更新
- 更早版本：不再支持

---

## 链接

- [完整发布说明](RELEASE_NOTES_v2.1.0.md)
- [升级指南](README.md#升级指南)
- [问题反馈](https://github.com/tmzncty/EnglishExamRPG/issues)

---

<div align="center">

**持续改进中 🚀**

查看 [项目主页](https://github.com/tmzncty/EnglishExamRPG) 获取最新信息

</div>
