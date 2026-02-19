# Project_Mia 前后端分离架构

## 项目结构

```
Project_Mia/
├── backend/                # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # 入口
│   ├── data/               # SQLite数据库
│   │   ├── static_content.db
│   │   └── femo_profile.db
│   └── requirements.txt
│
├── frontend/               # Vue3前端
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── stores/
│       └── views/
│
└── scripts/                # 工具脚本
    └── migrate_v1_to_v2.py
```

## 快速开始

### 1. 数据迁移 (阶段一)

```bash
cd scripts
python migrate_v1_to_v2.py
```

### 2. 启动后端 (阶段二)

```bash
cd backend
pip install -r requirements.txt
python -m app.main
# 访问: http://localhost:8000
```

### 3. 启动前端 (阶段三)

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:5173
```

## 数据库说明

### static_content.db (静态内容,只读)
- `papers` - 试卷元数据
- `questions` - 题目内容
- `dictionary` - 词典
- `stories` - Mia剧情

### femo_profile.db (用户数据,读写)
- `vocab_progress` - 词汇学习进度(SM-2)
- `exam_history` - 答题历史
- `mia_memory` - Mia记忆库
- `game_saves` - 游戏存档

## 开发路线图

- [x] 阶段零: 项目结构初始化
- [x] 阶段一: 数据库Schema + 迁移脚本
- [ ] 阶段二: FastAPI后端API
- [ ] 阶段三: Vue3前端重构

---

**作者**: 绯墨 (Femo)  
**版本**: 2.0.0  
**日期**: 2026-02-15
