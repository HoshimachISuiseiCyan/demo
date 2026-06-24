from __future__ import annotations

import json
import os
import requests


# =========================
# 基类
# =========================
class LLMService:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, system_prompt: str, user_prompt: str):
        text = self.generate(system_prompt, user_prompt)

        print("🧠 LLM原始返回：", text)  # 👈关键调试

        try:
            return json.loads(text)
        except Exception:
            # 容错提取 JSON
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end + 1])

            raise RuntimeError(f"LLM返回非JSON: {text}")


# =========================
# 豆包（字节）实现
# =========================
class DoubaoLLMService(LLMService):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "")).rstrip("/")

        if not self.api_key:
            raise RuntimeError("❌ 未配置 LLM_API_KEY")
        if not self.model:
            raise RuntimeError("❌ 未配置 LLM_MODEL")
        if not self.base_url:
            raise RuntimeError("❌ 未配置 LLM_BASE_URL")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/responses"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        }

        print("🚀 正在请求AI...")
        print("👉 Prompt片段:", user_prompt[:120])

        resp = requests.post(url, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            raise RuntimeError(f"LLM请求失败: {resp.status_code} {resp.text}")

        data = resp.json()

        return self._extract_text(data)

    def _extract_text(self, data: dict) -> str:
        try:
            for item in data.get("output", []):
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            return c.get("text", "")
        except Exception as e:
            raise RuntimeError(f"解析失败: {e}")

        raise RuntimeError(f"未知LLM结构: {data}")


# =========================
# 兜底（不要用）
# =========================
class UnavailableLLMService(LLMService):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("❌ LLM 未配置")