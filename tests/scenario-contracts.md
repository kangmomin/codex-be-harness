# Workflow Scenario Contracts

아래 시나리오는 문구가 아니라 상태 전이와 부작용 경계를 검증한다.

| 시나리오 | 필수 관찰 결과 |
|---|---|
| profile 부재 (프로젝트 루트·메인 워크트리 모두) | `PROFILE_MISSING` — `init` 안내 후 구현·브랜치 변경 없이 종료 |
| linked worktree에 profile 없음 + 메인 워크트리에 있음 | 메인 워크트리 profile 상속, `[Assumption] 메인 워크트리 profile 상속` 보고, 종료하지 않음 |
| Phase 1 중복 스캔 — 다른 worktree/open PR의 변경 파일이 Spec 대상과 교차 | 후보 목록 보고 후 `BLOCKED:DUPLICATE_IN_PROGRESS`, 스캔 전후 mutation 0 |
| Phase 1 중복 스캔 — 현재 브랜치/현재 PR만 매칭 | 차단하지 않음 |
| Phase 1 중복 스캔 — worktree·PR에 연결되지 않은 단독 로컬 브랜치만 매칭 | 차단하지 않음 |
| request 질문 기본값 승인 | 빈 응답/`skip`/"기본값으로 진행"이면 기본값 채택 + `[Assumption]` 표기 |
| workflow 내부 E2E 인증 부재 | `mode: workflow`면 사용자 질문 없이 `SKIPPED:NO_AUTH` |
| Phase 12 보고 | `{REPORT_DIR}`에 `*-workflow-report.md` 아카이브 1개(부록 A/B/C) — HTML 없음 |
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
| topology bootstrap | entry agent가 `fork_turns:none` Sol High를 한 번만 만들고 marker/hop limit으로 재귀 spawn을 막음 |
| bootstrap 실패 | Phase 5 전이면 상태 파일·코드·git 효과 없이 중단 사유를 보고 |
| 고정 모델 미가용 | `model_unavailable(...)`은 진단에만 기록하고 타 모델로 조용히 대체하지 않음 |
| executor 사망 | Terra writer/external-effect가 두 번 실패하면 `BLOCKED:AGENT_DIED`, Sol High가 worktree/push를 대행하지 않음 |
| read-back 사망 | Phase 8.8 Luna가 두 번 실패하면 `SKIPPED:AGENT_DIED`, orchestrator가 대체 복원하지 않음 |
| 상태 writer 경계 | Sol High만 `{STATE_FILE}`과 Phase Results를 쓰고 다른 역할은 구조화 결과만 반환 |
| Phase 4.3 | 매 iteration 새 `fork_turns:none` Sol Max context이며 최대 5회와 Phase 4.4 승인 Gate를 유지 |
| Phase 4.3 advisor 사망 | Sol Max가 두 번 사망하면 대체 모델 없이 `agent_died(...)` 진단과 `CODEX-UNAVAILABLE` 결과를 남기고 Phase 4.4로 진행 |
| Phase 12 remediation | 사용자 승인 remediation으로 diff가 바뀌면 Phase 10 Assumption Gate와 Phase 4.4 외부 효과 범위를 다시 확인 |
| E2E lifecycle | 같은 Terra가 중첩 spawn·직접 commit 없이 E2E와 실패 수정을 수행하고 PID/정리 결과를 반환하며 Sol High만 상태·commit을 조정 |
| config 전체 조회 | 조회만 수행하고 mutation 0 (profile·상태 파일·기타 파일 불변) |
| config 배치 수정 | 전건 검증 후 한 번의 치환 — 전건 `DONE` 또는 전건 미반영(부분 반영 없음) |
| config 상속 profile 수정 | linked worktree에서 메인 워크트리 profile을 수정하고 절대 경로 + `[Assumption] 메인 워크트리 profile 상속` 보고 |
| config 비지원 레이아웃 | 대상 키가 비지원 저장 형태면 `BLOCKED:UNSUPPORTED_LAYOUT`, 파일 바이트 불변 |
| 락 acquire exit 1 | e2e-test는 `BLOCKED:LOCK_UNAVAILABLE`·서버 미기동 → e2e-test-loop는 즉시 종료·렌더링 생략·`E2E 리포트: 없음 (BLOCKED:LOCK_UNAVAILABLE)` → quality-loop 8.6 행 기록·루프 계속 → Phase 10 Gate 보류·3택(락 재시도 / E2E 없이 진행 / 중단) |
| `## Test Baseline` 완전성 | 헤더 1개 + (`수집 실패 — regression 판정 불가` 줄 1개(있으면 행 유무 무관 완료·우선; SKIP 줄과 공존은 불완전) 또는 SKIP 줄 1개 또는 스위트별 6셀 baseline 행 1개), 불완전하면 Implementation Notes 템플릿 헤더 확인 후 재수집·교체 |
| Phase 10 Gate 락 재시도 | 승격 ⑥ 미적용, `수정: N` ∧ DONE/WARN만 즉시 복귀, `수정: Y`이면 Phase 7 → 새 standard Phase 8 루프 → Phase 9 재판정 → Phase 10 |
| light 판정과 축소 | A ≤ 3 ∧ B ≤ 3 ∧ 금지 조건 0 ∧ TDD 활성 ∧ ≠ parallel-slices ∧ `--tier standard` 없음 → 4.2 Luna 1역할·`{PLAN_MAX}` 2·`{QL_MAX}` 2·8.2 `SKIPPED:TIER_LIGHT`·8.6 `--smoke`·8.8 `SKIPPED:TIER_LIGHT` |
| 승격 latch | 루프 종료·상한 평가보다 먼저 적용, 단방향, 카운터 단조 증가; Phase 8 재진입(⑦·락 재시도 후 수정)만 새 루프 |
| `--smoke` 무효화 | 실효 full latch·`{MAX_ITER}` 5·`실행 수준: full(smoke 미적용)` |
| 렌더러·아카이버 exit ≠ 0 | 폴백 + `script_fallback`, stdout `경로:`/`상태:`를 그대로 기록 |
| 렌더러·폴백 모두 실패 | `{RUN_DIR}` 보존·리포트 없음 보고·루프 판정 불변 |
| `## Flags`와 CLI 인자 충돌 | `## Flags`가 우선하며 기록값 사용 + 충돌 고지 |
| 상태 파일 스키마 불일치 | `## Flags` 부재·필수 키 누락·`## Profile Snapshot`/`## Verification Tier` 누락 시 `BLOCKED:STATE_SCHEMA_MISMATCH` |
| 재개·형제 스킬 profile 해석 | `## Profile Snapshot`만 사용하며 config로 profile이 바뀌어도 실행 중 값 불변 |
| 상태 파일 생성 이전 중단 | Pre-flight 재시작 |
| 토폴로지 슬롯 설정 적용 | profile `topologyModels`/`--topology-models`의 유효 슬롯은 해당 역할 spawn의 model/effort로 쓰이고 `## Flags` `TOPOLOGY_MODELS`·Phase Assignments에 확정값으로 기록, 라벨은 불변 |
| 무효 슬롯 | profile 무효 슬롯 → 그 슬롯만 기본값 + 경고(profile 불변, doctor `INVALID_SLOT`); 플래그 무효 → 대화형 재입력 1회 / 비대화형 무시 + 경고 |
| 설정 model/effort 거부 | `model_unavailable({슬롯}:{사유})` 진단 + 해당 Phase 기존 계약, 대체·강등 재시도 없음; orchestrator 슬롯이면 상태 파일 없이 bootstrap 실패 보고 |
| 플래그 ephemeral | `--topology-models`는 profile을 바꾸지 않으며 다음 실행에 남지 않음 |
| `SCHEMA: 2` 재개 | 0.4.0 상태 파일은 `TOPOLOGY_MODELS`·`topologyModels` 기본값 보완 + `SCHEMA: 3`으로 임시 파일 원자 교체 후 재개; 난이도 기록 없으면 `BLOCKED:STATE_SCHEMA_MISMATCH` |

## Clean-room smoke prompts

독립 검증 agent는 임시 Git 저장소와 가짜 profile을 사용한다. 원격 push와 PR은 수행하지 않는다.

1. `$codex-be-harness:start-workflow --analyze .` — Phase A 보고 계약만 평가한다.
2. `$codex-be-harness:start-workflow 결제 취소 API와 화면을 함께 변경해줘` — fullstack handoff를 평가한다.
3. `$codex-be-harness:simplify-loop` — 변경 없는 저장소에서 즉시 수렴하는지 평가한다.
4. linked worktree(`git worktree add`)에서 `$codex-be-harness:start-workflow --analyze .` — 메인 워크트리 profile 상속 보고를 평가한다.
5. 다른 worktree에 같은 파일을 만지는 브랜치를 둔 뒤 `$codex-be-harness:start-workflow {같은 기능}` — Phase 1 `BLOCKED:DUPLICATE_IN_PROGRESS`와 mutation 0을 평가한다.
