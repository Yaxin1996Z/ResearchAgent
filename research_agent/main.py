"""
ResearchAgent CLI —— 多 Agent 研究助手

用法：
  python -m research_agent.main "你的研究主题"
  python -m research_agent.main "RAG技术" --output ./reports
  python -m research_agent.main "MCP协议" --kb-path ./my_docs
  python -m research_agent.main --interactive
"""

import sys
import argparse
import os
import re
from datetime import datetime

# Windows 终端 UTF-8 支持
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from . import __version__
from .tools import ToolExecutor, save_file, query_knowledge
from .memory import ResearchMemory
from .orchestrator import Agent, Task, Crew
from .agents import create_researcher, create_writer, create_reviewer, create_planner
from .report import save_report
from .rag import get_knowledge_base


# ============================================================
# 初始化
# ============================================================

def run_research(topic: str, output_dir: str = "", kb_path: str = "") -> str:
    """执行完整的研究流程"""

    # 初始化组件
    memory = ResearchMemory()
    memory.add_user_message(f"研究主题：{topic}")

    # 知识库（可能为空）
    kb = get_knowledge_base(repo_dir=kb_path)
    has_kb = kb.count() > 0
    if has_kb:
        print(f"  📚 知识库已加载：{kb.count()} 个片段")
    else:
        print("  📚 知识库为空，未注册检索工具")

    # 按角色分配工具 ============================================
    # 研究员：知识库（按主题匹配）+ 保存文件
    researcher_tools = ToolExecutor()

    # 知识库关键词匹配：只有 topic 涉及知识库内容时才注册检索工具
    KB_KEYWORDS = ["鲁迅", "阿Q", "狂人日记", "呐喊", "彷徨", "朝花夕拾",
                   "白鹿原", "陈忠实",
                   "毛泽东", "毛主席",
                   "中国近代史", "民国", "传记", "小说", "文学"]
    topic_match = any(kw in topic for kw in KB_KEYWORDS)

    if has_kb and topic_match:
        researcher_tools.register(query_knowledge)
        print(f"  📚 主题与知识库匹配，已注册检索工具")
    elif has_kb:
        print(f"  📚 知识库已加载但主题不匹配，未注册检索工具")

    # 写手：保存文件
    writer_tools = ToolExecutor()
    writer_tools.register(save_file)

    # 规划师、审核员：不需要工具
    planner_tools = ToolExecutor()
    reviewer_tools = ToolExecutor()

    # 创建 Agent
    researcher = create_researcher(researcher_tools, memory)
    writer = create_writer(writer_tools, memory)
    reviewer = create_reviewer(reviewer_tools, memory)
    planner = create_planner(planner_tools, memory)

    # 研究流程
    tasks = [
        Task(
            description=(
                f"分析研究主题「{topic}」，制定研究计划。\n"
                "输出结构化研究计划，包含：\n"
                "1. 研究目标\n"
                "2. 关键问题（3-5个）\n"
                "3. 研究范围\n"
                "4. 预期产出"
            ),
            agent=planner,
        ),
        Task(
            description=(
                f"执行研究计划，调研主题「{topic}」。\n"
                "如果有相关的本地文档，可以用 query_knowledge 工具查询知识库获取详细信息。\n"
                "你需要涵盖：基本原理、核心概念、主流方案、优缺点对比、适用场景。\n"
                "如果有代码示例更好。\n"
                "输出详细的调研结果。"
            ),
            agent=researcher,
        ),
        Task(
            description=(
                "基于前面的调研结果，撰写一份完整的技术报告。\n"
                "要求包含以下章节：\n"
                "1. Executive Summary（摘要）\n"
                "2. 背景介绍\n"
                "3. 核心概念与原理\n"
                "4. 主流方案对比\n"
                "5. 实践建议\n"
                "6. 参考资料\n\n"
                "格式要求：Markdown，使用表格对比方案，代码示例用 ``` 标注。"
            ),
            agent=writer,
        ),
        Task(
            description=(
                "审核并改进这份技术报告。\n"
                "检查：技术准确性、结构完整性、表达清晰度。\n"
                "输出改进后的最终完整报告。"
            ),
            agent=reviewer,
        ),
    ]

    crew = Crew(
        agents=[planner, researcher, writer, reviewer],
        tasks=tasks,
        memory=memory,
    )

    print(f"\n{'='*60}")
    print(f"  ResearchAgent v{__version__}")
    print(f"  研究主题：{topic}")
    print(f"  启动时间：{datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    final_report = crew.kickoff()

    # 保存报告
    filepath = save_report(topic, final_report, output_dir)
    print(f"\n{'='*60}")
    print(f"  ✅ 研究完成！报告已保存：")
    print(f"  📄 {filepath}")
    print(f"{'='*60}")

    return filepath


# ============================================================
# CLI
# ============================================================

def cli():
    parser = argparse.ArgumentParser(
        description="ResearchAgent - 多 Agent 研究助理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  research-agent "RAG技术"                           # 研究RAG技术
  research-agent "MCP协议" --output ./reports        # 指定输出目录
  research-agent --rebuild                            # 强制重建知识库索引
  research-agent "Transformer" --kb-path ./my_docs   # 指定知识库目录
  research-agent --interactive                        # 交互模式
        """,
    )
    parser.add_argument("topic", nargs="?", default="", help="研究主题")
    parser.add_argument("--output", "-o", default="", help="报告输出目录")
    parser.add_argument("--kb-path", default="", help="知识库文档目录路径")
    parser.add_argument(
        "--rebuild", action="store_true", help="强制重建知识库索引"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="交互模式"
    )
    parser.add_argument(
        "--version", "-v", action="store_true", help="显示版本"
    )

    args = parser.parse_args()

    if args.version:
        print(f"ResearchAgent v{__version__}")
        return

    # 强制重建知识库
    if args.rebuild:
        from .rag import get_knowledge_base
        kb = get_knowledge_base(repo_dir=args.kb_path)
        kb.rebuild()
        print(f"  ✅ 知识库已重建，共 {kb.count()} 个片段")
        return

    if args.interactive:
        print("ResearchAgent 交互模式（输入 q 退出）")
        while True:
            topic = input("\n🔍 研究主题：").strip()
            if topic.lower() in ("q", "quit", "exit"):
                break
            if topic:
                run_research(topic, args.output, args.kb_path)
        return

    if not args.topic:
        parser.print_help()
        return

    run_research(args.topic, args.output, args.kb_path)


def main():
    cli()


if __name__ == "__main__":
    main()
