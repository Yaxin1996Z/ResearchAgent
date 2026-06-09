"""
LLM 调用封装 —— 统一管理 API 调用
"""

import os
from openai import OpenAI

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        model = os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")

        if not api_key:
            raise RuntimeError(
                "请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量"
            )

        _client = OpenAI(api_key=api_key, base_url=base_url)
        _client._model = model  # type: ignore

    return _client


def get_model() -> str:
    return os.getenv("OPENAI_MODEL_NAME", "deepseek-chat")


def call(prompt: str, system: str = "", temperature: float = 0.3) -> str:
    """调用 LLM 并返回文本"""
    client = get_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=get_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=4096,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[API 错误] {e}"
