"""Human-readable result storage: one prompt and latest completed reply per model."""

import json
from pathlib import Path

from scripts.experiment12.config import CASES, ROOT
from scripts.experiment12.providers import extract
from scripts.experiment12.scoring import score

DETAILS = "\n\n<details>\n<summary>Run settings and assistant evaluation</summary>\n\n"


def case_directory(case, root=None):
    return (root or ROOT / "results") / f"experiment-{CASES[case]}-{case}"


def write_transcript(
    provider, request, response, case, elapsed_seconds, *, root=None, review=None
):
    answer, complete = extract(provider, response)
    if not complete or not answer.strip():
        raise ValueError("Only completed responses can replace a retained result")
    messages = request.get("input", request.get("messages"))
    prompt = messages[0]["content"]
    system = request.get("instructions", request.get("system", ""))
    directory = case_directory(case, root)
    directory.mkdir(parents=True, exist_ok=True)
    prompt_file = directory / "prompt.txt"
    if prompt_file.exists() and prompt_file.read_text() != prompt:
        raise ValueError(
            "Prompt differs from the retained case; use a separate results root"
        )
    kind = "game" if CASES[case] == 1 else "shape"
    evaluation = score(answer, kind, case)
    if review:
        evaluation["manual_review"] = review
    settings = {
        k: v
        for k, v in request.items()
        if k not in ("input", "messages", "instructions", "system")
    }
    metadata = {
        "experiment": CASES[case],
        "case": case,
        "model": request["model"],
        "provider": provider,
        "status": "complete",
        "elapsed_seconds": elapsed_seconds,
        "request_settings": settings,
        "usage": response.get("usage"),
        "evaluation_author": "OpenAI assistant (Codex); not user-authored",
        "evaluation": evaluation,
    }
    reasoning = []
    if provider == "anthropic":
        for block in response.get("content", []):
            if block.get("type") == "thinking":
                reasoning.append(block["thinking"])
            elif block.get("type") == "redacted_thinking":
                reasoning.append("[The provider redacted this thinking block.]")
    else:
        for item in response.get("output", []):
            if item.get("type") == "reasoning":
                for block in item.get("summary", []) + item.get("content", []):
                    if "text" in block:
                        reasoning.append(block["text"])
    text = (
        f"# {request['model']} — experiment {CASES[case]}: {case}\n\n"
        f"Provider: {provider}. Status: complete.\n\n"
        "## System instruction\n\n" + system.strip() + "\n\n"
        "## User prompt\n\n[Complete prompt, including weights](prompt.txt)\n\n"
        "## Reasoning returned by the provider\n\n"
        + ("\n\n".join(reasoning) or "(None returned.)")
        + "\n\n"
        "## Assistant response\n\n"
        + answer
        + DETAILS
        + "```json\n"
        + json.dumps(metadata, indent=2, ensure_ascii=False)
        + "\n```\n\n</details>\n"
    )
    prompt_file.write_text(prompt)
    path = directory / f"{request['model'].split('/')[-1]}-transcript.md"
    path.write_text(text)
    return path


def read_transcript(path):
    text = Path(path).read_text()
    body, details = text.rsplit(DETAILS, 1)
    metadata = json.loads(details.split("```json\n", 1)[1].split("\n```", 1)[0])
    answer = body.split("## Assistant response\n\n", 1)[1].rstrip("\n")
    return metadata, answer
