#!/usr/bin/env python3
"""Deterministic structural checks for the Codex BE harness port."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import warnings
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
PINNED_SCRIPT_SHA256 = {
    "skills/start-workflow/assets/risk_facts.py": "1ea5ff3a3ffe253054b6cc68f21429c0889baa2bc9b67a3be86cae6a8301094a",
    "skills/start-workflow/assets/test_failures.py": "8362c4ad45d8d674605c32a59806f47b6b7c70d242b6c8e93d8f92842ef64a5d",
    "skills/start-workflow/assets/workflow_archive.py": "cca44dabb0c703c570d89b4808875da3cc9fb8a1134f0e533cebf7dfa130a302",
    "skills/e2e-test-loop/assets/render_e2e_report.py": "9d6d26a57a292d13501c1bad1370c0afcb39ba97830ee8e380cdb5d1a3e2904c",
}


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
    manifest_version = str(manifest.get("version", ""))
    require(bool(manifest_version), "manifest version is empty")
    for doc in ["COMPATIBILITY.md", "README.md"]:
        require(
            f"codex-be-harness@{manifest_version}" in (ROOT / doc).read_text(encoding="utf-8"),
            f"{doc} must reference codex-be-harness@{manifest_version}",
        )

required_skills = {
    "commit",
    "commit-hard-push",
    "commit-pr",
    "commit-push",
    "config",
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

html_report_residue = re.compile(
    r"e2e-report\.html|impl-notes\.html|리포트 HTML|HTML 렌더링|HTML 리포트|api-test-cases-prompt",
    re.IGNORECASE,
)
html_report_runtime_files = list(skills_dir.rglob("*.md")) + [
    ROOT / "PROFILE.md",
    ROOT / "OVERRIDES.md",
    ROOT / "README.md",
    ROOT / ".codex-plugin" / "plugin.json",
]
for path in html_report_runtime_files:
    if path.is_file():
        require(
            html_report_residue.search(path.read_text(encoding="utf-8")) is None,
            f"{path.relative_to(ROOT)}: legacy HTML report residue",
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
    "skills/start-workflow/assets/risk_facts.py",
    "skills/start-workflow/assets/test_failures.py",
    "skills/start-workflow/assets/workflow_archive.py",
    "skills/e2e-test-loop/assets/render_e2e_report.py",
    "skills/start-workflow/references/verification-tier.md",
]
for relative in known_resources:
    require((ROOT / relative).is_file(), f"missing mapped resource: {relative}")

python_assets = sorted(skills_dir.glob("*/assets/*.py"))
require(len(python_assets) >= 4, f"expected at least 4 Python assets, got {len(python_assets)}")
for path in python_assets:
    relative = path.relative_to(ROOT)
    source = path.read_text(encoding="utf-8")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(source, str(path), "exec")
    except (SyntaxError, Warning) as exc:
        require(False, f"{relative}: python syntax check failed: {exc}")

for relative, expected_hash in PINNED_SCRIPT_SHA256.items():
    path = ROOT / relative
    if not path.is_file():
        require(False, f"missing pinned script: {relative}")
        continue
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    require(
        actual_hash == expected_hash,
        f"{relative}: SHA-256 mismatch: expected {expected_hash}, actual {actual_hash}",
    )

upstream_root = Path("/workspace/harness-plugins/be-harness")
if upstream_root.exists():
    for relative in PINNED_SCRIPT_SHA256:
        path = ROOT / relative
        upstream_path = upstream_root / relative
        if path.is_file() and upstream_path.is_file() and path.read_bytes() != upstream_path.read_bytes():
            print(f"note: {relative} differs from local upstream working tree (pinned hash still matches)")

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
for flag in ["--hard", "--no-tdd", "--tier standard", "--reflect", "--analyze", "--verify"]:
    require(flag in workflow, f"start-workflow: missing flag {flag}")
for contract in [
    "BLOCKED:FULLSTACK_HANDOFF_REQUIRED",
    "SKIPPED:REFLECT_NOT_REQUESTED",
    "planning-only",
    "Phase 4.4",
    "BLOCKED:DUPLICATE_IN_PROGRESS",
    "외부 CLI 리뷰어를 호출하지 않는다",
    "{PROFILE_PATH}",
    "같은 orchestrator task",
    "SKIPPED:TIER_LIGHT",
    "{PLAN_MAX}",
    "{QL_MAX}",
    "tier_escalated",
    "script_fallback",
    "RUN_ID",
    "START_SHA",
    "BLOCKED:STATE_SCHEMA_MISMATCH",
    "{WORK_REPORT}",
    "## Profile Snapshot",
]:
    require(contract in workflow, f"start-workflow: missing contract {contract}")

build_phases = (skills_dir / "start-workflow" / "references" / "build-phases.md").read_text(encoding="utf-8")
for contract in [
    "git worktree list",
    "BLOCKED:DUPLICATE_IN_PROGRESS",
    "workflow-report.md",
    "`## 편차`에서 `[Assumption]`",
    "{PLAN_MAX}",
    "{QL_MAX}",
    "verification-tier.md",
    "BLOCKED:LOCK_UNAVAILABLE",
    "## Flags",
    "## Profile Snapshot",
    "START_SHA",
    "workflow_archive.py",
]:
    require(contract in build_phases, f"build-phases: missing contract {contract}")

templates_doc = (skills_dir / "start-workflow" / "references" / "templates.md").read_text(encoding="utf-8")
for contract in ["workflow-report.md", "workflow_archive.py", "-workflow-report.md", "## 부록 A", "## Final Decisions", "검증 티어"]:
    require(contract in templates_doc, f"templates: missing md archive contract {contract}")

state_begin_marker = "<!-- state-template-begin -->"
state_end_marker = "<!-- state-template-end -->"
state_begin_count = templates_doc.count(state_begin_marker)
state_end_count = templates_doc.count(state_end_marker)
require(state_begin_count == 1, f"templates: expected one state-template-begin marker, got {state_begin_count}")
require(state_end_count == 1, f"templates: expected one state-template-end marker, got {state_end_count}")

state_template = ""
if state_begin_count == 1 and state_end_count == 1:
    state_begin_position = templates_doc.find(state_begin_marker)
    state_end_position = templates_doc.find(state_end_marker)
    require(state_begin_position < state_end_position, "templates: state-template-begin must precede state-template-end")
    if state_begin_position < state_end_position:
        state_template = templates_doc[state_begin_position + len(state_begin_marker):state_end_position]
        for contract in [
            "## Flags",
            "- SCHEMA: 2",
            "- MODE: be",
            "- RUN_ID:",
            "- START_SHA:",
            "- TIER:",
            "## Verification Tier",
            "- 계산 티어:",
            "- 최종 티어:",
            "## Profile Snapshot",
            "- profile_path:",
            "- profile_sha256:",
            "- resolved_report_dir:",
            "- resolved_e2e_lock_dir:",
            "## Final Decisions",
            "## Artifacts",
            "workflow-report: 미생성",
            "e2e-report: 미생성",
            "tier_escalated(",
            "script_fallback(",
        ]:
            require(contract in state_template, f"templates state template: missing contract {contract}")
        require("## Test Baseline" not in state_template, "templates: initial state template must not contain Test Baseline")

baseline_headers = re.findall(r"^## Test Baseline\s*$", templates_doc, re.MULTILINE)
require(len(baseline_headers) == 1, f"templates: expected one append Test Baseline header, got {len(baseline_headers)}")

tdd_doc = (skills_dir / "start-workflow" / "references" / "tdd.md").read_text(encoding="utf-8")
baseline_table_header = "| suite | 명령 | 러너 완주 | 통과 | 실패 | 실패 목록 (식별자 :: 정규화 시그니처) |"
for label, document in [("templates", templates_doc), ("tdd", tdd_doc)]:
    require(baseline_table_header in document, f"{label}: missing baseline six-cell header")
    for status in [
        "SKIPPED:USER_OPT_OUT",
        "SKIPPED:NO_TEST_COMMAND",
        "SKIPPED:NO_TEST_INFRA",
        "SKIPPED:TASK_TYPE",
        "SKIPPED:NO_TEST_BASIS",
    ]:
        require(status in document, f"{label}: missing baseline status {status}")
    require("수집 실패 — regression 판정 불가" in document, f"{label}: missing collect-failed baseline marker")

for contract in ["--emit-baseline", "script_fallback(test_failures:", "BLOCKED:STATE_SCHEMA_MISMATCH"]:
    require(contract in tdd_doc, f"tdd: missing baseline contract {contract}")

tier_doc = (skills_dir / "start-workflow" / "references" / "verification-tier.md").read_text(encoding="utf-8")
require("`--no-tdd` 미지정" in tier_doc, "verification-tier: missing --no-tdd light-tier gate")
require("`## Flags`의 `TDD`가 `true`" not in tier_doc, "verification-tier: Phase 2 must not read Phase 5 flags")

request_doc = (skills_dir / "request" / "SKILL.md").read_text(encoding="utf-8")
require("기본값" in request_doc and "`[Assumption]`으로 표기" in request_doc, "request: missing default-answer batching rule")

unit_test_doc = (skills_dir / "unit-test" / "SKILL.md").read_text(encoding="utf-8")
require("## Profile Snapshot" in unit_test_doc, "unit-test: missing snapshot-first profile rule")

e2e_doc = (skills_dir / "e2e-test" / "SKILL.md").read_text(encoding="utf-8")
for contract in [
    "mode: workflow",
    "{mainBranch}...HEAD",
    "SKIPPED:NO_AUTH",
    "--smoke",
    "SMOKE_OMITTED",
    "BLOCKED:LOCK_UNAVAILABLE",
    "- 실행 수준:",
    "## Profile Snapshot",
    "resolved_e2e_lock_dir",
    "Project Notes",
]:
    require(contract in e2e_doc, f"e2e-test: missing contract {contract}")
require("main...HEAD" not in e2e_doc.replace("{mainBranch}...HEAD", ""), "e2e-test: hardcoded main base ref")

e2e_loop_doc = (skills_dir / "e2e-test-loop" / "SKILL.md").read_text(encoding="utf-8")
for contract in [
    "-e2e-report.md",
    "render_e2e_report.py",
    "--smoke",
    "BLOCKED:LOCK_UNAVAILABLE",
    "E2E 리포트:",
    "set -C",
    "## Profile Snapshot",
    "resolved_report_dir",
    "- 실행 수준:",
]:
    require(contract in e2e_loop_doc, f"e2e-test-loop: missing contract {contract}")
require('--level-note "smoke 미적용' not in e2e_loop_doc, "e2e-test-loop: renderer adds the smoke prefix itself")

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
        "{PLAN_MAX}",
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
    "E2E 리포트:",
    "BLOCKED:LOCK_UNAVAILABLE",
    "e2e-report:",
    "## Profile Snapshot",
    "- 수정된 이슈:",
    "이슈: 0건",
]:
    require(contract in quality_loop, f"quality-loop: missing topology contract {contract}")
require(
    "Terra executor가 `{STATE_FILE}`에 기록" not in quality_loop,
    "quality-loop: Terra must not write E2E handle to STATE_FILE",
)

agent_prompts = (skills_dir / "start-workflow" / "references" / "agent-prompts.md").read_text(encoding="utf-8")
for contract in [
    "## 대기 규약",
    "mode: workflow",
    "Sol Max Phase 4.3이 실행 중 두 번 사망하면",
    "`CODEX-UNAVAILABLE` 결과로 Phase 4.4에 진행",
    "Terra는 중첩 agent spawn이나 직접 commit 없이 E2E와 실패 수정을 수행",
    "Sol High만 `{STATE_FILE}` 기록과 commit 조정을 한다",
    "## Profile Snapshot",
    "파일을 다시 읽지 않는다",
]:
    require(contract in agent_prompts, f"agent-prompts: missing topology contract {contract}")
require("profile 경로: {PROFILE_PATH}" not in agent_prompts, "agent-prompts: envelope must pass the profile snapshot, not only the live path")
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
require("## profile 해석" in profile and "{PROFILE_PATH}" in profile, "PROFILE.md must define the profile resolution rule")
require("## Profile Snapshot" in profile, "PROFILE.md must define the workflow snapshot-first rule")

profile_keys: set[str] = set()
profile_delimiters = list(re.finditer(r"^---\s*$", profile, re.MULTILINE))
require(len(profile_delimiters) >= 2, "PROFILE.md must contain two frontmatter delimiters")
if len(profile_delimiters) >= 2:
    profile_frontmatter = profile[profile_delimiters[0].end():profile_delimiters[1].start()]
    profile_key_tokens = [
        *re.findall(r"^([A-Za-z0-9_-]+):", profile_frontmatter, re.MULTILINE),
        *re.findall(r"^# ([A-Za-z0-9_-]+):", profile_frontmatter, re.MULTILINE),
    ]
    profile_key_counts = Counter(profile_key_tokens)
    duplicate_profile_keys = sorted(key for key, count in profile_key_counts.items() if count != 1)
    require(not duplicate_profile_keys, f"PROFILE.md duplicate frontmatter keys: {duplicate_profile_keys}")
    profile_keys = set(profile_key_tokens)

config_doc = (skills_dir / "config" / "SKILL.md").read_text(encoding="utf-8")
for contract in ["BLOCKED:NO_PROFILE", "{PROFILE_PATH}", "한 번의", "config:keys-begin"]:
    require(contract in config_doc, f"config: missing contract {contract}")

begin_marker = "<!-- config:keys-begin"
end_marker = "<!-- config:keys-end"
begin_count = config_doc.count(begin_marker)
end_count = config_doc.count(end_marker)
require(begin_count == 1, f"config: expected one keys-begin marker, got {begin_count}")
require(end_count == 1, f"config: expected one keys-end marker, got {end_count}")

config_keys: set[str] = set()
config_keys_valid = False
if begin_count == 1 and end_count == 1:
    begin_position = config_doc.find(begin_marker)
    end_position = config_doc.find(end_marker)
    require(begin_position < end_position, "config: keys-begin marker must precede keys-end marker")
    begin_line_end = config_doc.find("\n", begin_position)
    require(begin_line_end != -1 and begin_line_end < end_position, "config: keys-begin marker must end before keys-end marker")
    if begin_position < end_position and begin_line_end != -1 and begin_line_end < end_position:
        config_key_tokens = re.findall(r"`([^`]+)`", config_doc[begin_line_end + 1:end_position])
        config_key_counts = Counter(config_key_tokens)
        duplicate_config_keys = sorted(key for key, count in config_key_counts.items() if count != 1)
        require(not duplicate_config_keys, f"config: duplicate key marker tokens: {duplicate_config_keys}")
        config_keys = set(config_key_tokens)
        config_keys_valid = True

if len(profile_delimiters) >= 2 and config_keys_valid:
    require(
        not profile_keys - config_keys,
        f"config: keys missing from marker: {sorted(profile_keys - config_keys)}",
    )
    require(
        not config_keys - profile_keys,
        f"config: marker keys missing from PROFILE.md: {sorted(config_keys - profile_keys)}",
    )

snapshot_match = re.search(
    r"^## Profile Snapshot\s*$\n(.*?)(?=^## |\Z)",
    state_template,
    re.MULTILINE | re.DOTALL,
)
require(snapshot_match is not None, "templates: missing Profile Snapshot section in state template")
if snapshot_match:
    snapshot_key_tokens = re.findall(r"^- ([A-Za-z0-9_]+):", snapshot_match.group(1), re.MULTILINE)
    snapshot_key_counts = Counter(snapshot_key_tokens)
    expected_snapshot_keys = profile_keys | {
        "profile_path",
        "profile_sha256",
        "resolved_report_dir",
        "resolved_e2e_lock_dir",
    }
    require(
        set(snapshot_key_counts) == expected_snapshot_keys,
        "templates: Profile Snapshot key mismatch: "
        f"missing={sorted(expected_snapshot_keys - set(snapshot_key_counts))}, "
        f"extra={sorted(set(snapshot_key_counts) - expected_snapshot_keys)}",
    )
    invalid_snapshot_counts = sorted(key for key, count in snapshot_key_counts.items() if count != 1)
    require(not invalid_snapshot_counts, f"templates: Profile Snapshot duplicate keys: {invalid_snapshot_counts}")
    for key, value in re.findall(r"^- ([A-Za-z0-9_]+):[ \t]*(.*)$", snapshot_match.group(1), re.MULTILINE):
        require(
            re.fullmatch(r"\{.+\}", value) is not None,
            f"templates: Profile Snapshot row must be a placeholder: {key}",
        )

compatibility = (ROOT / "COMPATIBILITY.md").read_text(encoding="utf-8")
source_inventory = [
    *[f"be-harness/skills/{name}/**" for name in [
        "start-workflow", "request", "unit-test", "simplify-loop", "convention-check",
        "default-conventions", "e2e-test", "e2e-test-loop", "init", "doctor", "config",
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
