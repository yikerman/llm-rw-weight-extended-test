import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from writing_weight_emergence import cli


class RunnerTests(unittest.TestCase):
    def prepare(self, directory, provider='anthropic'):
        args = argparse.Namespace(output=directory, provider=provider, repetitions=1, max_tokens=16384, seed=42)
        with contextlib.redirect_stdout(io.StringIO()):
            cli.prepare(args)
        return json.loads((directory / 'plan.json').read_text())

    def test_original_answers(self):
        for exp, kind in [('exp1_which_game', 'game'), ('exp2_diffusion', 'shape')]:
            for row in json.loads((cli.UPSTREAM / exp / 'eval/scores.json').read_text()):
                text = (cli.UPSTREAM / exp / 'runs' / row['true'] / 'answer.md').read_text()
                scored = cli.score(text, kind, row['true'])
                self.assertTrue(scored['correct'], scored)
                if kind == 'shape':
                    self.assertEqual(scored['fill_description'], 'outline')

    def test_only_answer_section_scored(self):
        result = cli.score('Reasoning: Breakout is unlikely.\nGame: Pong\nConfidence: 90%', 'game', 'pong')
        self.assertTrue(result['correct'])
        self.assertTrue(cli.score('Game: Pac‑Man', 'game', 'pacman')['correct'])
        self.assertEqual(result['confidence'], 90)
        self.assertTrue(cli.score('Game: Pong or Breakout', 'game', 'pong')['needs_review'])
        self.assertTrue(cli.score('Reasoning: Pong', 'game', 'pong')['needs_review'])
        self.assertTrue(cli.score('Game: Not Pong', 'game', 'pong')['needs_review'])

    def test_frozen_requests_both_providers(self):
        with tempfile.TemporaryDirectory() as tmp:
            for provider in cli.MODELS:
                folder = Path(tmp) / provider
                plan = self.prepare(folder, provider)
                self.assertEqual(len(plan['cases']), 7)
                for case in plan['cases']:
                    payload = json.loads((folder / 'requests' / (case['id'] + '.json')).read_text())
                    messages = payload.get('messages', payload.get('input'))
                    self.assertEqual(len(messages), 1)
                    self.assertEqual(messages[0]['content'], (cli.ROOT / case['source']).read_text())
                    self.assertNotIn('truth', payload)
                    self.assertNotIn('api_key', payload)
                    self.assertFalse(payload.get('tools'))
                    if provider == 'openai':
                        self.assertNotIn('max_output_tokens', payload)
                        self.assertEqual(plan['max_tokens'], 128000)

    def test_run_resume_and_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'run'
            plan = self.prepare(folder)
            responses = [{'content': [{'type': 'text', 'text': ('Game: ' if c['kind'] == 'game' else 'Images: ') + c['truth']}], 'stop_reason': 'end_turn'} for c in plan['cases']]
            args = argparse.Namespace(directory=folder, budget=20)
            with patch.object(cli, 'call', side_effect=responses) as call, contextlib.redirect_stdout(io.StringIO()):
                cli.run(args)
                cli.run(args)
                self.assertEqual(call.call_count, 7)
            scores = json.loads((folder / 'scores.json').read_text())
            self.assertEqual(scores['auto_correct'], 7)
            with patch.object(cli, 'call') as call:
                args.budget = 0
                with self.assertRaises(ValueError): cli.run(args)
                call.assert_not_called()

    def test_failure_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'run'
            self.prepare(folder)
            args = argparse.Namespace(directory=folder, budget=20)
            with patch.object(cli, 'call', side_effect=RuntimeError('HTTP 429')) as call, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError): cli.run(args)
                with self.assertRaises(ValueError): cli.run(args)
                self.assertEqual(call.call_count, 1)

    def test_tampering_blocked_before_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'run'
            self.prepare(folder)
            next((folder / 'requests').glob('*.json')).write_text('{}')
            with patch.object(cli, 'call') as call:
                with self.assertRaises(ValueError): cli.run(argparse.Namespace(directory=folder, budget=20))
                call.assert_not_called()

    def test_truncation_not_scored_as_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'run'
            plan = self.prepare(folder)
            c = plan['cases'][0]
            answer = ('Game: ' if c['kind'] == 'game' else 'Images: ') + c['truth']
            response = {'stop_reason': 'max_tokens', 'content': [{'type': 'text', 'text': answer}]}
            with patch.object(cli, 'call', return_value=response) as call, contextlib.redirect_stdout(io.StringIO()):
                cli.run(argparse.Namespace(directory=folder, budget=20))
                self.assertEqual(call.call_count, 1)
            result = json.loads((folder / 'scores.json').read_text())
            self.assertEqual(result['auto_correct'], 0)
            self.assertEqual(result['needs_review'], 1)
            with patch.object(cli, 'call', return_value=response) as call, contextlib.redirect_stdout(io.StringIO()):
                cli.run(argparse.Namespace(directory=folder, budget=20, continue_after_invalid=True))
                self.assertEqual(call.call_count, 1)  # Only the next case; no retry of the first.
                self.assertTrue((folder / 'responses' / (c['id'] + '.reviewed.json')).exists())

    def test_null_error_is_success(self):
        response = {'error': None, 'status': 'completed', 'output': []}
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-only'}), patch.object(cli.urllib.request, 'urlopen') as transport:
            transport.return_value.__enter__.return_value = io.StringIO(json.dumps(response))
            self.assertEqual(cli.call('openai', {'model': 'gpt-6-astra'}), response)

    def test_openai_response(self):
        response = {'error': None, 'status': 'completed', 'output': [{'type': 'reasoning'}, {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Game: Pong'}]}]}
        self.assertEqual(cli.extract('openai', response), ('Game: Pong', True))
        response['status'] = 'incomplete'
        self.assertFalse(cli.extract('openai', response)[1])


if __name__ == '__main__':
    unittest.main()
