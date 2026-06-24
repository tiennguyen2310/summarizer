import os
from typing import Iterable

import requests
from dotenv import load_dotenv
load_dotenv()

class LLMSummarizer:
    def __init__(
        self,
        model_path=None,
        use_mock=False,
        llama_cli=None,
        max_tokens=160,
        ctx_size=4096,
        gpu_layers=0,
        timeout=180,
    ):
        self.use_mock = use_mock
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", max_tokens))
        self.timeout = int(os.getenv("OPENROUTER_TIMEOUT", timeout))
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.2"))
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.model = os.getenv("OPENROUTER_MODEL", "~openai/gpt-latest")
        self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "Summarizer")
        self.current_model_path = self.model

    def load_model(self, model_path):
        if not model_path:
            return "Error loading model: missing OpenRouter model slug."

        self.model = model_path.strip()
        self.current_model_path = self.model
        return f"Using OpenRouter model: {self.model}"

    def summarize(self, text, topic=None, style="item"):
        if self.use_mock:
            return f"[FAKE SUMMARY] {text[:120]}"

        if not self.api_key:
            return "OpenRouter API key missing. Set OPENROUTER_API_KEY or enable USE_MOCK_LLM."

        prompt = self._build_item_prompt(text=text, topic=topic, style=style)
        return self._chat(prompt, max_tokens=self.max_tokens)

    def summarize_collection(self, items: Iterable[dict], topic=None, cross_media=False):
        if self.use_mock:
            first = next(iter(items), {"body": ""})
            return f"[FAKE COLLECTION SUMMARY] {str(first.get('body', ''))[:120]}"

        if not self.api_key:
            return "OpenRouter API key missing. Set OPENROUTER_API_KEY or enable USE_MOCK_LLM."

        prompt = self._build_collection_prompt(list(items), topic=topic, cross_media=cross_media)
        return self._chat(prompt, max_tokens=self.max_tokens)

    def _chat(self, prompt, max_tokens):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-OpenRouter-Title": self.app_name,
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a concise, factual summarizer. Use only the provided text and do not add preambles.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            return f"OpenRouter request failed: {exc}"

        if response.status_code >= 400:
            return f"OpenRouter error {response.status_code}: {response.text.strip()}"

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "OpenRouter returned no completion."

        message = choices[0].get("message", {})
        content = message.get("content", "")
        return self._clean_output(content)

    def _build_item_prompt(self, text, topic=None, style="item"):
        topic_line = f"Topic: {topic}" + chr(10) if topic else ""
        return f"""{topic_line}Summarize this {style} in exactly 2 short sentences.
Focus on the main facts only.

Source text:
{text}"""

    def _build_collection_prompt(self, items, topic=None, cross_media=False):
        topic_line = f"Topic: {topic}" + chr(10) if topic else ""
        source_lines = []
        for index, item in enumerate(items[:5], start=1):
            subject = item.get("subject", f"Item {index}")
            body = item.get("body", "")
            source = item.get("source", "text")
            content_type = item.get("content_type", "text")
            source_lines.append(
                f"[{index}] source={source} type={content_type} title={subject}" + chr(10) + body
            )

        media_hint = (
            "Blend institutional facts from text/news with on-the-ground video transcript reactions."
            if cross_media
            else "Blend the sources into a single summary."
        )

        sources_block = (chr(10) + chr(10)).join(source_lines)
        return f"""{topic_line}You are combining up to 5 source snippets into one cohesive summary.
{media_hint}
Write:
1. One short headline sentence.
2. Three bullets: facts, reactions, and what is still uncertain.
Keep it grounded in the snippets below and do not invent details.

{sources_block}"""

    def _clean_output(self, text):
        return " ".join((text or "").split())

