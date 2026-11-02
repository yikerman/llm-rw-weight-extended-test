"""Export full API transcripts and build the plain LaTeX replication report."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'results/pilot-2026-11-02'
BASE = 'https://github.com/yikerman/llm-rw-weight-extended-test/blob/master/'
summary = json.loads((RESULT / 'summary.json').read_text())
effective = {(r['model'], r['truth']): r for r in summary['effective_results']}
models = ['gpt-6-astra', 'claude-opus-5-5', 'claude-fable-5-1']
names = ['Astra', 'Opus 5.5', 'Fable 5.1']
cases = [('pacman', 'Pac-Man'), ('breakout', 'Breakout'), ('pong', 'Pong'),
         ('freeway', 'Freeway'), ('circle', 'Circle'), ('square', 'Square'), ('triangle', 'Triangle')]
transcript_paths = {}
prompt_paths = {}

for row in summary['all_attempts']:
    run, case_id = row['run'], row['id']
    raw = RESULT / 'raw' / run / (case_id + '.json')
    if not raw.exists():
        continue  # Lost infrastructure attempt is disclosed, not reconstructed.
    request_file = ROOT / 'runs' / run / 'requests' / (case_id + '.json')
    if request_file.exists():
        request_bytes = request_file.read_bytes()
        request = json.loads(request_bytes)
    else:
        # Rebuild from the exported transcript on a fresh clone (runs/ is ignored).
        archived = RESULT / 'transcripts' / run / (case_id + '.json')
        request = json.loads(archived.read_text())['request']
        request_bytes = (json.dumps(request, indent=2) + '\n').encode()
    plan = json.loads((RESULT / 'plans' / run / 'plan.json').read_text())
    case = next(c for c in plan['cases'] if c['id'] == case_id)
    assert hashlib.sha256(request_bytes).hexdigest() == case['request_sha256']
    messages = request.get('input', request.get('messages'))
    assert len(messages) == 1
    prompt = messages[0]['content']
    assert hashlib.sha256(prompt.encode()).hexdigest() == case['prompt_sha256']
    prompt_file = RESULT / 'prompts' / (case_id.split('-r')[0] + '.txt')
    prompt_file.parent.mkdir(exist_ok=True)
    prompt_file.write_bytes(prompt.encode())
    prompt_paths[row['truth']] = str(prompt_file.relative_to(ROOT))
    saved = json.loads(raw.read_text())
    transcript = {
        'description': 'Full experiment API request and full returned JSON response. Authentication headers omitted. No supplied response fields or text omitted.',
        'provider': plan['provider'], 'model': plan['model'],
        'endpoint': 'https://api.openai.com/v1/responses' if plan['provider']=='openai' else 'https://api.anthropic.com/v1/messages',
        'api_version': '2026-10-21' if plan['provider']=='anthropic' else None,
        'source_commit': plan['source_commit'], 'prompt_sha256': case['prompt_sha256'],
        'request_sha256': case['request_sha256'], 'request': request,
        'response': saved['response'], 'elapsed_seconds': saved['elapsed_seconds'],
    }
    dest = RESULT / 'transcripts' / run / (case_id + '.json')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + '\n')
    transcript_paths[run, case_id] = str(dest.relative_to(ROOT))


def link(path, label):
    base = BASE.replace('/blob/', '/tree/') if path.endswith('/plans') else BASE
    return r'\href{' + base + path + '}{' + label + '}'


lines = [r'''\documentclass[11pt]{article}
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

The tested models were GPT-6 Astra, Claude Opus 5.5, and Claude Fable 5.1.
Their API identifiers and complete settings are preserved in the transcripts.
They were accessed through the official OpenAI Responses and Anthropic Messages APIs. Each request contained the original user prompt,
including all numerical weights, and the neutral system instruction
``Answer the user's request.'' Prompt hashes were checked against the archived
source manifest. Each trial was a fresh request, with no tools, web access,
code execution, demonstrations, or feedback. Ground-truth labels and previous
answers were not included in the requests.

Astra used high reasoning effort with detailed reasoning summaries. The Claude
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
\end{tabular}
\end{center}

The primary results reproduce the reported category-identification success on
all seven released inputs for Astra and extend it to both Claude models.
Game labels treat Freeway and Frogger as equivalent. Shape scoring accepts the
published category aliases, including square/rectangle.

Fable's Pong answer was manually adjudicated as correct: it explicitly identifies
Pong-style, single-player Pong and describes the vertical paddle, but also calls
it ``Breakout-without-bricks'' as an analogy. The automatic scorer flags both
names. This assistant review was not blinded to the model or answer key; its
rationale is retained in the linked scoring records. All other final category
results were scored automatically. Unicode hyphens were normalized for label
matching.

All three diffusion targets generate filled shapes. Astra describes all three
as outlines. Opus describes the square and triangle as filled, but the circle
as a ring. Fable describes the triangle as filled and the other two as outlines.
The last table column measures only this attribute of the written description;
it is not a complete image-fidelity score. Dimensions, variability, drawings,
and individual numerical claims have not been independently scored.

\section*{Execution qualifications}
The initial pilot had an assistant-imposed output limit of 16,384 tokens.
Opus's Breakout response identified the correct game but was truncated during
its description. At the user's direction, the smaller limit was removed.
Subsequent OpenAI requests omitted \texttt{max\_output\_tokens}; Anthropic's
required \texttt{max\_tokens} was set to its documented maximum of 128,000.
The truncated Opus trial was rerun and completed with the correct answer,
using 18,161 output tokens including thinking. Earlier completed responses
were retained. Thus output limits were not uniform across trials, and this
was not a fully preregistered comparison. Both Opus attempts are preserved.

The first Astra request was lost because the runner incorrectly treated an
\texttt{error: null} field as a failure. Its task outcome and exact usage are
unknown; it is excluded from scoring and cannot be supplied as a transcript.
A separate failed local network launch is also documented. Neither is treated
as evidence about model capability. There are 21 final completed trials and
22 retained full responses, including the truncated Opus attempt.

Token-price estimates for retained responses are \$9.09 for Astra, \$4.79 for
Opus, and \$14.83 for Fable (\$28.71 total). These include the retained truncated
attempt but exclude the lost Astra response and small endpoint smoke tests;
they are not billing statements.

\section*{Prompts and full transcripts}
Each ``Prompt'' link contains the complete original user prompt, including all
weights. Each model link contains the entire API request (including the system
instruction and settings) and the entire returned response JSON. No returned
text is removed; available reasoning fields, stop reasons, and usage are included.
Authentication headers are excluded. Reasoning that the provider did not return
cannot be included. Links assume publication of this repository's master branch
at \href{https://github.com/yikerman/llm-rw-weight-extended-test}{the GitHub repository}.

\begin{longtable}{lllll}
Task & Input & Astra & Opus 5.5 & Fable 5.1\\
\hline
\endhead
''']
for truth, label in cases:
    cells = [label, link(prompt_paths[truth], 'Prompt')]
    for model in models:
        row = effective[model, truth]
        cells.append(link(transcript_paths[row['run'], row['id']], 'Transcript'))
    lines.append(' & '.join(cells) + r'\\' + '\n')
lines.append(r'\end{longtable}' + '\n\n')
lines.append('Earlier truncated Opus Breakout response: ' + link(transcript_paths['opus-pilot', 'a9f535cc-r0'], 'full transcript') + '.\n\n')
lines.append('Scoring and provenance: ' + ', '.join([
    link('results/pilot-2026-11-02/results.csv', 'final per-case scores'),
    link('results/pilot-2026-11-02/all_attempts.csv', 'all recorded attempts'),
    link('results/pilot-2026-11-02/manual_reviews.json', 'manual adjudication'),
    link('results/pilot-2026-11-02/plans', 'plans and incident records'),
    link('src/writing_weight_emergence/cli.py', 'runner and scorer')]) + '.\n')
lines.append(r'''
\section*{Assistant assessment}
Success on these seven published inputs is not exclusive to Astra: Opus and
Fable also identify all game and shape categories. This supports cross-model
replicability of these demonstrations, not broad weight-space understanding.
The repeated circle error illustrates the distinction between recognizing a
category and accurately describing the complete network's output.

These results do not identify how any model acquired the ability. They cannot
establish or rule out task-specific training, reinforcement learning,
memorization, or transfer from broader reasoning and interpretability knowledge.
Only seven public checkpoints were tested, with one final completed response
per model and checkpoint. No fresh-network, description-only, or shuffled-weight
control was run. The study therefore provides limited evidence about
out-of-distribution generalization or the original training-history hypothesis.
\end{document}
''')
(ROOT / 'report/replication.tex').write_text(''.join(lines))
# Refresh artifact checksums to include newly exported prompt/transcript files.
manifest = {str(p.relative_to(RESULT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in RESULT.rglob('*') if p.is_file() and p.name != 'artifacts.sha256.json'}
(RESULT / 'artifacts.sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(f'Exported {len(prompt_paths)} prompts and {len(transcript_paths)} full transcripts.')
print('Wrote report/replication.tex')
