# Weight-reading replication: experiments 1–2

Compare GPT-6 Astra, Claude Opus 5.5, and Claude Fable 5.1 on the exact four
game-policy and three diffusion-model prompts released with
[Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/).

The runner uses official APIs only: OpenAI Responses (`gpt-6-astra`) and Anthropic
Messages (`claude-opus-5-5`, `claude-fable-5-1`). Python 3.14; no third-party runtime
dependencies. Independent plans can run concurrently.

## Setup

```sh
uv sync
git submodule update --init --recursive
cp .env.example .env  # New checkouts only; preserve an existing .env.
chmod 600 .env
```

Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in `.env`. Environment variables take
precedence. `.env`, `.env.*` (except the empty example), and local `runs/` are
ignored. Keys are sent only in HTTP headers and are excluded from request artifacts.

The upstream submodule is pinned at `4d09ba6d6a7e891dd8063974dfe81b3d78e3494f`.
`sources/manifest.json` records URLs and prompt SHA-256 hashes. The upstream scripts
are not executed.

## New campaigns

Preparation is offline. Each plan contains seven independent requests, shuffled
in a deterministic order, with one repetition per network by default. Existing
plans cannot be overwritten. Use new directory names for new campaigns.

```sh
uv run writing-weight-emergence prepare --provider openai --output runs/astra-new
uv run writing-weight-emergence prepare --provider anthropic --output runs/opus-new
uv run writing-weight-emergence prepare --provider anthropic --model claude-fable-5-1 --output runs/fable-new

# Paid calls; each command can run in its own terminal.
uv run writing-weight-emergence run runs/astra-new --budget 60
uv run writing-weight-emergence run runs/opus-new --budget 25
uv run writing-weight-emergence run runs/fable-new --budget 60
```

`--cases ID ...` restricts preparation to specified network IDs; `--repetitions 3`
creates three fresh calls per network. `--seed` controls order only, not API sampling.
Do not run the same plan directory concurrently. Different plans are independent.

```sh
uv run writing-weight-emergence score runs/astra-new
uv run python -m unittest discover -s tests -v
uv run python scripts/report_pilots.py
```

The report script combines this workspace's campaigns, retaining every attempt and
selecting the latest attempted response per model/case, irrespective of correctness.
It writes `runs/comparison/summary.json`, `results.csv`, and `all_attempts.csv`.

## Protocol

- Original prompt bytes are verified against the source manifest. No article,
  previous answer, filename, answer key, or scoring instructions are sent.
- Neutral system instruction: `Answer the user's request.`
- Fresh, stateless request per network; no tools, code execution, web, feedback,
  demonstrations, or prior conversation.
- OpenAI uses high reasoning effort and detailed reasoning summaries, matching the
  released effort/summary settings. Anthropic uses adaptive thinking and high effort.
  Identical effort labels do not establish equal inference compute.
- **No smaller experimental output cap:** OpenAI omits `max_output_tokens`;
  Anthropic requires `max_tokens`, set to its documented 128,000 maximum by default.
  Provider limits still apply. The initial pilot used 16,384 before the user removed
  that restriction; completed responses are retained and truncated ones rerun.
- No temperature or generation seed is imposed.
- Primary outcomes: game identity and shape category. Parse only the `Game` or
  `Images` section, including Markdown headings and Unicode-hyphen normalization.
  Fixed aliases are in `cli.py`; Freeway/Frogger are equivalent. Missing, ambiguous,
  and negated labels require review. This is our conservative implementation of the
  documented keyword scheme, not the authors' unreleased scoring script.
- Filled versus outline is recorded separately. All three original targets generate
  filled shapes. Automated fill extraction should be checked against the full answer
  and drawing. A correct category is not a complete behavioral description.
- Record all planned cases, failures, truncations, and reviews. Incomplete responses
  are never silently counted as successful complete trials. Category labels observed
  in partial answers remain visible separately in the comparison report.
- Preserve raw response JSON, exact requests, model IDs, token usage, and latency.
  No automatic retries: timeouts may still incur charges. Completed responses are
  skipped on resume. After inspection, `--continue-after-invalid` preserves an
  incomplete response and proceeds to unqueried cases. Reruns use separate plans.
- This replicates published inputs through official APIs, not the original Codex CLI
  wrapper or an immutable historical model snapshot. Provider aliases can change.
  These seven networks do not identify training history or establish broad transfer.

## Cost control

Preparation computes a conservative allocation: prompt UTF-8 bytes plus 1,024
input-token overhead per case, plus the maximum possible output. This is an offline
allowance, not a provider token count or billing cap. `--budget` rejects a plan whose
allocation exceeds that amount. Recheck prices before later campaigns.

Prices checked November 2, 2026, per million tokens:

| Model | Input | Output |
|---|---:|---:|
| Astra | $10 | $50 |
| Opus | $4 | $20 |
| Fable | $10 | $50 |

A full seven-case campaign reserves about $54.24 for Astra/Fable or $21.69 for Opus
at the provider output maximum. Actual usage is expected to be substantially lower;
the original Astra run's 594,243 input and 14,586 output tokens would cost about $6.67.
No discount is assumed in allocation. The report estimates actual retained-response
cost from usage, including reported cache reads; it is not an invoice. These prompts
remain below Astra's long-context pricing boundary under the input allowance.

## This workspace's pilot history

- Official endpoint smoke tests succeeded; stored in `runs/smoke/`, excluded from scores.
- `astra-official-pilot` stopped after one call due to a runner bug: treating an
  `error: null` field as an error. Its response was lost, usage unknown, and it may
  have been billed. The infrastructure failure is recorded; no task outcome is inferred.
- `astra-official-pilot-v2` uses the fixed transport. A separate failed local network
  launch is archived under `failed_launch/` before the successful launch.
- Initial `opus-pilot` Breakout named the correct game but truncated its description
  at 16,384 tokens. `opus-uncapped` reruns it at the provider maximum.
- `astra-uncapped`, `fable-uncapped`, and `fable-case-*` contain remaining cases under
  revised settings. Old unqueried cases have `held_without_request` markers to prevent
  duplicate dispatch; those markers are not API attempts or model failures.
- Fable's Unicode spelling `Pac‑Man` prompted a formatting-only scorer fix, covered
  by a regression test. Its original answer is retained unchanged.

References: [OpenAI model/pricing](https://developers.openai.com/api/docs/models/gpt-6-astra),
[Responses API](https://developers.openai.com/api/reference/typescript/resources/responses/methods/create),
[Anthropic models](https://docs.anthropic.com/en/docs/about-claude/models/overview),
[Messages API](https://platform.claude.com/docs/en/api/messages/create).

## Assistant-authored evaluation of the completed pilot

**Author: the OpenAI assistant (Codex). This interpretation is not user-authored
and does not imply the user's agreement or endorsement.** Model-generated answers
are retained separately, unchanged, in `results/pilot-2026-11-02/raw/`.

All three models identified the four game categories and three shape categories:

| Model | Games | Shapes | Filled-shape descriptions matching the targets |
|---|---:|---:|---:|
| GPT-6 Astra | 4/4 | 3/3 | 0/3 |
| Claude Opus 5.5 | 4/4 | 3/3 | 2/3: square and triangle |
| Claude Fable 5.1 | 4/4* | 3/3 | 1/3: triangle |

*Fable's Pong answer requires manual adjudication. It explicitly calls the game
Pong-style / single-player Pong and describes the side-mounted vertical paddle,
but also uses “Breakout-without-bricks” as an analogy. The automatic scorer flags
both names. I adjudicated this as Pong, without altering the raw answer or hiding
the automatic ambiguity. This review was not blinded to model identity or the
answer key; the rationale is in `manual_reviews.json`.*

The filled-shape column measures that one descriptive attribute only. It is not a
complete image-fidelity score: dimensions, locations, variability, and example
renderings have not been independently scored. All three models describe the
circle model as hollow, whereas the released target generates filled circles.
Astra describes all three shapes as hollow, reproducing the published error;
Opus describes square and triangle as solid, and Fable describes triangle as solid.

### What I infer

The pilot provides evidence that success on these seven published weight-reading
inputs is not exclusive to Astra. Both Anthropic models can identify the game and
shape categories under the same tool-free, one-response task framing. This weakens
the narrower conjecture that other frontier models would fail these demonstrations.
It does not establish whether any provider deliberately trained on weight reading,
nor whether RL, supervised examples, pretraining, or broader reasoning transfer
produced the ability.

The qualitative game explanations connect spatial weight structure to player
location, movement constraints, moving objects, and reward layout. Those are
plausible task signatures, consistent with the authors' descriptions. However,
this pilot does not independently validate every quoted weight, claimed circuit,
or causal interpretation. A correct category plus a plausible explanation is not
proof of full computational understanding. The repeated circle error is a concrete
example of that gap: recognizing geometry in weights does not guarantee correctly
predicting the image the complete diffusion process produces.

I would not rank the models' general interpretability capability from these results.
Primary category accuracy is saturated on seven networks; the descriptive differences
are interesting exploratory observations, not a statistically established advantage.
Likewise, Fable used substantially more output/reasoning tokens here, but this is not
a controlled compute-efficiency comparison.

### Limitations and execution history

- These are seven already-public checkpoints, not fresh independently trained test
  cases. No contamination, memorization, description-only, or shuffled-weight control
  was run. The model-facing prompts did not contain the article or previous answers.
- There is effectively one completed response per model/network. Opus Breakout has
  an earlier truncated response and a separate completed rerun; both name Breakout.
- The pilot began with an assistant-imposed 16,384-token limit. At the user's direction,
  this was removed: new OpenAI requests omit their output cap; new Anthropic requests
  use the required field at the provider maximum of 128,000. Earlier completed trials
  were retained; the one truncated trial was rerun. Therefore output limits were not
  uniform across all trials. The final Opus Breakout response used 18,161 output
  tokens, including 16,653 thinking tokens; the initial limit was materially restrictive.
- Initial Astra infrastructure errors are documented above. The first generated
  response was lost to a transport bug, so it cannot be audited or scored. No conclusion
  is drawn from that attempt. All 22 retained model responses are exported.
- Official APIs were used instead of the authors' Codex wrapper. Model IDs are aliases,
  and effort labels do not guarantee matched compute across providers.

Estimated token charges for retained responses, including the truncated Opus attempt,
are **$9.09 Astra, $4.79 Opus, $14.83 Fable; $28.71 total**. These exclude the lost
Astra response and tiny smoke tests and are not billing statements.

My recommended next experiment is a preregistered test on fresh checkpoints, including
function-preserving hidden-unit permutations, destructive weight-shuffle controls,
and description-only baselines. That would probe dependence on meaningful weight
structure more directly than further repetitions of these same public examples.

### Results and verification

- [Summary and all attempts](results/pilot-2026-11-02/summary.json)
- [Effective results CSV](results/pilot-2026-11-02/results.csv)
- [All attempts CSV](results/pilot-2026-11-02/all_attempts.csv)
- [Manual review](results/pilot-2026-11-02/manual_reviews.json)
- Raw responses, plans, failure/transition records, and artifact hashes are alongside
  those files. Exact prompts are recoverable from the pinned submodule and source hashes.

Nine local tests cover exact prompt preservation, answer-section scoring, original
answers, Unicode names, both response formats, budget checks, request tampering,
resume behavior, null API errors, and preservation of truncated attempts. Secrets
are excluded from the exported artifacts. The upstream release is pinned by the Git submodule pointer.

## Plain LaTeX report

[LaTeX source](report/replication.tex) and [compiled PDF](report/replication.pdf)
state what was reproduced and link to all seven complete prompts and 22 full API
transcripts under `github.com/yikerman/llm-rw-weight-extended-test`. The evaluation
is explicitly assistant-authored. Regenerate with `python scripts/build_report.py`;
compile twice with `pdflatex -output-directory=/tmp report/replication.tex`.
