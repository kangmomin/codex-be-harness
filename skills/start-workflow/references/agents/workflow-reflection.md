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
