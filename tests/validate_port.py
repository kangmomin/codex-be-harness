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
    "skills/start-workflow/references/agent-topology.md",
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

topology_path = skills_dir / "start-workflow" / "references" / "agent-topology.md"
require(topology_path.is_file(), "start-workflow: missing agent topology")
if topology_path.is_file():
    topology = topology_path.read_text(encoding="utf-8")
    for contract in [
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "Sol High",
        "Terra High",
        "Terra Max",
        "Luna xHigh",
        "Sol Max",
        "topology_bootstrapped=true",
        "topology_hop_limit=1",
        "USER_INPUT_REQUIRED: {질문}",
        "같은 orchestrator task",
        "새 bootstrap을 만들지 않으며",
        "fork_turns:none",
        "model_unavailable(...)",
        "CODEX-UNAVAILABLE",
        "SKIPPED:AGENT_DIED",
        "BLOCKED:AGENT_DIED",
        "degraded_fallback(...)",
        "Phase 8.8",
        "Phase 4.3",
        "Analyze A3",
        "Verify V3/V4",
        "결과를 Plan에 반영하거나 기각하는 판단은 Sol High만 한다",
        "Assumption Gate와 Phase 4.4에서 승인된 외부 효과 범위를 다시 확인",
        "실행 중 두 번 사망하면 타 모델 대체 없이 기존",
        "`agent_died(...)`",
    ]:
        require(contract in topology, f"start-workflow topology: missing {contract}")
    require(
        "Sol High만 `{STATE_FILE}`" in topology
        and "Executor, Luna, Advisor는 `{STATE_FILE}`과 Phase Results를 쓰지 않고" in topology
        and "Executor, Luna, Advisor는 파일을 쓰지 않고" not in topology,
        "start-workflow topology: state writer/result boundary missing",
    )
    require(
        "트리 내용은 직접 편집하지 않는다" in topology
        and "단일 writer는 해당 시점에 배정된 Terra executor" in topology,
        "start-workflow topology: single-writer boundary missing",
    )
    require(
        "Phase 5 전에 실패하면 상태 파일을 만들지 않는다" in topology,
        "start-workflow topology: bootstrap pre-Phase-5 boundary missing",
    )
    for value in re.findall(r"fork_turns\s*[:=]\s*[`\"']?([A-Za-z_-]+)", topology):
        require(value == "none", f"start-workflow topology: fixed spawn must use fork_turns:none, got {value}")

for relative in [
    "skills/start-workflow/references/build-phases.md",
    "skills/start-workflow/references/analyze-verify-modes.md",
    "skills/start-workflow/references/quality-loop.md",
    "skills/start-workflow/references/tdd.md",
    "skills/start-workflow/references/agent-prompts.md",
]:
    text = (ROOT / relative).read_text(encoding="utf-8")
    require("fork_turns:none" in text, f"{relative}: topology spawn boundary missing")

for path in (skills_dir / "start-workflow").rglob("*.md"):
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if "fork_turns" in line:
            require("none" in line, f"{path.relative_to(ROOT)}:{line_number}: fixed spawn must use fork_turns:none")

assignments = (skills_dir / "start-workflow" / "references" / "templates.md").read_text(encoding="utf-8")
for contract in ["Sol High orchestrator", "Terra executor", "Luna reflection", "fresh Sol Max advisor"]:
    require(contract in assignments, f"start-workflow templates: missing fixed assignment {contract}")
require(
    "Terra executor가 수행하고 Sol High가 승인·상태·commit 조정을 한다" in assignments,
    "start-workflow templates: Phase 12 remediation ownership missing",
)

quality_loop = (skills_dir / "start-workflow" / "references" / "quality-loop.md").read_text(encoding="utf-8")
for contract in [
    "PID/세션 핸들과 정리 결과를 Sol High에 반환",
    "Sol High만 그 handle을 `{STATE_FILE}`에 기록",
    "중첩 agent spawn이나 직접 commit 없이",
    "E2E와 실패 수정까지 같은 배정 안에서 수행하고 구조화 결과만 반환",
    "Sol High만 Implementation Notes에 append",
]:
    require(contract in quality_loop, f"quality-loop: missing topology contract {contract}")
require(
    "Terra executor가 `{STATE_FILE}`에 기록" not in quality_loop,
    "quality-loop: Terra must not write E2E handle to STATE_FILE",
)

agent_prompts = (skills_dir / "start-workflow" / "references" / "agent-prompts.md").read_text(encoding="utf-8")
for contract in [
    "Sol Max Phase 4.3이 실행 중 두 번 사망하면",
    "`CODEX-UNAVAILABLE` 결과로 Phase 4.4에 진행",
    "Terra는 중첩 agent spawn이나 직접 commit 없이 E2E와 실패 수정을 수행",
    "Sol High만 `{STATE_FILE}` 기록과 commit 조정을 한다",
]:
    require(contract in agent_prompts, f"agent-prompts: missing topology contract {contract}")
require(
    "Luna xHigh 읽기 전용 역할" in agent_prompts
    and "low-effort 역할" not in agent_prompts
    and "더 높은 effort의 독립 검증" not in agent_prompts
    and "Executor/Luna/Advisor는 `{STATE_FILE}`과 `{IMPL_NOTES}`를 직접 쓰지 않고" in agent_prompts
    and "Terra executor의 작업 트리 편집 권한은 전달된 파일 소유권 범위에서 유지" in agent_prompts,
    "agent-prompts: discovery role must use Luna xHigh topology",
)

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
