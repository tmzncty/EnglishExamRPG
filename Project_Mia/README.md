# Project Mia - 服务器部署说明

## 部署信息

| 项目 | 端口 | 状态 |
|------|------|------|
| 后端 (FastAPI) | 18005 | Supervisor 管理 |
| 前端 (Vue + Vite) | 18006 | Supervisor 管理 |

## 访问地址

- **前端**: http://192.168.24.17:18006
- **后端 API**: http://192.168.24.17:18005
- **健康检查**: http://192.168.24.17:18005/health
- **API 文档**: http://192.168.24.17:18005/docs

## 目录结构

```
/opt/project-mia/
├── backend/                 # FastAPI 后端
│   ├── app/                 # 应用代码
│   │   ├── api/             # API 路由
│   │   ├── db/              # 数据库操作
│   │   └── main.py          # 入口文件
│   ├── data/                # SQLite 数据库
│   │   ├── femo_profile.db  # 用户存档 (782KB)
│   │   └── static_content.db # 静态内容 (7.7MB)
│   ├── .env                 # 环境变量配置
│   ├── requirements.txt     # Python 依赖
│   └── venv/                # Python 虚拟环境
├── frontend/                # Vue 前端
│   ├── src/                 # 源代码
│   ├── public/              # 静态资源
│   ├── package.json         # Node.js 依赖
│   └── vite.config.js       # Vite 配置
└── README.md                # 本文件
```

## 环境配置

### 后端 .env

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv
OPENAI_BASE_URL=https://api.vectorengine.ai/v1
OPENAI_MODEL=gemini-3-flash-preview
```

### 前端 vite.config.js

- 端口: 18006
- API 代理: http://127.0.0.1:18005

## 服务管理

### Supervisor 配置文件

- 后端: /etc/supervisor/conf.d/project-mia-backend.conf
- 前端: /etc/supervisor/conf.d/project-mia-frontend.conf

### 常用命令

```bash
# 查看状态
sudo supervisorctl status

# 重启服务
sudo supervisorctl restart project-mia-backend
sudo supervisorctl restart project-mia-frontend

# 查看日志
tail -f /var/log/project-mia-backend.log
tail -f /var/log/project-mia-frontend.log
```

## 防火墙

已开放端口:
- 18005/tcp (project-mia-backend)
- 18006/tcp (project-mia-frontend)

## 迁移记录

- 迁移时间: 2026-04-20
- 源路径: F:\sanity_check_avg\Project_Mia
- 目标服务器: 192.168.24.17
- Node.js 版本: v20.20.2 (通过 n 安装)
- Python 版本: 3.12
