# ResearchAgent 🧠

> **多 Agent 智能研究助理** —— 输入一个技术主题，4 个 AI 专家协作完成调研、撰写、审核，自动输出结构化 Markdown 报告。

---

## 项目亮点

| 维度 | 说明 |
|------|------|
| **技术栈** | Python 3.12, OpenAI API (DeepSeek), 手写多 Agent 编排引擎 |
| **核心能力** | 多角色 Agent 协作、工具调用、层级记忆、Markdown 报告自动生成 |
| **代码量** | ~500 行，零框架依赖，从底层 LLM 调用到上层编排全部手写 |
| **简历价值** | 展示 Agent 架构设计能力、工程落地能力、系统思维能力 |

---

## 架构

```
用户输入 "什么是MCP协议"
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
│              ┌──────────────┐               │
│              │  工具系统    │               │
│              │  · 计算器    │               │
│              │  · 文件操作  │               │
│              └──────────────┘               │
└──────────────────┬──────────────────────────┘
                   │ 调研结果
                   ▼
┌─────────────────────────────────────────────┐
│               Writer Agent                   │
│         (技术报告撰写专家 - 输出报告)          │
│              ┌──────────────┐               │
│              │   记忆系统   │               │
│              │  · 短期缓冲  │               │
│              │  · 实体提取  │               │
│              │  · 研究发现  │               │
│              └──────────────┘               │
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

### 核心组件

| 模块 | 职责 | 对应文件 |
|------|------|---------|
| **Agent** | 角色设定 + 工具 + 记忆，执行具体任务 | `orchestrator.py` |
| **Task** | 任务单元（描述 + 分配给谁） | `orchestrator.py` |
| **Crew** | 任务调度器，管理 Agent 执行顺序 | `orchestrator.py` |
| **Tool Executor** | 工具注册、调用、结果回送 | `tools.py` |
| **ResearchMemory** | 三层记忆（Buffer + Entity + Findings） | `memory.py` |
| **LLM Client** | API 调用封装，支持多 Provider | `llm.py` |
| **Report** | Markdown 报告生成与持久化 | `report.py` |

### Agent 角色

| Agent | 角色 | 目标 |
|-------|------|------|
| 🗂️ **Planner** | 研究规划专家 | 分析需求，制定研究计划 |
| 🔬 **Researcher** | 高级技术研究员 | 深度调研，收集信息 |
| ✍️ **Writer** | 技术报告撰写专家 | 将调研结果写成结构化报告 |
| ✅ **Reviewer** | 技术审核专家 | 审核质量，输出改进版 |

---

## 快速开始

### 1. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的 API Key
# 默认使用 DeepSeek（OpenAI 兼容）
```

### 2. 安装

```bash
# 方式一：pip（推荐）
pip install -e .

# 方式二：uv（需预先安装 uv）
uv sync
```

### 3. 使用

```bash
# 命令行模式
python -m research_agent.main "你的研究主题"

# 示例
python -m research_agent.main "RAG 技术"
python -m research_agent.main "MCP 协议"

# 指定输出目录
python -m research_agent.main "Agent Memory" --output ./reports

# 交互模式
python -m research_agent.main --interactive
```

### 4. Docker 部署（推荐）

```bash
# 构建镜像（首次构建较慢，需下载基础镜像）
docker compose build

# 启动服务（FastAPI + 健康检查 + 自动重启）
docker compose up -d

# 查看启动状态
docker compose ps

# 查看日志
docker compose logs -f

# 调用 API
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "RAG 技术"}'

# 健康检查
curl http://localhost:8000/health

# 停止服务
docker compose down
```

> **容器化优势**：隔离运行环境、自动重启、资源限制（CPU/Memory）、输出持久化到本地 `./output`

#### 验证步骤

构建并启动后，确认一切正常：

```bash
# 1. 检查容器状态（应为 Up + healthy）
docker ps --filter name=research-agent

# 2. 测试健康接口
curl http://localhost:8000/health
# 返回: {"status":"ok","service":"ResearchAgent","version":"1.0.0"}

# 3. 访问 API 文档
open http://localhost:8000/docs
```

---

## 项目结构

```
ResearchAgent/
├── research_agent/               # 核心包
│   ├── __init__.py               # 包信息
│   ├── main.py                   # CLI 入口
│   ├── orchestrator.py           # Agent / Task / Crew 编排引擎
│   ├── agents.py                 # Agent 角色定义
│   ├── tools.py                  # 工具系统（注册 + 执行）
│   ├── memory.py                 # 三层记忆管理
│   ├── llm.py                    # LLM API 封装
│   └── report.py                 # 报告生成与保存
├── output/                       # 生成的报告（自动创建）
├── .env.example                  # 环境变量模板
├── pyproject.toml                # 项目配置
├── Dockerfile                    # 容器镜像定义（pip + 阿里云镜像加速）
├── docker-compose.yml            # 容器编排（含资源限制/健康检查）
├── .dockerignore                 # 容器构建忽略规则
└── README.md
```

---

## 设计理念

### 为什么手写？

| 方案 | 优点 | 缺点 |
|------|------|------|
| **CrewAI 框架** | 开箱即用 | 黑盒、Python 版本限制、难排查 |
| **手写编排引擎** | 完全可控、零依赖、可讲清原理 | 代码量稍多 |

**结论**：理解原理后可以用框架提效，但这个项目手写是为了展示对 Agent 架构的深入理解。

### Agent 协作模式

```
Sequential Pipeline（顺序流水线）：
  Planner → Researcher → Writer → Reviewer

  每个 Agent 接收前一个的输出作为上下文，
  在自己的角色范围内完成工作后传递给下一个。
```

### 工具调用

```
LLM 输出："TOOL_CALL: calculator | 235 * 47"
          ↓
  解析 → 执行 Python 函数 → 结果送回 LLM → 继续回答
```

### 记忆系统

| 层次 | 作用 |
|------|------|
| Entity Memory | 从对话中提取关键实体 |
| Findings | 研究发现的关键事实列表 |
| CircularBuffer | 保留最近 N 轮对话 |

---

## 运行示例

```
$ python -m research_agent.main "MCP 协议"

============================================================
  ResearchAgent v1.0.0
  研究主题：MCP 协议
============================================================

  🚀 启动 4 个 Agent，4 个任务

  📋 任务 1: 分析研究主题「MCP协议」，制定研究计划...
  🤖 [研究规划专家] 处理中...
  ✅ 完成 (1861 字)

  📋 任务 2: 执行研究计划，调研主题「MCP协议」...
  🤖 [高级技术研究员] 处理中...
  ✅ 完成 (6009 字)

  📋 任务 3: 撰写完整的技术报告...
  🤖 [技术报告撰写专家] 处理中...
  ✅ 完成 (6715 字)

  📋 任务 4: 审核并改进技术报告...
  🤖 [技术审核专家] 处理中...
  ✅ 完成 (7860 字)

============================================================
  ✅ 研究完成！报告已保存：
  📄 ./output/20260609_1513_什么是MCP协议.md
============================================================
```

---

## 路线图

- [x] 多 Agent 顺序编排
- [x] 工具调用系统
- [x] 三层记忆管理
- [x] Markdown 报告生成
- [x] Docker 容器化部署（单阶段构建 + docker-compose + 健康检查 + 资源限制）
- [ ] MCP 协议集成（Agent 间通信）
- [ ] 层级管理模式（Manager Agent）
- [ ] Web 界面（FastAPI + 前端）

---

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 运行环境 |
| DeepSeek API | LLM 推理（OpenAI 兼容） |
| pip / uv | 包管理（pip 国内镜像加速） |
| 零框架依赖 | 编排引擎、工具、记忆全部手写 |
| Docker / Docker Compose | 容器化部署（单阶段构建 + 资源限制 + 健康检查 + 自动重启） |

---

## Docker 容器化设计

### 架构

```
┌────────────────────────────────────────────┐
│           Docker 容器 (research-agent)       │
│                                            │
│  ┌────────────────┐   ┌─────────────────┐  │
│  │  uvicorn 服务    │   │  FastAPI 应用     │  │
│  │  (端口 8000)    │──→│  /api/research  │  │
│  │                │   │  /health        │  │
│  │                │   │  /api/reports   │  │
│  └────────────────┘   └────────┬────────┘  │
│                                │           │
│  ┌─────────────────────────────┴─────────┐  │
│  │      Agent 编排引擎                    │  │
│  │  Planner → Researcher → Writer → Reviewer │
│  └─────────────────────────────────────────┘  │
│                                │              │
│  ┌─────────────────────────────┴─────────┐   │
│  │      LLM API 调用 (出站)              │   │
│  └─────────────────────────────────────────┘  │
└──────────────────────┬─────────────────────────┘
                       │
              ┌────────┴────────┐
              │  卷挂载: output/  │
              │  报告持久化       │
              └─────────────────┘
```

### 关键设计

| 设计点 | 说明 |
|--------|------|
| **单阶段构建** | 基于 `python:3.12-slim`，配置阿里云 PyPI 镜像加速依赖下载 |
| **资源限制** | CPU 上限 2 核，内存上限 2G，防止 LLM 并发调用打爆宿主机 |
| **健康检查** | 每 30s 检查一次，失败 3 次自动重启 |
| **自动重启** | `unless-stopped` 策略，跟随 Docker Daemon 自动拉起 |
| **输出持久化** | `./output` 目录挂载到容器内，报告不随容器销毁而丢失 |
| **环境变量** | 通过 `.env` 文件传入 API Key，不硬编码在镜像中 |
