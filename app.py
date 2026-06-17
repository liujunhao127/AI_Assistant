"""A ChatGPT-style Streamlit interface for a local Ollama assistant."""

from __future__ import annotations

import importlib
from html import escape

import streamlit as st

from llm import ask_llm
import sidebar


sidebar = importlib.reload(sidebar)


st.set_page_config(
    page_title="我的 AI 助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --assistant-bg: #f7f7f8;
            --assistant-border: #e5e5e5;
            --assistant-text: #202123;
            --assistant-muted: #6b7280;
            --sidebar-bg: #f7f7f8;
            --button-bg: #ffffff;
            --button-hover: #ececf1;
            --conversation-hover: #f1f1f3;
        }

        .stApp {
            background: #ffffff;
            color: var(--assistant-text);
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar-bg);
            border-right: 1px solid var(--assistant-border);
        }

        [data-testid="stSidebar"] * {
            color: var(--assistant-text);
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] textarea {
            color: #111827 !important;
            background: #ffffff !important;
            border-radius: 8px;
        }

        [data-testid="stSidebar"] .stSlider * {
            color: var(--assistant-text);
        }

        [data-testid="stSidebar"] button {
            background: transparent;
            border: 1px solid transparent;
            color: var(--assistant-text) !important;
            box-shadow: none;
            min-height: 2.35rem;
        }

        [data-testid="stSidebar"] button:hover {
            background: var(--button-hover);
            border-color: transparent;
            color: var(--assistant-text) !important;
        }

        [data-testid="stSidebar"] button[kind="primary"] {
            background: var(--button-bg);
            border: 1px solid var(--assistant-border);
            color: var(--assistant-text) !important;
        }

        [data-testid="stSidebar"] button[kind="secondary"] {
            background: transparent;
            border-color: transparent;
            color: var(--assistant-text) !important;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #e1e3e6;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.1rem 0.25rem;
            margin-bottom: 0.45rem;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:hover {
            background: var(--conversation-hover);
            border-color: #d8dbe0;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button {
            min-height: 2rem;
            padding: 0.25rem 0.45rem;
            text-align: left;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button p {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            text-align: left;
            width: 100%;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] button:has(p:empty) {
            background: transparent !important;
            border: 0 !important;
            min-width: 0;
            padding: 0;
            opacity: 0;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]:hover button:has(p:empty) {
            opacity: 0.35;
        }

        .block-container {
            max-width: 920px;
            padding-top: 2rem;
            padding-bottom: 8rem;
        }

        .chat-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid var(--assistant-border);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }

        .chat-title {
            font-size: 1.15rem;
            font-weight: 650;
        }

        .chat-subtitle {
            margin-top: 0.2rem;
            color: var(--assistant-muted);
            font-size: 0.9rem;
        }

        .welcome {
            text-align: center;
            padding: 9vh 0 2rem;
        }

        .welcome h1 {
            font-size: clamp(2rem, 5vw, 3.2rem);
            line-height: 1.1;
            margin-bottom: 0.75rem;
            letter-spacing: 0;
        }

        .welcome p {
            color: var(--assistant-muted);
            font-size: 1.02rem;
            margin-bottom: 2rem;
        }

        .prompt-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0 auto;
            max-width: 760px;
        }

        .prompt-card {
            border: 1px solid var(--assistant-border);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            text-align: left;
            background: #ffffff;
            color: #374151;
            min-height: 84px;
        }

        .prompt-card strong {
            display: block;
            color: #111827;
            margin-bottom: 0.3rem;
        }

        [data-testid="stChatMessage"] {
            border-radius: 0;
            padding: 1rem 0;
            border-bottom: 1px solid #f1f1f1;
        }

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            background: var(--assistant-bg);
            box-shadow: 0 0 0 100vmax var(--assistant-bg);
            clip-path: inset(0 -100vmax);
        }

        .stChatInput {
            max-width: 920px;
            margin: 0 auto;
            background: transparent !important;
        }

        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"],
        [data-testid="stChatInputContainer"],
        [data-testid="stChatInput"] {
            background: transparent !important;
            box-shadow: none !important;
            border: 0 !important;
        }

        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] > div,
        [data-testid="stChatInput"] > div {
            background: transparent !important;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] textarea {
            border-radius: 14px;
            border: 1px solid #d1d5db;
            background: #ffffff !important;
            box-shadow: none !important;
            min-height: 52px;
        }

        @media (max-width: 700px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .chat-header {
                align-items: flex-start;
                flex-direction: column;
            }

            .prompt-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(conversation: dict) -> None:
    title = escape(conversation["title"])
    model_name = escape(st.session_state.model_name)
    st.markdown(
        f"""
        <div class="chat-header">
            <div>
                <div class="chat-title">{title}</div>
                <div class="chat-subtitle">模型：{model_name}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome">
            <h1>今天想聊点什么？</h1>
            <p>可以提问、写作、总结资料、生成代码或梳理方案。</p>
            <div class="prompt-grid">
                <div class="prompt-card"><strong>整理思路</strong>把一个复杂问题拆成可执行步骤</div>
                <div class="prompt-card"><strong>代码助手</strong>解释报错、改进函数或生成测试用例</div>
                <div class="prompt-card"><strong>写作润色</strong>改写邮件、报告、文案或学习笔记</div>
                <div class="prompt-card"><strong>学习陪练</strong>用问答方式理解一个新概念</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_model_messages(messages: list[dict]) -> list[dict]:
    model_messages = []
    system_prompt = st.session_state.system_prompt.strip()
    if system_prompt:
        model_messages.append({"role": "system", "content": system_prompt})
    model_messages.extend(messages)
    return model_messages


def main() -> None:
    sidebar.init_session_state()
    apply_style()
    sidebar.render_sidebar()

    conversation = sidebar.get_active_conversation()
    render_header(conversation)

    if conversation["messages"]:
        st.download_button(
            "导出 Markdown",
            data=sidebar.export_markdown(conversation),
            file_name=f"{conversation['title']}.md",
            mime="text/markdown",
        )
    else:
        render_welcome()

    for message in conversation["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("给 AI 助手发送消息"):
        sidebar.update_title_from_prompt(prompt)
        conversation = sidebar.get_active_conversation()
        conversation["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = ask_llm(
                build_model_messages(conversation["messages"]),
                model=st.session_state.model_name,
                temperature=st.session_state.temperature,
                stream=True,
            )
            answer = st.write_stream(stream)

        conversation["messages"].append({"role": "assistant", "content": answer})
        sidebar.save_conversation()
        st.rerun()


if __name__ == "__main__":
    main()
