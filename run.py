"""
ResearchAgent API 启动入口

用法：
    python run.py              # 启动服务（默认 8000 端口）
    python run.py --port 8080  # 指定端口
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # noqa

import uvicorn


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    print(f"  ResearchAgent API 启动")
    print(f"  ===========================")
    print(f"  地址: http://localhost:{port}")
    print(f"  文档: http://localhost:{port}/docs")
    print(f"  健康: http://localhost:{port}/health")
    print()
    uvicorn.run("research_agent.api:app", host="0.0.0.0", port=port, reload=True)
