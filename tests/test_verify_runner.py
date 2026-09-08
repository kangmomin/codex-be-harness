from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/verify.sh'


class VerifyRunnerTests(unittest.TestCase):
    def test_python_and_node_failures_reach_the_required_command(self):
        with tempfile.TemporaryDirectory(prefix='verify runner ') as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'tests').mkdir()
            shutil.copyfile(SCRIPT, root / 'scripts/verify.sh')
            (root / 'tests/validate_port.py').write_text('print("structure passed")\n')
            test = root / 'tests/test_sentinel.py'
            node = root / 'tests/docgen.test.mjs'
            test.write_text('import unittest\nclass Sentinel(unittest.TestCase):\n    def test_failure(self):\n        self.fail("PYTHON_SENTINEL")\n')
            node.write_text('throw new Error("NODE_SENTINEL");\n')
            def run():
                return subprocess.run(['bash', str(root / 'scripts/verify.sh')],
                                      text=True, capture_output=True, timeout=30)
            failed = run()
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('PYTHON_SENTINEL', failed.stderr)
            self.assertNotIn('NODE_SENTINEL', failed.stdout)
            test.write_text('import unittest\nclass Sentinel(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(2 + 2, 4)\n')
            failed = run()
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('NODE_SENTINEL', failed.stdout + failed.stderr)
            node.write_text('import { test } from "node:test";\ntest("success", () => {});\n')
            passed = run()
            self.assertEqual(passed.returncode, 0, passed.stderr)


if __name__ == '__main__':
    unittest.main()
