"""Build the plain LaTeX report from the retained human-readable transcripts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://github.com/yikerman/llm-rw-weight-extended-test/blob/master/"
models = ["gpt-6-astra", "claude-opus-5-5", "claude-fable-5-1", "kimi-k3.1-pro"]
cases = [
    ("pacman", "Pac-Man"),
    ("breakout", "Breakout"),
    ("pong", "Pong"),
    ("freeway", "Freeway"),
    ("circle", "Circle"),
    ("square", "Square"),
    ("triangle", "Triangle"),
]


def directory(case):
    experiment = 1 if case in ("pacman", "breakout", "pong", "freeway") else 2
    return f"results/experiment-{experiment}-{case}"


def link(path, label):
    assert (ROOT / path).exists(), path
    return r"\href{" + BASE + path + "}{" + label + "}"


lines = [
    r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[hidelinks]{hyperref}
\usepackage{longtable}
\pagestyle{plain}
\begin{document}
\noindent Replication of weight-reading experiments 1 and 2\\
November 2, 2026

\noindent This report and its interpretation were prepared by the OpenAI assistant
(Codex). They are not user-authored and do not imply the user's endorsement.
Model responses are linked separately and preserved unchanged.

\section*{What was reproduced}
Experiments 1 and 2 from
\href{https://rikiyat.github.io/blog/weight-space-programming/}{Sparks of Weight-Space Programming}
were repeated using the seven released prompts: four policy networks for game
identification and three diffusion networks for shape identification. The source
release was pinned at
\href{https://github.com/RikiyaT/lm_understand-logs/tree/4d09ba6d6a7e891dd8063974dfe81b3d78e3494f}{commit 4d09ba6d}.

The tested models were GPT-6 Astra, Claude Opus 5.5, Claude Fable 5.1,
and Kimi K3.1 Pro.
Their API identifiers and complete settings are preserved in the transcripts.
Astra and the Claude models used their official APIs; Kimi used OpenRouter's
Responses API with model ID \path{moonshotai/kimi-k3.1-pro}. Each request contained the original user prompt,
including all numerical weights, and the neutral system instruction
``Answer the user's request.'' Prompts were checked against the pinned upstream release. Each trial was a fresh request, with no tools, web access,
code execution, demonstrations, or feedback. Ground-truth labels and previous
answers were not included in the requests.

Astra and Kimi used high reasoning effort with detailed reasoning summaries requested. The Claude
models used adaptive thinking with high effort. These settings do not establish
equal inference compute. No temperature or generation seed was specified.

This is a replication of the released weight-reading tasks and category outcomes.
The underlying networks were not retrained. Experiments 3--8, training procedures,
and the authors' historical Codex CLI execution environment were not reproduced.

\section*{Results}
\begin{center}
\begin{tabular}{lrrr}
Model & Games & Shapes & Filled descriptions\\
\hline
GPT-6 Astra & 4/4 & 3/3 & 0/3\\
Claude Opus 5.5 & 4/4 & 3/3 & 2/3\\
Claude Fable 5.1 & 4/4 & 3/3 & 1/3\\
Kimi K3.1 Pro & 2/4 & 1/3 & 2/3\\
\end{tabular}
\end{center}

The primary results reproduce the reported category-identification success on
all seven released inputs for Astra and extend it to both Claude models.
Game labels treat Freeway and Frogger as equivalent. Shape scoring accepts the
published category aliases, including square/rectangle.

Kimi correctly identified Pong, Freeway/Frogger, and circle. It called Breakout
Frogger, Pac-Man Sokoban, square a circular blob, and triangle an uppercase A.
The Sokoban and uppercase-A answers fall outside the scorer's known categories;
the assistant adjudicated both as incorrect, without changing the answers or
expanding the accepted aliases. Those reviews were not blinded and are recorded
in the respective transcripts.

Fable's Pong answer was manually adjudicated as correct: it explicitly identifies
Pong-style, single-player Pong and describes the vertical paddle, but also calls
it ``Breakout-without-bricks'' as an analogy. The automatic scorer flags both
names. This assistant review was not blinded to the model or answer key; its
rationale is retained in that transcript's assistant-authored evaluation metadata. Apart from these reviews and the two Kimi judgments above, final category
results were scored automatically. Unicode hyphens were normalized for label
matching.

All three diffusion targets generate filled shapes. Astra describes all three
as outlines. Opus describes the square and triangle as filled, but the circle
as a ring. Fable describes the triangle as filled and the other two as outlines.
Kimi describes the circle and square targets as filled, but labels the square
as a circle; its triangle prediction is the letter A. Thus only its circle answer
combines the correct category with a correct filled description.
The last table column measures only the filled attribute, independently of category;
it is not a complete image-fidelity score. Dimensions, variability, drawings,
and individual numerical claims have not been independently scored.

\section*{Execution qualifications}
The initial pilot had an assistant-imposed output limit of 16,384 tokens.
Opus's Breakout response identified the correct game but was truncated during
its description. At the user's direction, the smaller limit was removed.
Kimi requests had no requested output cap. Subsequent OpenAI requests omitted \texttt{max\_output\_tokens}; Anthropic's
required \texttt{max\_tokens} was set to its documented maximum of 128,000.
The truncated Opus trial was rerun and completed with the correct answer,
using 18,161 output tokens including thinking. Earlier completed responses
were retained. Thus output limits were not uniform across trials, and this
was not a fully preregistered comparison. Only the latest completed response
for each case and model is retained in this repository.

The first Astra request was lost because the runner incorrectly treated an
\texttt{error: null} field as a failure. Its task outcome and exact usage are
unknown; it is excluded from scoring and cannot be supplied as a transcript.
Neither that failure nor an unsuccessful local network launch is treated as
evidence about model capability. Failed, test, and superseded runs have been
removed. There are 28 retained completed responses. No incorrect Kimi answer was rerun
to obtain a better result.

\section*{Prompts and full transcripts}
Each ``Prompt'' link contains the complete original user prompt, including all
weights. Each model link opens a human-readable transcript with the system
instruction, request settings, token usage, returned reasoning text, and complete
final answer. Opaque signatures, encrypted reasoning, and transport metadata are
omitted. Authentication headers are excluded. Reasoning that the provider did
not expose as text cannot be included. Links assume publication of this repository's master branch
at \href{https://github.com/yikerman/llm-rw-weight-extended-test}{the GitHub repository}.

\begin{longtable}{llllll}
Task & Input & Astra & Opus & Fable & Kimi\\
\hline
\endhead
"""
]
for truth, label in cases:
    cells = [label, link(directory(truth) + "/prompt.txt", "Prompt")]
    for model in models:
        cells.append(
            link(directory(truth) + "/" + model + "-transcript.md", "Transcript")
        )
    lines.append(" & ".join(cells) + r"\\" + "\n")
lines.append(r"\end{longtable}" + "\n\n")
lines.append(r"""
\section*{Assistant assessment}
Success on these seven published inputs is not exclusive to Astra: Opus and
Fable also identify all game and shape categories. This supports cross-model
replicability of these demonstrations, not broad weight-space understanding.
The repeated circle error illustrates the distinction between recognizing a
category and accurately describing the complete network's output.
Kimi's 3/7 category result shows that the same success does not extend uniformly
to every model tested here. Its correct filled-circle description also shows
that performance differences are not a simple ordering on every attribute.
Similar aggregate benchmark performance is not sufficient to predict success
on these particular weight-reading prompts. This small comparison cannot
attribute the difference to targeted training or reinforcement learning.

These results do not identify how any model acquired the ability. They cannot
establish or rule out task-specific training, reinforcement learning,
memorization, or transfer from broader reasoning and interpretability knowledge.
Only seven public checkpoints were tested, with one final completed response
per model and checkpoint. No fresh-network, description-only, or shuffled-weight
control was run. The study therefore provides limited evidence about
out-of-distribution generalization or the original training-history hypothesis.
\end{document}
""")
(ROOT / "report/replication.tex").write_text("".join(lines))
print("Wrote report/replication.tex; all linked files exist.")
