"""Minimal command-line check for the Ollama integration."""

from llm import ask_llm


if __name__ == "__main__":
    for text in ask_llm("你好，你是谁？", stream=True):
        print(text, end="", flush=True)
    print()
