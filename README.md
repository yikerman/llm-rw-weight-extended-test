# Weight Reading On Other Models

Do other models share Astra's ability to infer a neural network's behavior from
its weights? This project repeats experiments 1–2 from
[Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/)
with GPT-6 Astra, Claude Opus 5.5, Claude Fable 5.1, Kimi K3.1 Pro, and
Gemini 4 Argon.

See the [report](report/replication.pdf) ([LaTeX](report/replication.tex)).
Prompts and latest completed transcripts are in `results/experiment-{number}-{case}/`.
The evaluation is assistant-authored.

## Run

```sh
uv sync
git submodule update --init --recursive
```

Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `OPENROUTER_API_KEY` in `.env`
(see `.env.example`). Kimi and Gemini use OpenRouter; the others use their official APIs.

```sh
uv run python scripts/experiment12/run.py --model gpt-6-astra
uv run python scripts/experiment12/run.py --model claude-opus-5-5
uv run python scripts/experiment12/run.py --model claude-fable-5-1
uv run python scripts/experiment12/run.py --model moonshotai/kimi-k3.1-pro
uv run python scripts/experiment12/run.py --model google/gemini-4-argon
```

These commands can run concurrently. Each writes completed transcripts directly
to `results/`, replacing the previous output for that model and case. Select cases
with `--cases breakout circle`. Run offline tests with
`uv run python -m unittest discover -s tests`.
