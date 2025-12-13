# GitHub Release v2.1.0 发布指南

## 📋 发布信息

**版本号**: v2.1.0  
**发布日期**: 2025-12-13  
**代号**: Multi-Device Sync  
**类型**: 功能更新

---

## 🚀 创建 Release 步骤

### 1. 访问 GitHub Release 页面
```
https://github.com/tmzncty/EnglishExamRPG/releases/new
```

### 2. 填写 Release 信息

#### Tag version (标签)
```
v2.1.0
```

#### Release title (标题)
```
VocabWeb v2.1.0 - 多设备协同学习
```

#### Description (描述)
```markdown
## 🎉 VocabWeb v2.1.0 - 多设备协同学习时代来临！

### 📱 核心特性

#### ⭐ 多设备数据同步
**终于可以手机和电脑一起学完今天的单词了！**

- ✅ 手机学习 20 个单词
- ✅ 电脑继续学习 30 个单词  
- ✅ 进度自动累加到 50 个
- ✅ 数据实时同步，不会重复

#### 🔑 API Key 配置优化
**解决手机密码框无法粘贴的痛点**

**方法 1：电脑配置 + 手机同步（推荐）**
```
电脑: 输入 API Key → 保存设置
手机: 点击"🔄 同步配置" → 完成
```

**方法 2：显示/隐藏密码**
```
点击 👁️ 按钮 → 查看密码 → 确认 → 隐藏
```

详细教程: [API_KEY_SETUP.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/API_KEY_SETUP.md)

#### ⚙️ 配置与数据分离

| 数据类型 | 存储位置 | 是否同步 |
|---------|---------|---------|
| 学习记录 | 服务器 | ✅ 是 |
| 错题本 | 服务器 | ✅ 是 |
| AI 缓存 | 服务器 | ✅ 是 |
| API Key | 服务器 | ✅ 是 |
| 每日目标 | 本地 | ❌ 否 |
| 通知设置 | 本地 | ❌ 否 |

---

### 🆕 新增功能

#### API 接口
- `POST /api/save-db` - 保存学习数据
- `GET /api/get-db` - 获取学习数据
- `POST /api/save-config` - 保存配置
- `GET /api/get-config` - 获取配置
- `GET /api/status` - 服务器状态

#### 用户界面
- 🔄 "同步配置"按钮
- 👁️ 显示/隐藏密码按钮
- 📊 服务器状态指示器
- 🧪 测试页面（test-api-key.html）

#### 工具页面
- `clear.html` - 清除本地缓存
- `test.html` - 服务器连接测试
- `test-api-key.html` - API Key 同步测试

---

### 🐛 问题修复

- ✅ 修复服务器返回 0 KB 数据库导致加载失败
- ✅ 修复配置在 SQLite 中存储导致的同步冲突
- ✅ 修复手机端密码输入困难
- ✅ 修复数据库重复调用 schema 升级

---

### 📚 新增文档

- [API_KEY_SETUP.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/API_KEY_SETUP.md) - API Key 配置完整指南
- [CONFIG.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/CONFIG.md) - 配置文件说明
- [DATA_SYNC.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/DATA_SYNC.md) - 数据同步技术文档
- [USAGE_GUIDE.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/USAGE_GUIDE.md) - 详细使用教程
- [QUICK_REFERENCE.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/QUICK_REFERENCE.md) - 快速参考卡片
- [CHANGELOG.md](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/CHANGELOG.md) - 更新日志

---

### 🚀 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/tmzncty/EnglishExamRPG.git
cd EnglishExamRPG/VocabWeb

# 2. 安装依赖
pip install flask flask-cors

# 3. 启动服务器
python server.py

# 4. 访问应用
# 💻 电脑: http://localhost:8080
# 📱 手机: http://你的IP:8080
```

---

### 📊 数据统计

- ✅ **6131 个单词** - 覆盖考研核心词汇
- ✅ **1882 条真题例句** - 真实考试语境
- ✅ **完整题目元数据** - 年份、题型、section
- ✅ **预构建数据库** - 开箱即用

---

### 🆙 升级指南

从 v2.0.x 升级：

```bash
# 1. 备份数据（如果有）
copy user_vocab.db user_vocab.db.backup

# 2. 拉取更新
git pull origin main

# 3. 启动服务器
python server.py
```

**注意**: API Key 需要重新配置（存储方式已优化）

---

### 📞 支持

- 🐛 [报告问题](https://github.com/tmzncty/EnglishExamRPG/issues)
- 💬 [讨论交流](https://github.com/tmzncty/EnglishExamRPG/discussions)
- 📖 [完整文档](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/README.md)
- 📝 [发布说明](https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/RELEASE_NOTES_v2.1.0.md)

---

**祝你考研成功！🎓**
```

---

### 3. 选择分支
```
Target: main
```

### 4. 附件（可选）
无需上传附件，所有文件已在代码库中

---

## ✅ 发布检查清单

在点击"Publish release"前确认：

- [x] ✅ 代码已推送到 GitHub
- [x] ✅ 标签版本正确（v2.1.0）
- [x] ✅ 发布标题清晰
- [x] ✅ 描述完整（包含功能、修复、升级指南）
- [x] ✅ 链接正确（指向正确的文档）
- [x] ✅ 更新日志已创建（CHANGELOG.md）
- [x] ✅ 发布说明已创建（RELEASE_NOTES_v2.1.0.md）

---

## 📢 发布后操作

### 1. 更新 README.md 顶部徽章（如果有）
```markdown
[![Latest Release](https://img.shields.io/github/v/release/tmzncty/EnglishExamRPG)](https://github.com/tmzncty/EnglishExamRPG/releases/latest)
```

### 2. 发布推广（可选）
- 在 Discussions 发布更新公告
- 社交媒体分享
- 通知用户升级

### 3. 监控反馈
- 关注 Issues 中的问题
- 收集用户反馈
- 准备 hotfix（如有必要）

---

## 🔗 相关链接

- **GitHub 仓库**: https://github.com/tmzncty/EnglishExamRPG
- **Release 页面**: https://github.com/tmzncty/EnglishExamRPG/releases
- **文档主页**: https://github.com/tmzncty/EnglishExamRPG/blob/main/VocabWeb/README.md
- **问题追踪**: https://github.com/tmzncty/EnglishExamRPG/issues

---

<div align="center">

**🎉 准备就绪，可以发布了！**

点击 [创建 Release](https://github.com/tmzncty/EnglishExamRPG/releases/new)

</div>
