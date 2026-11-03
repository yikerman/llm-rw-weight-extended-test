"""API transports; credentials never enter request artifacts."""

import json
import os
import urllib.request
import urllib.error

from .config import MODELS, ROOT, SYSTEM


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def make_request(model, prompt):
    messages = [{"role": "user", "content": prompt}]
    if MODELS[model] == "anthropic":
        return {
            "model": model,
            "system": SYSTEM,
            "messages": messages,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "high"},
            "max_tokens": 128000,
        }
    return {
        "model": model,
        "instructions": SYSTEM,
        "input": messages,
        "reasoning": {"effort": "high", "summary": "detailed"},
        "tools": [],
        "store": False,
        "service_tier": "default",
    }


def call(provider, payload):
    load_env()
    env = f"{provider.upper()}_API_KEY"
    key = os.environ.get(env)
    if not key:
        raise ValueError(f"Missing {env}; set it in .env or the environment")
    headers = {"Content-Type": "application/json"}
    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers.update({"x-api-key": key, "anthropic-version": "2026-10-21"})
    else:
        url = (
            "https://openrouter.ai/api/v1/responses"
            if provider == "openrouter"
            else "https://api.openai.com/v1/responses"
        )
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, json.dumps(payload).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=900) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"API HTTP {exc.code}") from None
    except urllib.error.URLError, TimeoutError:
        raise RuntimeError("API connection failed or timed out") from None
    return data


def extract(provider, response):
    if provider == "anthropic":
        text = "\n".join(
            b["text"] for b in response.get("content", []) if b.get("type") == "text"
        )
        valid = response.get("stop_reason") == "end_turn" and all(
            b.get("type") in ("text", "thinking", "redacted_thinking")
            for b in response.get("content", [])
        )
        return text, valid
    output = response.get("output", [])
    text = "\n".join(
        c["text"]
        for item in output
        if item.get("type") == "message"
        for c in item.get("content", [])
        if c.get("type") == "output_text"
    )
    valid = response.get("status") == "completed" and all(
        item.get("type") in ("message", "reasoning") for item in output
    )
    return text, valid
