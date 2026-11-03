"""Run the original weight-reading prompts and save readable transcripts."""

import argparse
import time
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.experiment12.config import CASES, EXPERIMENTS, MODELS, ROOT, UPSTREAM
from scripts.experiment12.providers import call, extract, make_request
from scripts.experiment12.transcripts import write_transcript


def run(model, cases, results):
    provider = MODELS[model]
    failed = 0
    for case in cases:
        experiment = EXPERIMENTS[CASES[case]]
        prompt = (UPSTREAM / experiment / "runs" / case / "prompt.txt").read_text()
        request = make_request(model, prompt)
        print(f"{model}: {case}", flush=True)
        start = time.monotonic()
        try:
            response = call(provider, request)
        except RuntimeError as error:
            print(f"  Failed: {error}", flush=True)
            failed += 1
            continue
        elapsed = time.monotonic() - start
        answer, complete = extract(provider, response)
        if not complete or not answer.strip():
            print(
                f"  Incomplete response ({response.get('status')}, "
                f"{response.get('incomplete_details') or response.get('error')}); previous result kept.",
                flush=True,
            )
            failed += 1
            continue
        path = write_transcript(
            provider, request, response, case, elapsed, root=results
        )
        print(f"  Saved {path}", flush=True)
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--cases", nargs="+", choices=CASES, default=list(CASES))
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    try:
        failed = run(args.model, args.cases, args.results)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    if failed:
        parser.exit(1, f"{failed} case(s) did not complete.\n")


if __name__ == "__main__":
    main()
