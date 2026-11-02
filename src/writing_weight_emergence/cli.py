"""Frozen requests, append-only attempts, and conservative answer scoring."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / 'upstream/lm_understand-logs'
COMMIT = '4d09ba6d6a7e891dd8063974dfe81b3d78e3494f'
SYSTEM = "Answer the user's request.\n"
MODELS = {'openai': 'gpt-6-astra', 'anthropic': 'claude-opus-5-5'}
# USD per token, checked 2026-11-02. Recheck before later campaigns.
PRICES = {'gpt-6-astra': (10e-6, 50e-6), 'claude-opus-5-5': (4e-6, 20e-6), 'claude-fable-5-1': (10e-6, 50e-6)}
PROVIDERS = {'gpt-6-astra': 'openai', 'claude-opus-5-5': 'anthropic', 'claude-fable-5-1': 'anthropic'}
ALIASES = {
 'game': {'breakout': r'\bbreakout\b', 'pong': r'\bpong\b',
          'pacman': r'\bpac[ -]?man\b', 'freeway': r'\b(?:freeway|frogger)\b'},
 'shape': {'circle': r'\b(?:circles?|circular|discs?|disks?|round|ovals?)\b',
           'square': r'\b(?:squares?|rectangles?|rectangular|box|boxes)\b',
           'triangle': r'\b(?:triangles?|triangular|pyramids?|wedges?)\b'}}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('\"\''))


def section(text, name):
    # Handles both `**Images:** text` and a heading on its own line.
    plain = text.replace('**', '').replace('__', '')
    match = re.search(rf'(?im)^\s*(?:#+\s*)?{name}(?::[ \t]*|[ \t]*$)\s*', plain)
    if not match:
        return ''
    rest = plain[match.end():]
    return re.split(r'(?im)^\s*(?:#+\s*)?(?:Observations|Reasoning|Game|Description|Images|Example|Confidence)(?::|[ \t]*$)', rest)[0].strip()


def score(text, kind, truth):
    answer = section(text, 'Game' if kind == 'game' else 'Images')
    normalized = answer.translate(str.maketrans({c: '-' for c in '\u2010\u2011\u2012\u2013\u2014\u2212'}))
    matches = [label for label, pattern in ALIASES[kind].items()
               if re.search(pattern, normalized, re.I)]
    # Ambiguous/negated categories need human review, never silently choose the truth.
    negated = any(re.search(r'\b(?:not|rather than|instead of|either|unlikely)(?:\s+\w+){0,3}\s*$', normalized[:m.start()], re.I)
                  for pattern in ALIASES[kind].values() for m in re.finditer(pattern, normalized, re.I))
    review = len(matches) != 1 or negated
    confidence = section(text, 'Confidence')
    number = re.search(r'\b(\d{1,3})(?:\s*%)?', confidence)
    fill = None
    if kind == 'shape':
        outline = bool(re.search(r'\b(?:outline\w*|hollow|rings?|black interior)\b', answer, re.I))
        filled = bool(re.search(r'\b(?:filled|solid)\b', answer, re.I))
        fill = 'ambiguous' if outline and filled else 'outline' if outline else 'filled' if filled else 'unspecified'
    return {'answer_section': answer, 'candidates': matches,
            'prediction': matches[0] if not review else None,
            'correct': matches[0] == truth if not review else None,
            'needs_review': review, 'confidence': int(number[1]) if number and int(number[1]) <= 100 else None,
            'fill_description': fill}


def prepare(args):
    out = args.output
    model = getattr(args, 'model', None) or MODELS[args.provider]
    if PROVIDERS.get(model) != args.provider:
        raise ValueError('Model does not belong to the selected provider')
    if out.exists():
        raise ValueError('Output already exists; use a new directory to preserve the frozen plan.')
    manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
    if manifest['repository']['commit'] != COMMIT:
        raise ValueError('Unexpected source revision')
    source_hashes = {p['path']: p['sha256'] for p in manifest['pilot_prompts']}
    selected = set(getattr(args, 'cases', None) or [])
    cases = []
    for exp, kind in [('exp1_which_game', 'game'), ('exp2_diffusion', 'shape')]:
        scores = json.loads((UPSTREAM / exp / 'eval/scores.json').read_text())
        for row in scores:
            if selected and row['id'] not in selected:
                continue
            prompt_path = UPSTREAM / exp / 'runs' / row['true'] / 'prompt.txt'
            raw = prompt_path.read_bytes()
            if digest(raw) != source_hashes[str(prompt_path.relative_to(ROOT))]:
                raise ValueError(f'Prompt changed: {prompt_path}')
            for rep in range(args.repetitions):
                cases.append({'id': f'{row["id"]}-r{rep}', 'kind': kind, 'truth': row['true'],
                              'source': str(prompt_path.relative_to(ROOT)), 'prompt_sha256': digest(raw),
                              'reference_input_tokens': row['usage']['input_tokens'],
                              'prompt': raw.decode()})
    if selected - {c['id'].split('-r')[0] for c in cases}:
        raise ValueError('Unknown case ID')
    random.Random(args.seed).shuffle(cases)
    out.mkdir(parents=True)
    (out / 'requests').mkdir()
    total = 0
    for case in cases:
        prompt = case.pop('prompt')
        request = {'model': model, 'max_tokens': args.max_tokens,
                   'messages': [{'role': 'user', 'content': prompt}]}
        if args.provider == 'anthropic':
            request.update(system=SYSTEM, thinking={'type': 'adaptive'}, output_config={'effort': 'high'})
        else:
            request = {'model': MODELS['openai'], 'instructions': SYSTEM,
                       'input': request['messages'],
                       'reasoning': {'effort': 'high', 'summary': 'detailed'},
                       'tools': [], 'store': False, 'service_tier': 'default'}
        dest = out / 'requests' / (case['id'] + '.json')
        dump(dest, request)
        case['request_sha256'] = digest(dest.read_bytes())
        # UTF-8 bytes + overhead is intentionally conservative for these ASCII prompts.
        case['input_token_allowance'] = len(prompt.encode()) + 1024
        total += case['input_token_allowance']
    pin, pout = PRICES[model]
    output_allowance = 128000 if args.provider == 'openai' else args.max_tokens
    dump(out / 'plan.json', {'schema': 1, 'source_commit': COMMIT, 'provider': args.provider,
        'model': model, 'effort': 'high', 'max_tokens': output_allowance,
        'order_seed': args.seed, 'repetitions': args.repetitions,
        'price_date': '2026-11-02', 'usd_per_input_token': pin, 'usd_per_output_token': pout,
        'conservative_cost_usd': round(total * pin + len(cases) * output_allowance * pout, 4),
        'protocol': 'protocol-v1', 'cases': cases})
    print(f'Prepared {len(cases)} requests in {out}; no API calls.')
    print(f'Conservative allocation: ${total * pin + len(cases) * output_allowance * pout:.2f}')


def call(provider, payload):
    load_env()
    env = 'ANTHROPIC_API_KEY' if provider == 'anthropic' else 'OPENAI_API_KEY'
    key = os.environ.get(env)
    if not key:
        raise ValueError(f'Missing {env}; set it in .env or the environment')
    headers = {'Content-Type': 'application/json'}
    if provider == 'anthropic':
        url = 'https://api.anthropic.com/v1/messages'
        headers.update({'x-api-key': key, 'anthropic-version': '2026-10-21'})
    else:
        url = 'https://api.openai.com/v1/responses'
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(url, json.dumps(payload).encode(), headers)
    # No automatic retries: a timeout may still have incurred a charge.
    try:
        with urllib.request.urlopen(req, timeout=900) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'API HTTP {exc.code}; request not automatically retried') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Network failure/timeout; request may have been billed; no automatic retry') from None
    return data


def extract(provider, response):
    if provider == 'anthropic':
        text = '\n'.join(b['text'] for b in response.get('content', []) if b.get('type') == 'text')
        valid = response.get('stop_reason') == 'end_turn' and all(b.get('type') in ('text', 'thinking', 'redacted_thinking') for b in response.get('content', []))
        return text, valid
    output = response.get('output', [])
    text = '\n'.join(c['text'] for item in output if item.get('type') == 'message'
                     for c in item.get('content', []) if c.get('type') == 'output_text')
    valid = response.get('status') == 'completed' and all(item.get('type') in ('message', 'reasoning') for item in output)
    return text, valid



def run(args):
    out = args.directory
    plan = json.loads((out / 'plan.json').read_text())
    if PROVIDERS.get(plan['model']) != plan['provider']:
        raise ValueError('Obsolete provider/model plan; prepare a new plan.')
    # Reserve the full frozen sweep even on resume, including possibly billed failed calls.
    if plan['conservative_cost_usd'] > args.budget:
        raise ValueError(f'Plan allocation ${plan["conservative_cost_usd"]:.2f} exceeds --budget {args.budget}')
    requests = []
    for case in plan['cases']:
        raw = (out / 'requests' / (case['id'] + '.json')).read_bytes()
        if digest(raw) != case['request_sha256']:
            raise ValueError('Request differs from frozen plan')
        requests.append(json.loads(raw))
    (out / 'responses').mkdir(exist_ok=True)
    for case, payload in zip(plan['cases'], requests):
        dest = out / 'responses' / (case['id'] + '.json')
        marker = dest.with_suffix('.started.json')
        if dest.exists():
            previous = json.loads(dest.read_text())['response']
            text, valid = extract(plan['provider'], previous)
            if not valid or not text.strip():
                if not getattr(args, 'continue_after_invalid', False):
                    raise ValueError('Existing incomplete response; inspect it, then use --continue-after-invalid to retain it and query remaining cases.')
                dump(dest.with_suffix('.reviewed.json'), {'action': 'retained_incomplete_without_retry', 'reviewed_unix': time.time()})
            continue
        if marker.exists():
            if json.loads(marker.read_text()).get('held_without_request'):
                print('Case held for revised settings; stopping without a request.')
                break
            raise ValueError(f'Unfinished attempt {case["id"]}; inspect it before any manual retry. Use a new plan for reruns.')
        dump(marker, {'started_unix': time.time(), 'request_sha256': case['request_sha256']})
        print(f'Querying {case["id"]}...', flush=True)
        start = time.monotonic()
        try:
            response = call(plan['provider'], payload)
            dump(dest, {'response': response, 'elapsed_seconds': time.monotonic() - start})
        except Exception as exc:
            dump(dest.with_suffix('.error.json'), {'type': type(exc).__name__, 'message': str(exc)})
            raise
        text, valid = extract(plan['provider'], response)
        if not valid or not text.strip():
            print('Non-complete response retained; stopping sweep for review.')
            break
    summarize(out)


def summarize(out):
    plan = json.loads((out / 'plan.json').read_text())
    rows = []
    for case in plan['cases']:
        path = out / 'responses' / (case['id'] + '.json')
        row = {'id': case['id'], 'kind': case['kind'], 'truth': case['truth'], 'status': 'missing'}
        if path.exists():
            response = json.loads(path.read_text())['response']
            text, valid = extract(plan['provider'], response)
            row.update(score(text, case['kind'], case['truth']))
            row.update(status='complete' if valid and text.strip() else 'invalid', usage=response.get('usage'),
                       returned_model=response.get('model'), provider=response.get('provider'))
            if row['status'] != 'complete':
                row.update(correct=None, needs_review=True)
        rows.append(row)
    result = {'rows': rows, 'total_planned': len(rows),
              'complete': sum(r['status'] == 'complete' for r in rows),
              'auto_correct': sum(r.get('correct') is True for r in rows),
              'needs_review': sum(r.get('needs_review', False) for r in rows)}
    dump(out / 'scores.json', result)
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Freeze exact requests offline')
    p.add_argument('--provider', choices=MODELS, required=True)
    p.add_argument('--model', choices=PROVIDERS, help='Defaults to Astra for OpenAI, Opus for Anthropic')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--repetitions', type=int, default=1)
    p.add_argument('--max-tokens', type=int, default=128000, help='Anthropic required field; default is provider maximum. OpenAI omits its output cap.')
    p.add_argument('--cases', nargs='+', help='Optional network IDs for follow-up runs')
    p.add_argument('--seed', type=int, default=20261102)
    p = commands.add_parser('run', help='Execute a frozen plan (paid API calls)')
    p.add_argument('directory', type=Path)
    p.add_argument('--budget', type=float, default=20)
    p.add_argument('--continue-after-invalid', action='store_true', help='After inspection, retain existing incomplete trials and continue with unqueried cases')
    p = commands.add_parser('score', help='Score saved responses offline')
    p.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            if args.repetitions < 1 or not 1024 <= args.max_tokens <= 128000:
                raise ValueError('Use positive repetitions and 1024–128000 max tokens')
            prepare(args)
        elif args.command == 'run':
            run(args)
        else:
            summarize(args.directory)
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, str(exc) + '\n')
