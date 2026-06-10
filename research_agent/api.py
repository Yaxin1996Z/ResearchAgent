"""
ResearchAgent FastAPI 服务
    将多 Agent 研究助手包装为 RESTful API
"""

import sys
import os
from typing import Optional

# Windows UTF-8 支持
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv()

from . import __version__
from .main import run_research

# ============================================================
# FastAPI 应用实例
# ============================================================

app = FastAPI(
    title="ResearchAgent API",
    description="多 Agent 研究助理系统 - RESTful API 服务",
    version=__version__,
)


# ============================================================
# Pydantic 模型（请求/响应）
# ============================================================

class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="研究主题")
    output_dir: Optional[str] = Field("", description="报告输出目录（可选）")


class ReportItem(BaseModel):
    filename: str
    topic: str
    date: str
    size: int


class ReportList(BaseModel):
    reports: list[ReportItem]


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ResearchAgent",
        "version": __version__,
    }


# ============================================================
# 执行研究
# ============================================================

@app.post("/api/research")
def research(req: ResearchRequest):
    """提交研究主题，执行完整的多 Agent 研究流程，返回 Markdown 报告"""
    try:
        filepath = run_research(req.topic, req.output_dir)

        # 读取生成的报告
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "status": "ok",
            "topic": req.topic,
            "filepath": filepath,
            "report": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"研究过程出错：{str(e)}")


# ============================================================
# 列出所有报告
# ============================================================

@app.get("/api/reports", response_model=ReportList)
def list_reports():
    """列出所有已生成的报告文件"""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    if not os.path.exists(output_dir):
        return ReportList(reports=[])

    reports = []
    for fname in sorted(os.listdir(output_dir), reverse=True):
        if not fname.endswith(".md"):
            continue
        filepath = os.path.join(output_dir, fname)
        # 从文件名解析 topic 和 date
        parts = fname.replace(".md", "").split("_", 1)
        date_str = parts[0] if len(parts) > 1 else ""
        topic = parts[1] if len(parts) > 1 else parts[0]

        reports.append(ReportItem(
            filename=fname,
            topic=topic,
            date=date_str,
            size=os.path.getsize(filepath),
        ))

    return ReportList(reports=reports)


# ============================================================
# 获取单篇报告
# ============================================================

@app.get("/api/reports/{filename}", response_class=PlainTextResponse)
def get_report(filename: str):
    """获取指定报告文件的原始 Markdown 内容"""
    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    # 防止路径穿越
    safe_name = os.path.basename(filename)
    filepath = os.path.join(output_dir, safe_name)

    if not os.path.exists(filepath) or not safe_name.endswith(".md"):
        raise HTTPException(status_code=404, detail="报告未找到")

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()
