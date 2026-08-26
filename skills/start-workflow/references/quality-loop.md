> Phase 8의 상세 계약이다. 8.1~8.7은 최대 3회, 8.8은 루프 밖에서 정확히 1회 실행한다.
> 상태·노트 경로는 상위 스킬이 전달한 실행별 절대 경로만 사용한다.

# Phase 8 — Quality loop

## Loop invariant

```text
for iteration in 1..3:
  Batch A: Sol High 8.1 command + Luna xHigh(read-only, parallel) 8.2+8.3 / 8.4
  Phase 8.5 (Terra single writer): collected issues를 한 역할이 통합 수정
  Batch B: Terra 8.6 E2E / 8.7 integration fix, Sol High command and judgment

after loop: Phase 8.8 isolated read-back exactly once
```

Batch A는 같은 기준 작업 트리를 읽으며 파일을 수정하지 않는다. 수정이 생겼다면 채택하지 않고 이슈
목록만 사용한다. Phase 8.5만 그 iteration의 작성자다.

## Phase 8.1: Build + test

`buildCommand`와 `testCommand` 중 존재하는 명령을 직접 실행하고 로그를 수집한다. TDD 활성 시
[tdd.md](tdd.md)의 baseline 대조 순서로 실패를 분류한다.

1. Test Map에 있는 실패 → `new_red`
2. baseline 동일 ID + 동일 signature → `pre_existing`
3. 동일 ID + 다른 signature → 재실행 후 `regression` 또는 `flaky`
4. baseline에 없는 ID → 재실행 후 `regression` 또는 `flaky`

수정 큐에는 `regression`, `new_red` 순서로 넣는다. `pre_existing`은 범위 밖으로 보고만 한다. TDD가
생략됐으면 분류 없이 전체 실패 로그를 전달한다.

## Phase 8.2 + 8.3: Simplify + Convention

`fork_turns:none`의 Luna xHigh 읽기 전용 스캐너가 두 절차를 순서대로 실행하되 결과와 상태를 분리한다.

1. 오케스트레이터가 `../../simplify-loop/SKILL.md`를 읽고 `--dry-run` 계약을 스캐너에 전달해 후보만 수집한다.
2. 오케스트레이터가 `../../convention-check/SKILL.md`를 읽고 검사 계약을 전달해 위반만 수집한다.

Simplify 구현은 Codex가 소유한 bounded state machine 계약을 따른다. 네 관점
Correctness/Readability/Performance/Stability, 만장일치 뒤 Devil's Advocate, Arbiter, 단일 작성자,
기존 상태 필드와 종료 코드(`DONE`, `BLOCKED:MAX_ITERATIONS`, `BLOCKED:NO_PROGRESS`,
`BLOCKED:REVIEW_INCOMPLETE`, `SKIPPED:NO_CHANGES`, `SKIPPED:BASE_REF_UNRESOLVED`, `FAIL`)를
보존한다. 별도 런타임 스크립트를 복제하거나 의존하지 않는다. Phase 8의 dry-run에서는 적용하지 않는다.

반환:

```text
simplify 후보: N건
- file:line, 현재 요약, 제안, 근거
convention 위반: M건
- file:line, 위반 규칙, 제안
```

오케스트레이터가 8.2와 8.3 결과를 각각 `Phase Results`에 기록한다.

## Phase 8.4: Scope review

[agents/scope-reviewer.md](agents/scope-reviewer.md)를 읽고 `fork_turns:none`의 Luna xHigh 역할에서 Technical Spec 기준의 누락/불일치만 받는다.
코드 스타일은 보지 않으며 파일을 수정하지 않는다. `EC-nn` ID를 보존한다.

## Phase 8.5: Integrated fix — single writer

Batch A 이슈가 하나라도 있으면 `fork_turns:none`의 Terra executor 한 수정 역할에 아래 순서로 전달한다.

1. build/test: `regression` → `new_red`
2. Scope 누락
3. Convention 위반
4. 안전한 Simplify 후보

TDD 활성 시 테스트 파일과 `pre_existing` 실패는 수정하지 않는다. 테스트 충돌은 `[TestConflict]`로
보고한다. 같은 파일의 여러 이슈는 한 번의 편집으로 합친다. Terra는 설계 결정·편차·트레이드오프·
을 구조화 결과로 반환하고, Sol High만 Implementation Notes에 append한다.
`buildCommand`가 있으면 수정 후 확인한다. 변경이 있으면 `modified = true`다.

## Phase 8.6: E2E test loop

profile의 `e2eEnabled`, `runServerCommand`, `serverUrl`이 모두 유효할 때만 Terra executor가 수행하고
PID/세션 핸들과 정리 결과를 Sol High에 반환한다. Sol High만 그 handle을 `{STATE_FILE}`에 기록한다. 그렇지 않으면
명확한 `SKIPPED:{사유}`를 기록하고 `modified`에는 영향을 주지 않는다.

Sol High가 형제 `../../e2e-test-loop/SKILL.md`와 그 skill-relative assets를 읽고, 해결된
절대 asset 경로와 계약을 같은 Terra executor에 전달한다. Terra는 중첩 agent spawn이나 직접 commit 없이
E2E와 실패 수정까지 같은 배정 안에서 수행하고 구조화 결과만 반환한다. asset 경로를
프로젝트 CWD나 plugin 전역 경로로 추측하지 않는다. 서버는 다음 생명주기 계약을 지킨다.

- Terra가 시작한 PID 또는 실행 세션 핸들과 정리 결과를 Sol High에 반환하고, Sol High가 `{STATE_FILE}`에 기록한다.
- readiness와 lock polling은 매 wait를 60초 미만으로 yield하되 profile/형제 절차의 총 timeout을
  줄이지 않는다.
- 성공, 테스트 실패, 수정 실패, 사용자 중단, 상위 Phase 중단을 포함한 모든 exit에서 자신이 시작한
  서버와 lock을 정리한다.
- 기존 서버를 재사용했다면 종료하지 않는다.

결과는 `이슈: N건, 수정: Y/N, 스킵 사유: ...`다. 수정 Y면 `modified = true`다.

## Phase 8.7: Integration test

`makeTestCommand`가 있으면 Sol High가 순차 실행한다. 없으면 `SKIPPED:PROFILE_EMPTY`다. 실패하면 Terra executor에게 8.5와 같은
single-writer 수정 계약으로 실패 로그만 전달하고 Sol High가 재실행한다. 수정이 있으면 `modified = true`다.

## Iteration 판정

TDD 활성 테스트 판정:

| 판정 | 조건 |
|------|------|
| `PASS` | `regression == 0` 및 `new_red == 0` |
| `WARN` | `flaky`만 존재 |
| `FAIL` | `regression > 0` 또는 `new_red > 0` |

| 종료 조건 | 결과 |
|----------|------|
| `modified == false` AND 테스트 `PASS` | 루프 종료 |
| TDD 생략 AND `modified == false` | 루프 종료 |
| 그 외 | 변경 커밋 후 다음 iteration |
| 3회 도달 및 미PASS | `BLOCKED:TEST_NOT_GREEN`, 이후 8.8 계속 |

Sol High가 조정하는 수정 커밋은 `Fix: 품질 루프 수정 (반복 N)`이며 실제 변경 파일만 stage한다.

# Phase 8.8 — Isolated Spec read-back

루프가 끝난 뒤 1회만 한다. 목적은 Spec을 모르는 역할이 구현/테스트가 실제로 보장하는 동작을 복원하게
한 뒤 오케스트레이터가 Spec과 대조하는 것이다.

## 입력 소스

1. base 대비 변경된 `testDirs` 테스트 파일
2. 없으면 8.6 E2E report
3. 없으면 변경된 handler/route의 공개 인터페이스

모두 없으면 `SKIPPED:NO_READBACK_SOURCE`다. 소스 종류를 보고한다. 3번은 구현 복원이므로 A(검증
누락)를 판정하지 않고 `A 판정 불가(소스=구현 코드)`로 적는다.

## Isolation contract

`fork_turns:none`의 Luna xHigh Read-back 역할에는 다음을 절대 전달하지 않는다.

- `{STATE_FILE}` 경로
- Spec, Plan, Edge Cases
- TDD Test Map
- 다른 Phase의 상태 갱신 지시

프롬프트에는 선정 소스의 절대 경로만 전달하고 그 파일과 직접 참조 코드만 읽게 한다. 파일을 수정하지
않고 assertion, 조건, 반환 코드가 실제로 보장하는 것만 아래 표로 반환한다.

```markdown
### 복원된 시나리오
| # | Given | When | Then | 출처 |
|---|-------|------|------|------|

### 해석 불가
- file:line — 이유

### 보장되지 않는 것
- 항목 또는 없음
```

이 역할이 두 번 실패하면 `SKIPPED:AGENT_DIED`이며 오케스트레이터가 대신 복원하지 않는다.

## Orchestrator diff

복원 결과를 오케스트레이터가 Spec/Edge Cases와 대조한다.

| 유형 | 의미 |
|------|------|
| A | Spec edge case가 복원본에 없음: 검증 누락 |
| B | 복원본 동작이 Spec에 없음: Spec 밖 |
| C | 같은 케이스 기대값 불일치 |
| D | 복원 역할이 해석 불가로 분리 |
| E | 복원 동작이 Spec의 참조 구현과 다름: 컨벤션 이탈 |

E는 참조 구현 `file:line`이 있는 행만 판정한다. B/D는 보고만 하고 판정 합계에서 제외한다.

| 판정 | 조건 |
|------|------|
| `PASS` | A+C+E = 0 |
| `WARN` | A+C+E = 1~2 |
| `FAIL` | A+C+E >= 3 |

Phase 8.8은 코드와 Spec을 수정하지 않는다. Diff를 상태에 기록하고 `FAIL`이어도 Phase 9로 진행해
Phase 12에서 사용자 결정을 받는다.
