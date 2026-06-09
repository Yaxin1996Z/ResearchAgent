"""
报告生成 —— 将研究成果保存为标准 Markdown 文件
"""

import re
import os
from datetime import datetime


def generate_filename(topic: str) -> str:
    """根据主题生成文件名"""
    safe_name = re.sub(r"[^\w一-鿿]", "_", topic)[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{date_str}_{safe_name}.md"


def save_report(
    topic: str,
    content: str,
    output_dir: str = "",
) -> str:
    """保存报告到文件，返回文件路径"""
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    filename = generate_filename(topic)
    filepath = os.path.join(output_dir, filename)

    # 添加元数据头
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"""---
title: "{topic}"
generated_by: "ResearchAgent"
date: "{now}"
---

"""

    full_content = header + content

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    return filepath
