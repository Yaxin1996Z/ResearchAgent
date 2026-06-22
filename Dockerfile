# ============================================================
# ResearchAgent — 多 Agent 研究助理 Docker 镜像
# 单阶段构建，国内镜像加速
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# 设置 pip 国内镜像（加速依赖下载）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

# 安装依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# 拷贝应用代码
COPY research_agent/ ./research_agent/
COPY run.py .
COPY pyproject.toml .

# 创建输出目录
RUN mkdir -p /app/output

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import research_agent; print('ok')" || exit 1

# 默认启动：FastAPI 服务
CMD ["uvicorn", "research_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
