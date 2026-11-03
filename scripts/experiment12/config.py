"""Models, cases, and repository paths."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream/lm_understand-logs"
SYSTEM = "Answer the user's request.\n"
MODELS = {
    "gpt-6-astra": "openai",
    "claude-opus-5-5": "anthropic",
    "claude-fable-5-1": "anthropic",
    "moonshotai/kimi-k3.1-pro": "openrouter",
    "google/gemini-4-argon": "openrouter",
}
CASES = {
    "pacman": 1,
    "breakout": 1,
    "pong": 1,
    "freeway": 1,
    "circle": 2,
    "square": 2,
    "triangle": 2,
}
EXPERIMENTS = {1: "exp1_which_game", 2: "exp2_diffusion"}
