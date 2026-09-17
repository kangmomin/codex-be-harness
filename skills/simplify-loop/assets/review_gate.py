#!/usr/bin/env python3
"""Validate one independent Arbiter ruling; owns no workflow state or writes."""

import argparse
import json
from pathlib import Path


def decide(response, candidate_id):
    """Check evidence presence, not its semantic validity (the Arbiter's job)."""
    if not isinstance(response, dict) or not isinstance(response.get("rulings"), list):
        return {"decision": "ARBITER_FAILURE", "reason": "Missing or invalid Arbiter response"}
    matches = [r for r in response["rulings"] if isinstance(r, dict) and r.get("candidateId") == candidate_id]
    if len(matches) != 1:
        return {"decision": "ARBITER_FAILURE", "reason": "Expected exactly one ruling for this candidate"}
    ruling = matches[0]
    if (
        not isinstance(candidate_id, str)
        or not candidate_id.strip()
        or ruling.get("candidateId") != candidate_id
        or ruling.get("verdict") not in ("PROCEED", "RECONSIDER", "HOLD")
        or any(
            not isinstance(ruling.get(key), str) or not ruling[key].strip()
            for key in ("reasoning", "action")
        )
        or type(ruling.get("objectionsResolved")) is not bool
        or not isinstance(ruling.get("evidence"), str)
    ):
        return {"decision": "ARBITER_FAILURE", "reason": "Missing or invalid Arbiter ruling"}
    if ruling["verdict"] != "PROCEED":
        return {"decision": ruling["verdict"], "reason": ruling["reasoning"]}
    if not ruling["objectionsResolved"] or not ruling["evidence"].strip():
        return {"decision": "HOLD", "reason": "UNRESOLVED_OBJECTION — 반론 미해소 또는 근거 없음"}
    return {"decision": "APPROVED", "reason": ruling["reasoning"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--input", required=True, type=Path, help="Original Arbiter response JSON with rulings[]")
    args = parser.parse_args()
    try:
        result = decide(json.loads(args.input.read_text(encoding="utf-8")), args.candidate_id)
    except (OSError, ValueError) as exc:
        result = {"decision": "ARBITER_FAILURE", "reason": f"Cannot read Arbiter ruling: {exc}"}
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result["decision"] == "ARBITER_FAILURE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
