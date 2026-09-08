#!/usr/bin/env bash
# Required repository checks; dependency installation is a separate setup step.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python3 -B tests/validate_port.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
node --test tests/docgen.test.mjs
