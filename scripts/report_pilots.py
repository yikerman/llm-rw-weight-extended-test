"""Aggregate all retained attempts, selecting the latest attempt per model/case."""
import csv
import json
from pathlib import Path
from writing_weight_emergence.cli import ROOT, PRICES, extract, score

review_path = ROOT / 'runs/comparison/manual_reviews.json'
reviews = json.loads(review_path.read_text()) if review_path.exists() else {}
rows = []
for directory in sorted((ROOT / 'runs').iterdir()):
    if not (directory / 'plan.json').exists():
        continue
    plan = json.loads((directory / 'plan.json').read_text())
    if plan['model'] not in PRICES:
        continue
    for case in plan['cases']:
        path = directory / 'responses' / (case['id'] + '.json')
        marker = path.with_suffix('.started.json')
        if not marker.exists():
            continue
        started = json.loads(marker.read_text())
        if started.get('held_without_request'):
            continue
        row = {'run': directory.name, 'model': plan['model'], 'id': case['id'], 'kind': case['kind'],
               'truth': case['truth'], 'status': 'pending', 'observed_prediction': None,
               'observed_label_correct': None, 'protocol_correct': None, 'fill': None,
               'input_tokens': 0, 'output_tokens': 0, 'reasoning_tokens': 0,
               'cost_usd': 0, 'elapsed_seconds': 0, 'answer_section': '',
               'started_unix': started.get('started_unix', 0), 'scoring_method': 'automatic', 'review_rationale': ''}
        request = json.loads((directory / 'requests' / (case['id']+'.json')).read_text())
        row['output_cap'] = request.get('max_output_tokens', request.get('max_tokens'))
        if path.with_suffix('.error.json').exists():
            row['status'] = 'infrastructure_failure'
        if path.exists():
            saved = json.loads(path.read_text()); response = saved['response']
            text, valid = extract(plan['provider'], response)
            scored = score(text, case['kind'], case['truth'])
            row.update(status='complete' if valid and text.strip() else 'incomplete',
                       observed_prediction=scored['prediction'], observed_label_correct=scored['correct'],
                       protocol_correct=scored['correct'] if valid and text.strip() else None,
                       fill=scored['fill_description'], answer_section=scored['answer_section'],
                       elapsed_seconds=saved['elapsed_seconds'])
            usage = response.get('usage') or {}
            inp, out = usage.get('input_tokens', 0), usage.get('output_tokens', 0)
            pi, po = PRICES[plan['model']]
            if plan['provider'] == 'openai':
                detail = usage.get('input_tokens_details', {})
                cached, written = detail.get('cached_tokens', 0), detail.get('cache_write_tokens', 0)
                cost = max(0, inp-cached-written)*pi + cached*pi*0.1 + written*pi*1.25 + out*po
                thinking = usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)
            else:
                cost = inp*pi + usage.get('cache_read_input_tokens', 0)*pi*0.1 + usage.get('cache_creation_input_tokens', 0)*pi*1.25 + out*po
                thinking = usage.get('output_tokens_details', {}).get('thinking_tokens', 0)
            row.update(input_tokens=inp, output_tokens=out, reasoning_tokens=thinking, cost_usd=cost)
        review = reviews.get(plan['model']+'/'+case['id'])
        if review and row['status'] == 'complete':
            row.update(protocol_correct=review['correct'], scoring_method='manual_unblinded', review_rationale=review['rationale'])
        rows.append(row)
latest = {}
for row in sorted(rows, key=lambda r: r['started_unix']):
    latest[row['model'], row['id']] = row
summary = []
for model in PRICES:
    arm = [r for r in latest.values() if r['model'] == model]
    all_attempts = [r for r in rows if r['model'] == model]
    summary.append({'model': model, 'unique_cases': len(arm),
                    'completed': sum(r['status']=='complete' for r in arm),
                    'incomplete': sum(r['status']=='incomplete' for r in arm),
                    'observed_correct_labels': sum(r['observed_label_correct'] is True for r in arm),
                    'protocol_correct': sum(r['protocol_correct'] is True for r in arm),
                    'games_correct': sum(r['kind']=='game' and r['protocol_correct'] is True for r in arm),
                    'shapes_correct': sum(r['kind']=='shape' and r['protocol_correct'] is True for r in arm),
                    'recorded_cost_usd_all_attempts': round(sum(r['cost_usd'] for r in all_attempts), 6),
                    'recorded_input_tokens_all_attempts': sum(r['input_tokens'] for r in all_attempts),
                    'recorded_output_tokens_all_attempts': sum(r['output_tokens'] for r in all_attempts)})
output = ROOT / 'runs/comparison'; output.mkdir(exist_ok=True)
(output / 'summary.json').write_text(json.dumps({'evaluation_author': 'OpenAI assistant (Codex); not authored or endorsed by the user', 'arms': summary,
    'cost_caveat': 'Token-price estimate for retained responses only. Excludes smoke tests, local network launch failure and original lost Astra response; not an invoice.',
    'selection_rule': 'Latest attempted response per model/case, irrespective of correctness. All earlier attempts retained.',
    'effective_results': list(latest.values()), 'all_attempts': rows}, indent=2)+'\n')
for filename, data in [('results.csv', list(latest.values())), ('all_attempts.csv', rows)]:
    with (output / filename).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(data)
print(json.dumps(summary, indent=2))
