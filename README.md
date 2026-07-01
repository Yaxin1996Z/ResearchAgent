# ResearchAgent 🧠

> **多 Agent 智能研究助理** —— 输入一个研究主题，4 个 AI 专家协作完成调研、撰写、审核，自动输出结构化 Markdown 报告。支持本地知识库 RAG 检索增强生成。

---

## 项目亮点

| 维度 | 说明 |
|------|------|
| **技术栈** | Python 3.12, DeepSeek API, Chroma RAG, Docker Compose |
| **核心能力** | 多角色 Agent 编排、RAG 知识库检索、工具调用、三层记忆、Docker 部署 |
| **代码量** | ~600 行核心代码，编排引擎手写零框架依赖 |
| **简历价值** | 展示 Agent 架构 + RAG 落地 + 工程化部署能力 |

---

## 架构

```
用户输入 "鲁迅笔下的阿Q形象"
        │
        ▼
┌─────────────────────────────────────────────┐
│               Planner Agent                  │
│          (研究规划专家 - 制定计划)            │
└──────────────────┬──────────────────────────┘
                   │ 研究计划
                   ▼
┌─────────────────────────────────────────────┐
│              Researcher Agent                │
│          (高级技术研究员 - 深度调研)           │
│              ┌────────────────────┐         │
│              │  工具系统(按角色分配)│         │
│              │  · query_knowledge │         │
│              │    (RAG 知识库检索) │         │
│              └────────────────────┘         │
└──────────────────┬──────────────────────────┘
                   │ 调研结果 + 记忆(Findings)
                   ▼
┌─────────────────────────────────────────────┐
│               Writer Agent                   │
│         (技术报告撰写专家 - 输出报告)          │
│              ┌────────────────────┐         │
│              │  · save_file      │         │
│              │  · 记忆系统        │         │
│              │    (Buffer/Entity/Findings)  │
│              └────────────────────┘         │
└──────────────────┬──────────────────────────┘
                   │ 报告草稿
                   ▼
┌─────────────────────────────────────────────┐
│              Reviewer Agent                  │
│         (技术审核专家 - 审核改进)             │
└──────────────────┬──────────────────────────┘
                   │ 最终报告
                   ▼
            ┌──────────────┐
            │  Markdown 文件 │
            │  (自动保存)    │
            └──────────────┘
```

### RAG 知识库

支持本地文档语义检索，启动时自动加载 `rag/repo/` 下的 `.md` / `.txt` 文件，分块后经 bge-small-zh 模型 embedding 存入 Chroma 向量库。

- **匹配机制**：研究主题与知识库内容（鲁迅/毛泽东/白鹿原等）匹配时才注册检索工具，避免无效调用
- **持久化**：Chroma 索引落盘到 `rag/rag_db/`，重复启动复用，无需重新 embedding
- **回退机制**：Docker 环境无 torch 时自动使用 ONNX 轻量模型

### 工具分配

| Agent | 可用工具 | 说明 |
|-------|---------|------|
| 🗂️ Planner | 无 | 仅做规划，不需要工具 |
| 🔬 Researcher | query_knowledge | 按主题匹配注册 |
| ✍️ Writer | save_file | 保存报告 |
| ✅ Reviewer | 无 | 仅做审核 |

---

## 快速开始

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key
```

### 2. 安装

```bash
pip install -e .
# 或 uv sync
```

### 3. 使用

```bash
# CLI 模式
python -m research_agent.main "鲁迅笔下的阿Q形象"

# 指定知识库目录
python -m research_agent.main "白鹿原" --kb-path ./my_docs

# 重建知识库索引
python -m research_agent.main --rebuild

# 交互模式
python -m research_agent.main --interactive
```

### 4. Docker 部署

```bash
# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 重建知识库（首次或更新文档后）
docker compose exec research-agent python -m research_agent.main --rebuild

# 调用 API
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "毛泽东的早期经历"}'

# 查看日志
docker compose logs -f
```

### 运行效果

```bash
# 重建知识库：1760 个片段，约 5 分钟
$ docker compose exec research-agent python -m research_agent.main --rebuild
Loading weights: 100%|█████████████████████████████████████████████████████████████████████████████| 71/71 [00:00<00:00, 176.69it/s]
  📄 《毛泽东传》（罗斯.特里尔版）.txt: 436 个片段，正在 embedding...
     ✅ 179 秒
  📄 《白鹿原》全集.txt: 587 个片段，正在 embedding...
     ✅ 218 秒
  📄 鲁迅全集.txt: 737 个片段，正在 embedding...
     ✅ 264 秒
  📚 知识库加载完成：1760 个片段（共 662 秒）
  ✅ 知识库已重建，共 1760 个片段

# 提交研究任务，RAG 自动检索鲁迅全集
$ curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "鲁迅的阿Q精神研究"}'

📚 知识库已加载：1760 个片段
📚 主题与知识库匹配，已注册检索工具
🚀 启动 4 个 Agent，4 个任务

📋 任务 1: 分析研究主题「鲁迅的阿Q精神研究」，制定研究计划...
  🤖 [研究规划专家] 处理中...  ✅ 完成 (1909 字)

📋 任务 2: 执行研究计划，调研主题「鲁迅的阿Q精神研究」...
  🤖 [高级技术研究员] 处理中...
    🔧 调工具 -> [1] 来源：鲁迅全集.txt（相似度：0.582）
    胜利的悲哀。然而我们的阿Q却没有这样乏，他是...
  ✅ 完成 (4113 字)  [记忆] 提取 5 条关键发现

📋 任务 3: 撰写完整的技术报告...
  🤖 [技术报告撰写专家] 处理中...  ✅ 完成 (8361 字)

📋 任务 4: 审核并改进技术报告...
  🤖 [技术审核专家] 处理中...  ✅ 完成 (9887 字)

✅ 研究完成！报告已保存：output/20260701_1141_鲁迅的阿Q精神研究.md
```

---

## 项目结构

```
ResearchAgent/
├── research_agent/
│   ├── __init__.py
│   ├── main.py                   # CLI入口 + 工具分配
│   ├── orchestrator.py           # Agent / Task / Crew 编排引擎
│   ├── agents.py                 # Agent 角色定义
│   ├── tools.py                  # 工具系统（@tool + ToolExecutor）
│   ├── memory.py                 # 三层记忆（Buffer / Entity / Findings）
│   ├── llm.py                    # LLM API 封装
│   ├── report.py                 # 报告生成与保存
│   ├── rag/                      # RAG 知识库模块
│   │   ├── __init__.py
│   │   ├── config.toml           # 模型路径、目录配置
│   │   ├── knowledge.py          # 文档加载 + Chroma 检索
│   │   ├── repo/                 # 知识库文档（.md/.txt）
│   │   └── rag_db/               # Chroma 持久化索引（自动生成）
│   └── api.py                    # FastAPI 服务
├── output/                       # 生成的报告
├── Dockerfile
├── docker-compose.yml            # 含 rag_data 卷挂载
├── pyproject.toml
└── README.md
```

---

## Docker 部署设计

### 卷挂载

| 卷 | 宿主机 | 容器内 | 作用 |
|----|--------|--------|------|
| **bind** | `./output` | `/app/output` | 报告持久化 |
| **named** | `rag_data` | `/app/research_agent/rag/rag_db` | 向量索引持久化 |
| **bind** | `./rag/repo` | `/app/research_agent/rag/repo` | 文档同步 |
| **bind** | `~/.cache` | `/root/.cache` | bge 模型共享 |

### 资源限制

- CPU 上限 2 核，内存上限 2G
- 健康检查 30s 间隔，3 次失败自动重启
- 自动重启策略 `unless-stopped`

---

## 设计理念

### 为什么手写编排引擎

| 方案 | 优点 | 缺点 |
|------|------|------|
| CrewAI | 开箱即用 | 黑盒、难排查、面试讲不清原理 |
| LangGraph | 状态机灵活 | 学习成本高、抽象层厚 |
| **手写** | 完全可控、零依赖 | 需要造轮子 |

### 记忆系统

| 层次 | 作用 |
|------|------|
| Buffer | 短期对话缓存，CircularBuffer 自动丢弃 |
| Entity | 实体提取（人名/术语/概念） |
| Findings | 研究发现持久化，跨 Agent 传递关键信息 |

---

## 路线图

- [x] 多 Agent 顺序编排
- [x] 工具调用系统 + 按角色分配
- [x] 三层记忆管理
- [x] RAG 知识库（Chroma + bge 本地模型）
- [x] Docker 容器化部署

---

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 运行环境 |
| DeepSeek API | LLM 推理 |
| Chroma + bge-small-zh | RAG 知识库向量检索 |
| Docker / Compose | 容器化部署 |
| 零框架依赖 | 编排引擎、工具、记忆全部手写 |
