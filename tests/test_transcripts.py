import tempfile
import unittest
from pathlib import Path

from writing_weight_emergence import cli
from writing_weight_emergence.transcripts import read_transcript, write_transcript


class TranscriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = cli.ROOT / "runs/test-transcripts"
        cls.scratch.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.scratch.rmdir()

    def test_latest_completed_response_and_reasoning(self):
        request = {
            "model": "claude-opus-5-5",
            "system": "neutral",
            "messages": [{"role": "user", "content": "weights"}],
            "max_tokens": 128000,
        }
        response = {
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 1, "output_tokens": 2},
            "content": [
                {
                    "type": "thinking",
                    "thinking": "reasoning text",
                    "signature": "opaque",
                },
                {"type": "text", "text": "Game: Pong"},
            ],
        }
        with tempfile.TemporaryDirectory(dir=self.scratch) as tmp:
            root = Path(tmp)
            path = write_transcript(
                "anthropic", request, response, "pong", 1, root=root
            )
            self.assertEqual(path.parent.name, "experiment-1-pong")
            self.assertEqual(path.name, "claude-opus-5-5-transcript.md")
            self.assertIn("reasoning text", path.read_text())
            self.assertNotIn("opaque", path.read_text())
            self.assertEqual(read_transcript(path)[1], "Game: Pong")
            original = path.read_bytes()
            response["stop_reason"] = "max_tokens"
            with self.assertRaises(ValueError):
                write_transcript("anthropic", request, response, "pong", 2, root=root)
            self.assertEqual(path.read_bytes(), original)
            response["stop_reason"] = "end_turn"
            # A completed wrong answer is still legitimate experimental evidence.
            response["content"][-1]["text"] = "Game: Breakout"
            write_transcript("anthropic", request, response, "pong", 3, root=root)
            self.assertFalse(read_transcript(path)[0]["evaluation"]["correct"])
            self.assertEqual(len(list(path.parent.iterdir())), 2)
            request["messages"][0]["content"] = "different weights"
            with self.assertRaises(ValueError):
                write_transcript("anthropic", request, response, "pong", 3, root=root)

    def test_retained_results_layout(self):
        folders = sorted((cli.ROOT / "results").iterdir())
        self.assertEqual(len(folders), 7)
        for folder in folders:
            self.assertRegex(folder.name, r"^experiment-[12]-[a-z]+$")
            self.assertEqual(
                {p.name for p in folder.iterdir()},
                {
                    "prompt.txt",
                    "gpt-6-astra-transcript.md",
                    "claude-opus-5-5-transcript.md",
                    "claude-fable-5-1-transcript.md",
                },
            )
            for path in folder.glob("*-transcript.md"):
                meta, answer = read_transcript(path)
                self.assertEqual(meta["status"], "complete")
                self.assertTrue(answer.strip())


if __name__ == "__main__":
    unittest.main()
