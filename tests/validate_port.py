#!/usr/bin/env python3
"""Deterministic structural checks for the Codex BE harness port."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


manifest_path = ROOT / ".codex-plugin" / "plugin.json"
require(manifest_path.is_file(), "missing .codex-plugin/plugin.json")
if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("name") == "codex-be-harness", "manifest name mismatch")
    require(manifest.get("skills") == "./skills/", "manifest skills path mismatch")
    require(bool(manifest.get("description")), "manifest description is empty")

required_skills = {
    "commit",
    "commit-hard-push",
    "commit-pr",
    "commit-push",
    "convention-check",
    "default-conventions",
    "doc-gen",
    "doctor",
    "e2e-test",
    "e2e-test-loop",
    "init",
    "request",
    "resolve-assumption",
    "simplify-loop",
    "start-workflow",
    "unit-test",
}

skills_dir = ROOT / "skills"
actual_skills = {path.name for path in skills_dir.iterdir() if path.is_dir()}
require(actual_skills == required_skills, f"skill inventory mismatch: {sorted(actual_skills ^ required_skills)}")

for skill_name in sorted(actual_skills):
    skill_file = skills_dir / skill_name / "SKILL.md"
    require(skill_file.is_file(), f"{skill_name}: missing SKILL.md")
    if not skill_file.is_file():
        continue
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    require(match is not None, f"{skill_name}: invalid frontmatter")
    if match:
        frontmatter = match.group(1)
        name_match = re.search(r"^name:\s*([^\n]+)$", frontmatter, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
        require(bool(name_match), f"{skill_name}: missing name")
        require(bool(desc_match), f"{skill_name}: missing description")
        if name_match:
            require(name_match.group(1).strip() == skill_name, f"{skill_name}: frontmatter name mismatch")

banned_literals = [
    "AskUserQuestion",
    "EnterPlanMode",
    "ExitPlanMode",
    "Workflow tool",
    "Skill tool",
    "CLAUDE_PLUGIN_ROOT",
    ".claude/",
    "CLAUDE.md",
    "/common:",
    "/be-harness:",
    "Claude Code",
]
runtime_files = list(skills_dir.rglob("*.md")) + [ROOT / "PROFILE.md", ROOT / "OVERRIDES.md"]
for path in runtime_files:
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    for token in banned_literals:
        require(token not in text, f"{path.relative_to(ROOT)}: banned runtime token {token!r}")
    require(
        not re.search(r"model:\s*(sonnet|opus|haiku)\b", text, re.IGNORECASE),
        f"{path.relative_to(ROOT)}: fixed provider model alias",
    )

known_resources = [
    "skills/start-workflow/references/agent-prompts.md",
    "skills/start-workflow/references/analyze-verify-modes.md",
    "skills/start-workflow/references/quality-loop.md",
    "skills/start-workflow/references/tdd.md",
    "skills/start-workflow/references/templates.md",
    "skills/start-workflow/references/agents/code-analyzer.md",
    "skills/start-workflow/references/agents/code-verifier.md",
    "skills/start-workflow/references/agents/scope-reviewer.md",
    "skills/start-workflow/references/agents/workflow-implementer.md",
    "skills/start-workflow/references/agents/workflow-pr.md",
    "skills/start-workflow/references/agents/workflow-reflection.md",
    "skills/request/references/edge-case-analyzer.md",
    "skills/simplify-loop/references/workflow-script.md",
    "skills/e2e-test/assets/e2e-lock.sh",
    "skills/e2e-test-loop/assets/api-test-cases-prompt.md",
]
for relative in known_resources:
    require((ROOT / relative).is_file(), f"missing mapped resource: {relative}")

for markdown in ROOT.rglob("*.md"):
    text = markdown.read_text(encoding="utf-8")
    for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = raw_target.split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        resolved = (markdown.parent / target).resolve()
        require(resolved.exists(), f"{markdown.relative_to(ROOT)}: broken link {raw_target}")

workflow = (skills_dir / "start-workflow" / "SKILL.md").read_text(encoding="utf-8")
for phase in range(1, 13):
    require(re.search(rf"\bPhase {phase}\b", workflow) is not None, f"start-workflow: missing Phase {phase}")
for flag in ["--hard", "--no-tdd", "--reflect", "--analyze", "--verify"]:
    require(flag in workflow, f"start-workflow: missing flag {flag}")
for contract in [
    "BLOCKED:FULLSTACK_HANDOFF_REQUIRED",
    "SKIPPED:REFLECT_NOT_REQUESTED",
    "planning-only",
    "Phase 4.4",
]:
    require(contract in workflow, f"start-workflow: missing contract {contract}")

simplify = (skills_dir / "simplify-loop" / "SKILL.md").read_text(encoding="utf-8")
for contract in ["10", "seen", "pendingRetry", "holds", "noProgressStreak"]:
    require(contract in simplify, f"simplify-loop: missing state contract {contract}")
simplify_state = (
    skills_dir / "simplify-loop" / "references" / "workflow-script.md"
).read_text(encoding="utf-8")
require(
    "hold가 1개 이상" in simplify_state,
    "simplify-loop: REVIEW_INCOMPLETE must require a non-empty hold set",
)

lock_script = skills_dir / "e2e-test" / "assets" / "e2e-lock.sh"
require(lock_script.is_file() and bool(lock_script.stat().st_mode & 0o111), "e2e-lock.sh must be executable")
if lock_script.is_file():
    lock_text = lock_script.read_text(encoding="utf-8")
    require(
        'sleep_for="$remaining"' in lock_text,
        "e2e-lock.sh must cap the final poll sleep to the remaining timeout",
    )

profile = (ROOT / "PROFILE.md").read_text(encoding="utf-8")
require(
    "profile 자체가 없으면 값을 추측하지 않는다" in profile,
    "PROFILE.md must agree with start-workflow's missing-profile stop rule",
)

compatibility = (ROOT / "COMPATIBILITY.md").read_text(encoding="utf-8")
source_inventory = [
    *[f"be-harness/skills/{name}/**" for name in [
        "start-workflow", "request", "unit-test", "simplify-loop", "convention-check",
        "default-conventions", "e2e-test", "e2e-test-loop", "init", "doctor",
    ]],
    *[f"be-harness/agents/{name}.md" for name in [
        "code-analyzer", "code-verifier", "edge-case-analyzer", "scope-reviewer",
        "workflow-implementer", "workflow-pr", "workflow-reflection",
    ]],
]
for source in source_inventory:
    require(source in compatibility, f"COMPATIBILITY.md missing mapping for {source}")

require((ROOT / "tests" / "scenario-contracts.md").is_file(), "missing scenario contracts")

if errors:
    print("PORT VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"PORT VALIDATION PASSED: {len(actual_skills)} skills, {len(known_resources)} mapped resources")
