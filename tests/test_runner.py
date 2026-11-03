import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from writing_weight_emergence import cli, providers
from writing_weight_emergence.config import CASES, EXPERIMENTS, MODELS, ROOT, UPSTREAM
from writing_weight_emergence.scoring import score
from writing_weight_emergence.transcripts import read_transcript


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = ROOT / "runs/test-work"
        cls.scratch.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.rmdir()

    def test_run_original_prompts_directly_to_transcripts(self):
        for model, provider in MODELS.items():
            with (
                self.subTest(model=model),
                tempfile.TemporaryDirectory(dir=self.scratch) as tmp,
            ):
                selected = list(CASES)
                responses = []
                for case in selected:
                    answer = (
                        UPSTREAM
                        / EXPERIMENTS[CASES[case]]
                        / "runs"
                        / case
                        / "answer.md"
                    ).read_text()
                    if provider == "anthropic":
                        response = {
                            "stop_reason": "end_turn",
                            "content": [{"type": "text", "text": answer}],
                        }
                    else:
                        response = {
                            "status": "completed",
                            "error": None,
                            "output": [
                                {
                                    "type": "message",
                                    "content": [
                                        {"type": "output_text", "text": answer}
                                    ],
                                }
                            ],
                        }
                    responses.append(response)
                with (
                    patch.object(cli, "call", side_effect=responses) as call,
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(cli.run(model, selected, Path(tmp)), 0)
                self.assertEqual(call.call_count, 7)
                for case, invocation in zip(selected, call.call_args_list):
                    payload = invocation.args[1]
                    messages = payload.get("input", payload.get("messages"))
                    source = (
                        UPSTREAM
                        / EXPERIMENTS[CASES[case]]
                        / "runs"
                        / case
                        / "prompt.txt"
                    )
                    self.assertEqual(
                        messages, [{"role": "user", "content": source.read_text()}]
                    )
                    self.assertNotIn("truth", payload)
                    if provider in ("openai", "openrouter"):
                        self.assertNotIn("max_output_tokens", payload)
                    path = (
                        Path(tmp)
                        / f"experiment-{CASES[case]}-{case}"
                        / f"{model.split('/')[-1]}-transcript.md"
                    )
                    metadata, _ = read_transcript(path)
                    self.assertTrue(metadata["evaluation"]["correct"])

    def test_failure_keeps_previous_result_and_continues(self):
        response = {
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": "Game: Pong"}],
        }
        with tempfile.TemporaryDirectory(dir=self.scratch) as tmp:
            output = Path(tmp)
            with (
                patch.object(cli, "call", return_value=response),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                cli.run("claude-opus-5-5", ["pong"], output)
            path = output / "experiment-1-pong/claude-opus-5-5-transcript.md"
            original = path.read_bytes()
            failed = {
                "stop_reason": "max_tokens",
                "content": [{"type": "text", "text": "partial"}],
            }
            with (
                patch.object(
                    cli, "call", side_effect=[RuntimeError("HTTP 429"), failed]
                ) as call,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(
                    cli.run("claude-opus-5-5", ["pong", "circle"], output), 2
                )
                self.assertEqual(call.call_count, 2)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse((output / "experiment-2-circle").exists())

    def test_scoring_uses_answer_section(self):
        result = score(
            "Reasoning: Breakout is unlikely.\nGame: Pong\nConfidence: 90%",
            "game",
            "pong",
        )
        self.assertTrue(result["correct"])
        self.assertTrue(score("Game: Pac‑Man", "game", "pacman")["correct"])
        for answer in ["Game: Pong or Breakout", "Reasoning: Pong", "Game: Not Pong"]:
            self.assertTrue(score(answer, "game", "pong")["needs_review"])

    def test_openrouter_transport(self):
        with (
            patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-only"}),
            patch.object(providers.urllib.request, "urlopen") as transport,
        ):
            transport.return_value.__enter__.return_value = io.StringIO(
                '{"status":"completed","output":[]}'
            )
            providers.call(
                "openrouter",
                providers.make_request("moonshotai/kimi-k3.1-pro", "prompt"),
            )
            request = transport.call_args.args[0]
            self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/responses")
            self.assertEqual(request.get_header("Authorization"), "Bearer test-only")

    def test_openai_null_error_response_is_preserved(self):
        response = {"error": None, "status": "completed", "output": []}
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-only"}),
            patch.object(providers.urllib.request, "urlopen") as transport,
        ):
            transport.return_value.__enter__.return_value = io.StringIO(
                json.dumps(response)
            )
            self.assertEqual(
                providers.call("openai", {"model": "gpt-6-astra"}), response
            )


if __name__ == "__main__":
    unittest.main()
