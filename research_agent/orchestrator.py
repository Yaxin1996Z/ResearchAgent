"""
编排引擎 —— Agent / Task / Crew 核心

设计：
  Agent  = 一个 LLM 角色 + 工具
  Task   = 一个任务单元（描述 + 分配给谁）
  Crew   = 任务调度器（支持 sequential / hierarchical）
"""

import re
from typing import Optional

from . import llm
from .tools import ToolExecutor
from .memory import ResearchMemory


# ============================================================
# Agent
# ============================================================

class Agent:
    """Agent = 角色设定 + 工具 + 记忆访问"""

    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str = "",
        tools: Optional[ToolExecutor] = None,
        memory: Optional[ResearchMemory] = None,
    ):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools
        self.memory = memory

    def build_system_prompt(self) -> str:
        prompt = f"你是{self.role}。\n目标：{self.goal}"
        if self.backstory:
            prompt += f"\n\n{self.backstory}"
        if self.tools:
            prompt += f"\n\n{self.tools.get_tools_prompt()}"
        return prompt

    def run(self, task: str, context: str = "") -> str:
        """执行任务（自带工具调用循环）"""

        system = self.build_system_prompt()

        user_msg = f"当前任务：{task}"
        if context:
            user_msg += f"\n\n可以参考以下上下文：\n{context}"

        # 如果有记忆，注入记忆上下文
        if self.memory:
            mem_ctx = self.memory.get_context()
            if mem_ctx:
                user_msg = f"{mem_ctx}\n\n{user_msg}"

        print(f"  🤖 [{self.role}] 处理中...")
        result = llm.call(user_msg, system)

        # 工具调用循环（最多 3 轮）
        if self.tools:
            for _ in range(3):
                tool_result, has_call = self.tools.execute_from_text(result)
                if not has_call:
                    break
                print(f"    🔧 调工具 -> {tool_result[:50]}...")
                result = llm.call(
                    f"{user_msg}\n\n---\n{result}\n\n工具返回：{tool_result}\n\n请基于结果继续。",
                    system,
                )

        return result


# ============================================================
# Task
# ============================================================

class Task:
    """一个任务单元"""

    def __init__(self, description: str, agent: Agent, expected_output: str = "文本"):
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.output: Optional[str] = None

    def execute(self, context: str = "") -> str:
        self.output = self.agent.run(self.description, context)
        return self.output


# ============================================================
# Crew
# ============================================================

class Crew:
    """任务调度器"""

    def __init__(self, agents: list[Agent], tasks: list[Task]):
        self.agents = agents
        self.tasks = tasks
        self._context = ""

    def kickoff(self) -> str:
        """顺序执行所有任务，前一个输出传给后一个"""
        print(f"\n  🚀 启动 {len(self.agents)} 个 Agent，{len(self.tasks)} 个任务\n")

        for agent in self.agents:
            print(f"    👤 {agent.role}")
        print()

        final = ""
        for i, task in enumerate(self.tasks):
            print(f"  📋 任务 {i+1}: {task.description[:50]}...")
            output = task.execute(context=self._context)
            print(f"  ✅ 完成 ({len(output)} 字)")
            self._context = output
            final = output

        return final
