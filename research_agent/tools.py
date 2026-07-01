"""
工具系统 —— Agent 可调用的工具

支持两种工具：
  1. 函数工具：通过 @tool 装饰器注册
  2. 记忆工具：读写 ResearchMemory
"""

import re
from typing import Any, Callable


# ============================================================
# 工具定义
# ============================================================

class Tool:
    """工具定义"""

    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func

    def run(self, *args, **kwargs) -> str:
        try:
            result = self.func(*args, **kwargs)
            return str(result)
        except Exception as e:
            return f"[工具错误] {e}"


def tool(name: str = "", description: str = ""):
    """工具装饰器"""
    def decorator(func):
        return Tool(
            name=name or func.__name__,
            description=description or func.__doc__ or "",
            func=func,
        )
    return decorator


# ============================================================
# 内置工具
# ============================================================

@tool(name="calculator", description="数学计算，输入表达式如 '2 + 3 * 4'")
def calculator(expression: str) -> str:
    return str(eval(expression))


@tool(name="save_file", description="保存文本到文件，参数格式：文件名 | 内容")
def save_file(args: str) -> str:
    """保存内容到 output 目录"""
    import os
    parts = args.split("|", 1)
    if len(parts) < 2:
        return "错误：格式应为 '文件名 | 内容'"
    filename = parts[0].strip()
    content = parts[1].strip()

    output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"文件已保存：{filepath}"


@tool(name="web_search", description="搜索互联网，输入搜索关键词，返回搜索结果标题和摘要")
def web_search(query: str) -> str:
    """搜索互联网，返回最新信息"""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                title = r.get("title", "")
                body = r.get("body", "")
                href = r.get("href", "")
                results.append(f"- {title}\n  {body}\n  {href}")
        if not results:
            return "没有找到相关结果。"
        return "搜索结果：\n" + "\n\n".join(results)
    except Exception as e:
        return f"[搜索出错] {e}"


@tool(name="query_knowledge", description="从本地知识库中搜索相关内容。知识库已预加载了本地文档，输入问题返回最相关的文档片段，可作为调研参考")
def query_knowledge(question: str) -> str:
    """从已加载的本地知识库中检索相关内容"""
    from .rag import get_knowledge_base
    kb = get_knowledge_base()
    return kb.query(question) or "知识库中没有相关内容。"


# ============================================================
# 工具执行器
# ============================================================

class ToolExecutor:
    """管理工具注册和调用"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def register_all(self, tools: list[Tool]):
        for t in tools:
            self.register(t)

    def get_tools_prompt(self) -> str:
        """生成供 LLM 使用的工具描述"""
        if not self._tools:
            return ""
        lines = ["可用工具："]
        for name, t in self._tools.items():
            lines.append(f"  - {t.name}: {t.description}")
        lines.append("调用格式：TOOL_CALL: 工具名 | 参数")
        return "\n".join(lines)

    def execute_from_text(self, text: str) -> tuple[str, bool]:
        """解析文本中的 TOOL_CALL 并执行，返回 (执行结果, 是否调用了工具)"""
        match = re.search(r"TOOL_CALL:\s*(\w+)\s*\|\s*(.+)", text, re.MULTILINE)
        if not match:
            return "", False

        name = match.group(1)
        args = match.group(2).strip()

        tool = self._tools.get(name)
        if not tool:
            return f"错误：未知工具 '{name}'", True

        result = tool.run(args)
        return result, True

    @property
    def tool_list(self) -> list[Tool]:
        return list(self._tools.values())
