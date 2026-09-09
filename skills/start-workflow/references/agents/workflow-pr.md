# Role: Workflow PR

## Workflow commit → 검증 → 원격 반영 배리어

start-workflow 내부에서는 VERSION/논리 commit/amend/rebase 준비까지 수행한 뒤 **push 전에** 현재 HEAD·소유 변경 목록·완료 단계를 Orchestrator에 반환한다. Orchestrator가 check-current로 검증 입력을 대조한다. 내용 동일 v2·HEAD 비의존 이벤트는 재사용하고, stale인 빌드/테스트만 실행해 RESULTS_FILE에 새 iteration을 기록한다. 현재 HEAD로 check-current와 Assumption Gate를 통과시킨다.
Orchestrator는 검증한 HEAD와 승인된 PUBLISH_POLICY를 전달해 같은 작업의 미완료 push/PR 단계만 재개한다. Worker는 HEAD가 같음을 즉시 확인하고 원격 반영한다. 이 재개에서는 VERSION/commit을 중복 수행하지 않는다. HEAD가 또 바뀌면 다시 배리어로 돌아간다. standalone은 요청된 검증/승인 범위를 따른다.

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

## 실행 범위 계약

workflow 호출은 START_SHA와 OWNED_FILES로 workflow_scope.py가 수집한 명시 경로 목록을 사용한다. main/base를 재추론하거나 dirty 상태에 따라 기준 SHA를 바꾸지 않는다. standalone은 기존 PR base·명시 base·profile mainBranch·origin/HEAD에서 확정한 base-ref를 사용한다. HEAD로 폴백하지 않는다. 삭제는 diff, symlink는 링크 자체만 검토한다. Git/helper 실패는 빈 범위 PASS가 아니라 BLOCKED:REVIEW_SCOPE다.
writer는 writer-safety.md의 실제 종료 확인 후에만 재시도한다. 공유 상태·결과 JSON은 오케스트레이터가 기록하고 역할은 구조화 결과만 반환한다.
