# Role: Workflow PR

Perform the approved Phase 10 branch/push/PR effects. The orchestrator must already have passed Phase 4.4 approval and
must run the Assumption Gate immediately before this role. Read `../../../commit-pr/SKILL.md`; its current branch/base,
logical commit, VERSION, existing-PR, push, and draft/ready rules are canonical.

## Required behavior

- Resolve the base once from project branch rules and reuse it for VERSION comparison and PR base.
- Reuse an existing open PR for the current branch and synchronize its body when needed.
- If a VERSION file exists, bump patch according to the canonical sibling procedure and avoid base-version regression.
- Create or rename a feature/hotfix branch only within the approved effects.
- Re-run the Assumption Gate over base diff additions and unpushed commit bodies. Any remaining tag returns
  `BLOCKED:ASSUMPTION_UNRESOLVED`; do not push or create/update a PR.
- Push normally, never force-push unless the user's approved request explicitly authorizes the separate hard procedure.
- Create a draft PR by default; ready only when explicitly requested. Include Summary, Changes, Test Plan, and resolved
  decisions without provider attribution.

## Output

```markdown
## Phase 10 결과: PR
- 상태: DONE | BLOCKED:ASSUMPTION_UNRESOLVED
- 브랜치: {branch}
- base: {base}
- PR URL: {url or 없음}
- PR 상태: draft | ready | 없음
- 태그 목록: {file:line / commit hash, or 없음}
```

If authentication or permission prevents PR creation after an approved push, report the exact error and leave the
already-pushed state explicit; do not silently retry with a different remote or credential.
