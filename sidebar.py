"""Sidebar controls and conversation management for the Streamlit app."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st


DEFAULT_MODEL = "deepseek-r1:14b"
CONVERSATION_DIR = Path(__file__).resolve().parent / "conversations"


def init_session_state() -> None:
    """Create the session keys used by the chat UI."""
    if "conversations" not in st.session_state:
        st.session_state.conversations = load_conversations()
        if st.session_state.conversations:
            st.session_state.active_conversation_id = next(
                reversed(st.session_state.conversations)
            )
        else:
            _create_empty_conversation()

    if "active_conversation_id" not in st.session_state:
        if st.session_state.conversations:
            st.session_state.active_conversation_id = next(iter(st.session_state.conversations))
        else:
            _create_empty_conversation()

    if "model_name" not in st.session_state:
        st.session_state.model_name = DEFAULT_MODEL

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = (
            "你是一个严谨、清晰、实用的 AI 助手。默认使用中文回答。"
        )


def render_sidebar() -> None:
    """Render ChatGPT-like sidebar navigation and settings."""
    st.sidebar.markdown("### 我的 AI 助手")

    if st.sidebar.button("+ 新对话", use_container_width=True, type="primary"):
        _discard_empty_conversations()
        _create_empty_conversation()
        st.rerun()

    st.sidebar.markdown("#### 对话")
    visible_conversations = [
        (conversation_id, conversation)
        for conversation_id, conversation in st.session_state.conversations.items()
        if conversation["messages"]
    ]

    if not visible_conversations:
        st.sidebar.caption("暂无历史对话")

    for conversation_id, conversation in visible_conversations[::-1]:
        title = conversation["title"]
        label = title if len(title) <= 18 else f"{title[:18]}..."
        is_active = conversation_id == st.session_state.active_conversation_id
        with st.sidebar.container(border=True):
            cols = st.columns([0.88, 0.12], gap="small")
            if cols[0].button(
                label,
                key=f"conversation-{conversation_id}",
                use_container_width=True,
                type="secondary",
                help="当前对话" if is_active else None,
            ):
                _discard_empty_conversations()
                st.session_state.active_conversation_id = conversation_id
                st.rerun()

            with cols[1].popover(" ", use_container_width=True):
                st.caption("对话操作")
                if st.button("清空", key=f"clear-{conversation_id}", use_container_width=True):
                    clear_conversation(conversation_id)
                    st.rerun()
                if st.button("删除", key=f"delete-{conversation_id}", use_container_width=True):
                    delete_conversation(conversation_id)
                    st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("#### 模型设置")
    st.session_state.model_name = st.sidebar.text_input(
        "Ollama 模型",
        value=st.session_state.model_name,
        help="例如 deepseek-r1:14b、llama3.1、qwen2.5 等本机 Ollama 已安装模型。",
    )
    st.session_state.temperature = st.sidebar.slider(
        "创造性",
        min_value=0.0,
        max_value=1.5,
        value=float(st.session_state.temperature),
        step=0.1,
    )
    st.session_state.system_prompt = st.sidebar.text_area(
        "系统提示词",
        value=st.session_state.system_prompt,
        height=120,
    )


def get_active_conversation() -> dict:
    """Return the currently selected conversation."""
    return st.session_state.conversations[st.session_state.active_conversation_id]


def update_title_from_prompt(prompt: str) -> None:
    """Use the first user prompt as the conversation title."""
    conversation = get_active_conversation()
    if conversation["title"] == "新对话":
        cleaned = " ".join(prompt.strip().split())
        conversation["title"] = cleaned[:24] or "新对话"


def export_markdown(conversation: dict) -> str:
    """Build a Markdown export for the active conversation."""
    lines = [
        f"# {conversation['title']}",
        "",
        f"- 创建时间: {conversation['created_at']}",
        f"- 模型: {st.session_state.model_name}",
        "",
    ]
    for message in conversation["messages"]:
        role = "用户" if message["role"] == "user" else "助手"
        lines.extend([f"## {role}", "", message["content"], ""])
    return "\n".join(lines)


def load_conversations() -> dict[str, dict[str, Any]]:
    """Load saved conversations from local JSON files."""
    CONVERSATION_DIR.mkdir(exist_ok=True)
    conversations: dict[str, dict[str, Any]] = {}
    for path in sorted(CONVERSATION_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        conversation_id = str(data.get("id") or path.stem)
        messages = data.get("messages")
        if not isinstance(messages, list) or not messages:
            continue

        normalized_messages = _normalize_loaded_messages(messages)
        if not normalized_messages:
            continue

        conversations[conversation_id] = {
            "title": str(data.get("title") or "新对话"),
            "messages": normalized_messages,
            "created_at": str(data.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M")),
            "updated_at": str(data.get("updated_at") or ""),
        }
    return conversations


def save_conversation(conversation_id: str | None = None) -> None:
    """Persist a non-empty conversation to a local JSON file."""
    conversation_id = conversation_id or st.session_state.active_conversation_id
    conversation = st.session_state.conversations[conversation_id]
    if not conversation["messages"]:
        delete_conversation_file(conversation_id)
        return

    CONVERSATION_DIR.mkdir(exist_ok=True)
    conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {
        "id": conversation_id,
        "title": conversation["title"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
        "messages": conversation["messages"],
    }
    path = CONVERSATION_DIR / f"{conversation_id}.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_conversation(conversation_id: str) -> None:
    """Clear a conversation and remove it from the visible history."""
    if conversation_id in st.session_state.conversations:
        st.session_state.conversations[conversation_id]["messages"] = []
        st.session_state.conversations[conversation_id]["title"] = "新对话"
    delete_conversation_file(conversation_id)
    _select_fallback_conversation(conversation_id)


def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation from memory and disk."""
    st.session_state.conversations.pop(conversation_id, None)
    delete_conversation_file(conversation_id)
    _select_fallback_conversation(conversation_id)


def delete_conversation_file(conversation_id: str) -> None:
    path = CONVERSATION_DIR / f"{conversation_id}.json"
    if path.exists():
        path.unlink()


def _new_conversation_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def _create_empty_conversation() -> None:
    conversation_id = _new_conversation_id()
    st.session_state.conversations[conversation_id] = {
        "title": "新对话",
        "messages": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": "",
    }
    st.session_state.active_conversation_id = conversation_id


def _discard_empty_conversations() -> None:
    for conversation_id, conversation in list(st.session_state.conversations.items()):
        if not conversation["messages"]:
            st.session_state.conversations.pop(conversation_id, None)


def _select_fallback_conversation(deleted_or_cleared_id: str) -> None:
    non_empty_ids = [
        conversation_id
        for conversation_id, conversation in st.session_state.conversations.items()
        if conversation["messages"]
    ]
    if non_empty_ids:
        if st.session_state.active_conversation_id == deleted_or_cleared_id:
            st.session_state.active_conversation_id = non_empty_ids[-1]
    else:
        st.session_state.conversations = {}
        _create_empty_conversation()


def _normalize_loaded_messages(messages: list[Any]) -> list[dict[str, str]]:
    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "user"))
        content = str(message.get("content", ""))
        if role in {"user", "assistant", "system"} and content:
            normalized.append({"role": role, "content": content})
    return normalized
