from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import AI_API_KEY, AI_MODEL, AI_PROVIDER


def _fallback_rewrite(text: str) -> str:
    cleaned = " ".join(text.split())
    replacements = {
        "worked on": "contributed to",
        "helped with": "supported",
        "responsible for": "managed",
    }
    for phrase, replacement in replacements.items():
        cleaned = re.sub(
            rf"\b{re.escape(phrase)}\b",
            lambda match: replacement.capitalize() if match.group(0)[0].isupper() else replacement,
            cleaned,
            flags=re.IGNORECASE,
        )
    return cleaned


def _request_openai(prompt: str) -> str:
    body = json.dumps({
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "Improve clarity and professional wording only. Preserve all facts. Never add skills, employers, metrics, outcomes, dates, or credentials. Return only the rewritten text."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")
    request = Request("https://api.openai.com/v1/chat/completions", data=body, headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read())
    return payload["choices"][0]["message"]["content"].strip()


def _request_gemini(prompt: str) -> str:
    import urllib.parse

    model = AI_MODEL if AI_MODEL.startswith("gemini-") else "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent?key={urllib.parse.quote(AI_API_KEY)}"
    body = json.dumps({"contents": [{"parts": [{"text": "Improve clarity and professional wording only. Preserve all facts. Never add skills, employers, metrics, outcomes, dates, or credentials. Return only the rewritten text.\n\n" + prompt}]}]}).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read())
    return payload["candidates"][0]["content"]["parts"][0]["text"].strip()


def improve_resume_text(text: str, kind: str) -> dict[str, str | bool]:
    prompt = f"Rewrite this resume {kind} without changing its factual meaning:\n\n{text}"
    if AI_API_KEY and AI_PROVIDER in {"openai", "gemini"}:
        try:
            improved = _request_openai(prompt) if AI_PROVIDER == "openai" else _request_gemini(prompt)
            if improved:
                return {"improved_text": improved, "mode": "ai", "provider": AI_PROVIDER, "notice": "AI-assisted wording. Review the result to confirm every statement remains accurate."}
        except Exception:
            pass

    return {
        "improved_text": _fallback_rewrite(text),
        "mode": "rule-based",
        "provider": "none",
        "notice": "AI enhancement unavailable. Showing rule-based wording only; no new qualifications or achievements were added.",
    }