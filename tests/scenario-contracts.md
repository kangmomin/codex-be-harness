# Workflow Scenario Contracts

아래 시나리오는 문구가 아니라 상태 전이와 부작용 경계를 검증한다.

| 시나리오 | 필수 관찰 결과 |
|---|---|
| profile 부재 | `init` 안내 후 구현·브랜치 변경 없이 종료 |
| custom profile 필수 필드 누락 | 누락 목록과 수정/중단 선택지를 제시 |
| `--analyze --verify` 동시 입력 | 하나를 선택하기 전 분석을 시작하지 않음 |
| fullstack 영향 발견 | Phase 3에서 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`, Phase 5 부작용 없음 |
| baseline 명령 실패 | 재시도/`--no-tdd`/중단 세 선택지를 제시 |
| Red 실행 | `red_assertion`, `already_satisfied`, `cannot_compile`, `deferred_e2e` 중 하나로 분류 |
| build 연속 실패 | 최대 3회 뒤 `BLOCKED:BUILD_FAIL` |
| quality issue 잔존 | 최대 3회 뒤 잔존 이슈와 함께 차단 |
| `[Assumption]` 잔존 | push/PR 없이 `BLOCKED:ASSUMPTION_UNRESOLVED` |
| `--reflect` 없음 | Phase 11 `SKIPPED:REFLECT_NOT_REQUESTED` |
| E2E 비활성/불가 | 사유가 있는 `SKIPPED:*`, 전체 build 실패로 오판하지 않음 |
| E2E 실행 | PASS/WARN/FAIL과 시나리오별 증거 보고 |
| simplify 수렴 | 변경 0건이면 DONE |
| simplify 10회 도달 | 잔존 이슈와 선택지를 포함한 BLOCKED |
| simplify no-progress | 같은 방향 수정 반복 시 조기 차단 |
| reviewer 일부 실패 | retry 상태를 유지하고 무검증 PASS 금지 |

## Clean-room smoke prompts

독립 검증 agent는 임시 Git 저장소와 가짜 profile을 사용한다. 원격 push와 PR은 수행하지 않는다.

1. `$codex-be-harness:start-workflow --analyze .` — Phase A 보고 계약만 평가한다.
2. `$codex-be-harness:start-workflow 결제 취소 API와 화면을 함께 변경해줘` — fullstack handoff를 평가한다.
3. `$codex-be-harness:simplify-loop` — 변경 없는 저장소에서 즉시 수렴하는지 평가한다.
