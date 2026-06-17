"""LLM integration helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def ask_llm(
    messages: list[dict[str, str]] | str,
    *,
    model: str = "deepseek-r1:14b",
    temperature: float = 0.7,
    stream: bool = True,
) -> Iterable[str]:
    """Send chat messages to Ollama and yield response text chunks."""
    normalized_messages = _normalize_messages(messages)

    try:
        from ollama import chat
    except ModuleNotFoundError:
        yield (
            "未安装 `ollama` Python 包。请先运行：\n\n"
            "```bash\npip3 install ollama\n```"
        )
        return

    try:
        response = chat(
            model=model,
            messages=normalized_messages,
            stream=stream,
            options={"temperature": temperature},
        )

        if stream:
            for chunk in response:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        else:
            yield response.get("message", {}).get("content", "")
    except Exception as exc:  # Ollama connection/model errors should render in the UI.
        yield (
            "调用本地 Ollama 失败。\n\n"
            f"- 模型: `{model}`\n"
            f"- 错误: `{exc}`\n\n"
            "请确认 Ollama 已启动，并且该模型已经下载。"
        )


def _normalize_messages(messages: list[dict[str, Any]] | str) -> list[dict[str, str]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]

    normalized = []
    for message in messages:
        role = str(message.get("role", "user"))
        content = str(message.get("content", ""))
        if content:
            normalized.append({"role": role, "content": content})
    return normalized
