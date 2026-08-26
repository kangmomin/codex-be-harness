> Phase 4.2~11의 위임 공통 계약이다. 단독 실행하지 않는다.
> `{CWD}`, `{RUN_DIR}`, `{STATE_FILE}`, `{IMPL_NOTES}`는 상위 스킬이 해결한 절대 경로다.

# Subagent prompts and recovery

## 공통 envelope

모든 서브에이전트 프롬프트에 아래 정보를 넣는다.

```text
프로젝트 루트: {CWD}
실행 디렉터리: {RUN_DIR}
상태 파일: {STATE_FILE} (Phase 8.8에는 전달 금지)
구현 노트: {IMPL_NOTES} (읽기 전용 역할에는 쓰기 금지)
현재 Phase: {PHASE}
남은 Phase: {REMAINING}
배정 model/effort: {선택값}
파일 소유권: {읽기 범위 / 수정 허용 범위}
반환 계약: {해당 Phase 출력 형식}
```

`{STATE_FILE}`과 `{IMPL_NOTES}`는 고정 경로로 추측하지 말고 받은 절대 경로만 사용한다. 서브에이전트는
담당 Phase 밖의 상태를 완료 처리하지 않는다. 읽기 전용 역할이 파일을 수정했다면 그 변경은 결과로
채택하지 않고, 이슈 목록만 사용한다.

탐색·수집 질문이 3개 이상이면 3~10개를 한 low-effort 역할에 묶는다. 한 질문마다 새 역할을 만들지
않는다. 반환은 질문별 `file:line`, 핵심 snippet 최대 5줄, 한 줄 결론으로 제한한다. `없음` 결론에는
검색한 pattern과 경로를 반드시 붙인다. 부재가 Plan을 바꾸는 결정적 근거라면 오케스트레이터가 직접
재확인하거나 더 높은 effort의 독립 검증을 사용한다.

### Implementation Notes 블록

파일을 수정하는 역할에만 넣는다.

```text
설계 결정·편차·트레이드오프·미결 질문이 생기면 코드 수정 전에 {IMPL_NOTES}의
해당 섹션에 한 줄 append한다. 기존 줄은 수정하지 않고 Markdown만 쓴다.
[Assumption]은 반드시 ## 편차에도 같은 항목으로 기록한다.
```

## 사망/불완전 결과 처리

오류, 응답 없음, 필수 반환 형식 누락을 실패로 감지한다. Phase마다 최대 두 번 재시도한다.

1. 동일 역할·동일 effort로 1회 재시도한다.
2. 한 단계 낮은 실행 비용으로 1회 재시도하고 `간결 모드: 산출물 계약은 유지하고 핵심만 수행`을
   추가한다. 최저 등급이면 같은 조건을 유지한다.

| 두 번 실패한 역할 | 처리 |
|-------------------|------|
| Phase 8.8 격리 Read-back | `SKIPPED:AGENT_DIED`; 오케스트레이터 대체 금지 |
| 읽기 전용 스캔·문서·PR·성찰 | 변경 파일만 대상으로 오케스트레이터 축소 수행; `DONE` + `degraded_fallback(...)` |
| 구현·수정(6.1, 6.2, 7 fix, 8.5) | `BLOCKED:AGENT_DIED`; 중단 |

재시도 성공은 `agent_retry({원인})`를 진단 셀에 기록한다. 한 실행에서 세션/예산 한계 사망이 2회
누적되면 Phase 8.4와 8.8 검증 독립성을 우선 보존하고 비검증 위임은
`SKIPPED:BUDGET_PRESERVED`할 수 있다. 모든 축소/재시도는 최종 보고의 `축소 실행 내역`에 남긴다.

## Phase 4 review prompts

Plan 리뷰어는 Spec과 Plan을 읽기만 한다. 각 관점마다 다음 형식으로 반환한다.

```text
Verdict: APPROVE | CONCERN | REJECT
Issues:
- {Spec ID 또는 Plan 항목} — {문제와 근거 file:line}
Suggestions:
- {최소 수정 제안}
```

fresh-context architect는 이전 결론을 답으로 주입하지 않는다. Spec-Plan 추적성, 레이어 책임, 파일
소유권, 검증 누락, 단순화 여지를 독립적으로 평가하도록 한다.

## Phase 6.2 Green

역할 계약은 [agents/workflow-implementer.md](agents/workflow-implementer.md)를 함께 전달한다.

```text
{STATE_FILE}의 확정 Spec과 Plan 순서대로 구현한다. 기존 프로젝트 스타일을 따르고 Spec 밖 동작은
변경하지 않는다. 변경 파일, 커밋 수, Plan diff, [Assumption], [TestConflict]를 반환한다.
```

TDD 활성 시 추가한다.

```text
테스트 파일을 수정하지 않는다. 테스트가 Spec과 충돌한다고 판단하면 코드와 테스트 모두 유지하고
[TestConflict]만 보고한다. Test Map의 모든 Green과 baseline 대비 신규 실패 0건이 통과 조건이다.
```

`sequential`에서는 논리 단위 커밋을 허용한다. `parallel-slices`에서는 각 역할에 정확한 파일 범위를
전달하고 커밋·빌드를 금지한다. 오케스트레이터가 모든 범위 밖 변경 여부를 검사한 뒤 단일 커밋한다.

## Phase 7 build-fix

```text
{buildCommand}의 아래 오류를 원인 범위 안에서만 수정한다.
오류: {BUILD_OUTPUT}
수정 후 같은 명령으로 확인하고 수정 파일과 원인을 반환한다. 무관한 정리는 하지 않는다.
```

구현 노트 블록을 포함하고 성공한 수정만 `Fix: 빌드 에러 수정 (Phase 7)`로 커밋한다.

## Phase 9 API docs

```text
{apiDocsPath}의 포맷을 내용으로 판정한다. 이번 Spec에서 추가·변경된 endpoint와 field만 파일에
반영한다. 외부 서비스에는 전송하지 않는다. 문서 diff와 반영 목록을 반환한다.
```

## Phase 10 PR

오케스트레이터가 먼저 Assumption Gate를 통과시킨다. 일반 모드는 `../../commit-pr/SKILL.md`, hard
모드는 `../../commit-hard-push/SKILL.md`를 읽고 해당 절차를 수행한다. Phase 4.4에 고지한 원격 효과만
허용한다. 일반 모드 반환에는 브랜치, base, PR URL, draft/ready 상태가 있어야 한다.

## Phase 11 reflection

역할 계약은 [agents/workflow-reflection.md](agents/workflow-reflection.md)를 전달한다. 상태 파일과 base
대비 커밋/diff를 읽어 계획 정확도, 품질 루프 효과, 난이도 정합성, 누락, 비용 집중 Phase를 분석한다.
개선안은 `.codex/be-harness/**` 로컬 오버라이드 후보로만 반환하고 직접 쓰지 않는다.

## 역할 문서

- Analyze: [agents/code-analyzer.md](agents/code-analyzer.md)
- Verify: [agents/code-verifier.md](agents/code-verifier.md)
- 요청 보강: [agents/edge-case-analyzer.md](agents/edge-case-analyzer.md)
- Scope 검증: [agents/scope-reviewer.md](agents/scope-reviewer.md)
- 구현: [agents/workflow-implementer.md](agents/workflow-implementer.md)
- PR: [agents/workflow-pr.md](agents/workflow-pr.md)
- 성찰: [agents/workflow-reflection.md](agents/workflow-reflection.md)
