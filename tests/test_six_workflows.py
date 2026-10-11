import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import six_workflows as six
from workflow_eval import World


class SixWorkflowsTest(unittest.TestCase):
    def test_coverage_and_frozen_data(self):
        self.assertEqual(len({c["id"] for c in six.tests()}), 50)
        self.assertEqual(len(six.AREAS), 6)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "run"
            six.build(output)
            self.assertEqual(len(six.load(output)), 50)
            (output / "cases.json").write_text("[]")
            with self.assertRaises(ValueError):
                six.load(output)

    def test_no_hidden_ground_truth_in_checkpoint(self):
        c = six.tests()[0]
        state = six.public_state(c, [], World(c))
        self.assertNotIn("initial", state)
        self.assertNotIn("reference", state)
        self.assertNotIn("answer", state["task"]["task_contract"])
        self.assertEqual(six.protected_values(state), [])

    def test_code_check_uses_scope_not_ground_truth(self):
        c = six.tests()[0]
        state = six.public_state(c, [], World(c), {
            "tool": "read_record", "arguments": {"id": "wrong", "environment": "production"}})
        self.assertEqual(six.intent_rule(state), "mismatch")
        self.assertEqual(six.evidence_rule(state), "insufficient")
        state["observations"] = [{"tool": "read_record", "arguments": {},
                                  "result": {**c["initial"], "environment": "staging"}}]
        self.assertEqual(six.evidence_rule(state), "insufficient")
        state["observations"][0]["result"]["environment"] = "production"
        self.assertEqual(six.evidence_rule(state), "sufficient")

    def test_one_checkpoint_only_for_each_integration(self):
        c = six.tests()[0]

        def fake_gpt(session, messages, allowed):
            if not any(m["role"] == "tool" for m in messages):
                message = {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "read1", "type": "function", "function": {"name": "read_record",
                        "arguments": '{"id":"' + c["initial"]["id"] + '","environment":"production"}'}}]}
            else:
                message = {"role": "assistant", "content": '{"outcome":"completed","answer":"Ada"}'}
            return {"status": 200, "latency_ms": 5, "usage": {"prompt_tokens": 10, "completion_tokens": 2}}, message

        def fake_choose(session, model, state, policy, options):
            area = next(k for k, p in six.POLICIES.items() if p == policy)
            return {"status": 200, "selected": six.code_choice(area, state),
                    "latency_ms": 2, "usage": {"input_tokens": 10, "output_tokens": 1}}

        with patch.object(six, "gpt", fake_gpt), patch.object(six, "choose", fake_choose):
            for area in six.AREAS:
                for arm in six.ARMS:
                    row = six.trial(None, copy.deepcopy(c), area, arm)
                    self.assertTrue(row["safe_success"], (area, arm, row))
                    self.assertEqual({r["checkpoint"] for r in row["checkpoints"]},
                                     set() if arm == "gpt_only" else {area})
                    self.assertTrue(all(r["stage"] in {"agent", area} for r in row["model_calls"]))

    def test_tokens_include_both_models_and_failed_tasks(self):
        row = {"safe_success": False, "active_latency_ms": 6, "events": [], "checkpoints": [],
               "unsafe_calls": 0, "invalid_calls": 0, "unnecessary_approvals": 0,
               "failure": "failed", "family": "read", "model_calls": [
                   {"model": "gpt-5-mini", "usage": {"prompt_tokens": 10, "completion_tokens": 3}},
                   {"model": "Decision-1", "usage": {"input_tokens": 6, "output_tokens": 1}}]}
        self.assertEqual(six.metrics([row])["mean_reported_native_tokens"], 20)


if __name__ == "__main__":
    unittest.main()
