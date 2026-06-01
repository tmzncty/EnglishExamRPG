# Project Mia Backend

FastAPI 后端服务，提供 AI 对话、考试、词汇学习等功能。

## 技术栈

- **框架**: FastAPI
- **数据库**: SQLite (femo_profile.db + static_content.db)
- **AI**: OpenAI API 兼容接口 (Gemini)

## 快速启动

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 18005

# 或使用 Supervisor
sudo supervisorctl restart project-mia-backend
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| / | GET | 欢迎信息 |
| /health | GET | 健康检查 |
| /docs | GET | Swagger API 文档 |
| /api/mia/interact | POST | AI 对话 |
| /api/exams | GET | 获取试卷列表 |
| /api/user/status | GET | 获取用户状态 |
| /api/vocab/* | * | 词汇相关 API |

## 数据库

### static_content.db (只读)
- 试卷内容
- 题目数据
- 词典数据

### femo_profile.db (读写)
- 用户存档 (HP, 等级, 经验值)
- 答题记录
- 学习进度

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| AI_PROVIDER | AI 提供商 (openai) | 是 |
| OPENAI_API_KEY | API 密钥 | 是 |
| OPENAI_BASE_URL | API 基础 URL | 是 |
| OPENAI_MODEL | 模型名称 | 是 |

## 依赖

```
google-generativeai
python-dotenv
fastapi
uvicorn[standard]
pydantic
sqlalchemy
```

## 日志

- Supervisor 日志: /var/log/project-mia-backend.log
