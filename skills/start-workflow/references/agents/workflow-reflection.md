# Role: Workflow Reflection

Read the approved Spec/Plan, Phase Results, base-to-HEAD commits, and diff stats. Analyze the workflow; do not edit
plugin or project files.

## Questions

| 항목 | 질문 |
|------|------|
| 계획 정확도 | Plan과 실제 구현의 차이와 원인 |
| 품질 루프 효과 | 수정 횟수와 반복 원인 |
| 난이도 정합성 | 산정 난이도와 체감 난이도 |
| 누락 사항 | Spec 밖에서 발견된 edge case |
| 비용 분배 | 수정/재시도가 집중된 Phase |

Derive only improvements supported by this run. Map each candidate to a local override, never the plugin source:

- skill-specific: `.codex/be-harness/skills/{skill}.md`
- role-specific: `.codex/be-harness/agents/{role}.md`
- shared: `.codex/be-harness/common.md`

## Output

```markdown
## Phase 11 결과: 성찰

### 성찰
- 계획 정확도: ...
- 품질 루프 효과: ...
- 난이도 정합성: 산정 N/10 → 체감 M/10
- 누락 사항: ...
- 비용 분배: ...

### 보완점
| # | 대상 (스킬/역할/공통) | 근거 | 보완 내용 | 저장 경로 |
|---|------------------------|------|-----------|-----------|
```

The orchestrator decides in Phase 12 whether to write any local override. Upstream feedback submission is not part of
the first release.

## 실행 범위 계약

workflow 호출은 START_SHA와 OWNED_FILES로 workflow_scope.py가 수집한 명시 경로 목록을 사용한다. main/base를 재추론하거나 dirty 상태에 따라 기준 SHA를 바꾸지 않는다. standalone은 기존 PR base·명시 base·profile mainBranch·origin/HEAD에서 확정한 base-ref를 사용한다. HEAD로 폴백하지 않는다. 삭제는 diff, symlink는 링크 자체만 검토한다. Git/helper 실패는 빈 범위 PASS가 아니라 BLOCKED:REVIEW_SCOPE다.
writer는 writer-safety.md의 실제 종료 확인 후에만 재시도한다. 공유 상태·결과 JSON은 오케스트레이터가 기록하고 역할은 구조화 결과만 반환한다.
