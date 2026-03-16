from __future__ import annotations

import json

from litellm import acompletion

from khire.config import settings


class LLMClient:
    def __init__(self, model: str | None = None):
        self.model = model or settings.default_llm_model

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await acompletion(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> dict:
        raw = await self.complete(prompt, system=system, temperature=temperature)
        return json.loads(raw)
