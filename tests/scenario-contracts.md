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
| Phase 12 보고 | `{REPORT_DIR}`에 `*-impl-notes.html`과 `*-workflow-report.md` 둘 다 존재 |
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

## Clean-room smoke prompts

독립 검증 agent는 임시 Git 저장소와 가짜 profile을 사용한다. 원격 push와 PR은 수행하지 않는다.

1. `$codex-be-harness:start-workflow --analyze .` — Phase A 보고 계약만 평가한다.
2. `$codex-be-harness:start-workflow 결제 취소 API와 화면을 함께 변경해줘` — fullstack handoff를 평가한다.
3. `$codex-be-harness:simplify-loop` — 변경 없는 저장소에서 즉시 수렴하는지 평가한다.
4. linked worktree(`git worktree add`)에서 `$codex-be-harness:start-workflow --analyze .` — 메인 워크트리 profile 상속 보고를 평가한다.
5. 다른 worktree에 같은 파일을 만지는 브랜치를 둔 뒤 `$codex-be-harness:start-workflow {같은 기능}` — Phase 1 `BLOCKED:DUPLICATE_IN_PROGRESS`와 mutation 0을 평가한다.
