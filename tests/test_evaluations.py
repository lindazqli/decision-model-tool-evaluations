import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import model_helpers
import run


class EvaluationsTest(unittest.TestCase):
    def test_coverage(self):
        cases = run.dataset()
        self.assertEqual(Counter(c["task"] for c in cases), {
            "selection": 100, "approval": 50, "intent": 50,
            "next_step": 50, "evidence": 50, "disclosure": 50,
        })
        self.assertEqual(len({c["id"] for c in cases}), 350)
        for case in cases:
            self.assertNotIn("reference", case["input"] if isinstance(case["input"], dict) else {})

    def test_frozen_dataset(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "trial"
            run.build(output)
            self.assertEqual(len(run.load_cases(output)), 350)
            (output / "cases.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                run.load_cases(output)

    def test_token_denominator_and_failed_attempt(self):
        rows = [
            {"arm": "gpt-5-mini", "selected": "matches", "correct": True,
             "latency_ms": 10, "usage": {"prompt_tokens": 100, "completion_tokens": 10}},
            {"arm": "gpt-5-mini", "correct": False, "latency_ms": 99, "usage": {}},
        ]
        result = run.summarize(rows)["gpt-5-mini"]
        self.assertEqual(result["accuracy"], .5)
        self.assertEqual(result["mean_reported_model_tokens"], 110)
        self.assertEqual(result["median_ms"], 10)

    def test_no_labels_in_model_payload(self):
        class FakeSession:
            def request(self, url, body):
                self.body = body
                return {"status": 200, "response": {
                    "answers": {"route": {"choice": "matches", "probabilities": {"matches": 1}}}},
                        "latency_ms": 1, "usage": {}}
        session = FakeSession()
        case = next(c for c in run.dataset() if c["task"] == "intent")
        model_helpers.choose(session, "Decision-1", case["input"], "policy", {"matches": "matches"})
        self.assertNotIn("reference", session.body["state"])
        self.assertNotIn("expected", session.body["state"])

    def test_all_six_paths_offline(self):
        class FakeSession:
            def __init__(self, **kwargs):
                pass

            def request(self, url, body):
                return {"status": 200, "response": {"result": {"content": [
                    {"type": "text", "text": json.dumps({"tools": []})}]}},
                        "latency_ms": 2, "usage": {}}

            def close(self):
                pass

        def fake_choose(session, model, state, policy, options):
            self.assertNotIn("reference", state if isinstance(state, dict) else {})
            return {"status": 200, "selected": next(iter(options)), "latency_ms": 3,
                    "usage": {"input_tokens": 10, "output_tokens": 1}}

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "trial"
            run.build(output)
            required = {c["reference"]["expected"] for c in run.dataset() if c["task"] == "selection"} - {"none"}
            required |= {c["input"]["proposed_call"]["name"] for c in run.dataset() if c["task"] == "approval"}
            catalog = Path(temp) / "catalog.json"
            catalog.write_text(json.dumps([{"name": name, "description": "Synthetic contract",
                                           "inputSchema": {}} for name in sorted(required)]), encoding="utf-8")
            with patch.object(run, "Session", FakeSession), patch.object(run, "choose", fake_choose), \
                    patch.dict(run.os.environ, {"SEARCH_ENDPOINT": "https://fixture.example.invalid/mcp"}), \
                    patch("builtins.print"):
                for task in ["selection", "approval", "intent", "next_step", "evidence", "disclosure"]:
                    run.run(output, task, catalog if task in {"selection", "approval"} else None)
                    run.analyze(output, task)
            self.assertTrue((output / "selection-analysis.json").exists())


if __name__ == "__main__":
    unittest.main()
