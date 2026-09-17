"""Same Arbiter acceptance vectors as the source executable simplify loop."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/simplify-loop/assets/review_gate.py"
spec = importlib.util.spec_from_file_location("review_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
VECTORS = json.loads((ROOT / "tests/fixtures/simplify-arbiter.json").read_text())


class SimplifyReviewGateTests(unittest.TestCase):
    def test_shared_acceptance_vectors(self):
        for case in VECTORS["cases"]:
            with self.subTest(case["name"]):
                ruling = {**VECTORS["ruling"], **case.get("patch", {})}
                if "omit" in case:
                    del ruling[case["omit"]]
                self.assertEqual(case["expected"], gate.decide({"rulings": [ruling]}, "i1-c1")["decision"])

    def test_absent_or_nonobject_ruling_and_invalid_candidate_fail_closed(self):
        for ruling in [None, [], "PROCEED", 1, True]:
            with self.subTest(ruling=ruling):
                self.assertEqual("ARBITER_FAILURE", gate.decide(ruling, "i1-c1")["decision"])
        for candidate_id in [None, "", " ", 1]:
            with self.subTest(candidate_id=candidate_id):
                self.assertEqual("ARBITER_FAILURE", gate.decide({"rulings": [VECTORS["ruling"]]}, candidate_id)["decision"])

    def test_duplicate_rulings_fail_closed_without_blocking_other_candidates(self):
        proceed = VECTORS["ruling"]
        hold = {**proceed, "verdict": "HOLD", "objectionsResolved": False}
        for rulings in [[], [proceed, hold], [hold, proceed], [proceed, hold, proceed]]:
            with self.subTest(rulings=rulings):
                response = {"rulings": [*rulings, {**proceed, "candidateId": "another"}]}
                self.assertEqual("ARBITER_FAILURE", gate.decide(response, "i1-c1")["decision"])
                self.assertEqual("APPROVED", gate.decide(response, "another")["decision"])
        for response in [{}, {"rulings": {}}, {"rulings": [None, "PROCEED"]}]:
            self.assertEqual("ARBITER_FAILURE", gate.decide(response, "i1-c1")["decision"])

    def test_cli_preserves_input_and_reports_missing_or_malformed_json(self):
        with tempfile.TemporaryDirectory(prefix="simplify gate ") as directory:
            path = Path(directory) / "ruling.json"
            command = [sys.executable, "-I", "-B", str(SCRIPT), "--candidate-id", "i1-c1", "--input", str(path)]
            missing = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(1, missing.returncode)
            self.assertEqual("ARBITER_FAILURE", json.loads(missing.stdout)["decision"])
            for body, code, decision in [("{broken", 1, "ARBITER_FAILURE"),
                                         (json.dumps({"rulings": [VECTORS["ruling"]]}), 0, "APPROVED"),
                                         (json.dumps({"rulings": [{**VECTORS["ruling"], "objectionsResolved": False}]}), 0, "HOLD")]:
                path.write_text(body)
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(code, result.returncode, result.stderr)
                self.assertEqual(decision, json.loads(result.stdout)["decision"])
                self.assertEqual(body, path.read_text())

    def test_native_instructions_route_majority_and_require_gate_before_writer(self):
        instructions = (ROOT / "skills/simplify-loop/references/workflow-script.md").read_text()
        self.assertNotIn("승인. minority rationale을 경고로 기록", instructions)
        for token in ["3/4", "risks", "objectionsResolved", "review_gate.py", "APPROVED", "ARBITER_FAILURE"]:
            self.assertIn(token, instructions)


if __name__ == "__main__":
    unittest.main()
