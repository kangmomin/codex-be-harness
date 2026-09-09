# Workflow Scenario Contracts

아래 시나리오는 문구가 아니라 상태 전이와 부작용 경계를 검증한다.

| 시나리오 | 필수 관찰 결과 |
|---|---|
| profile 부재 (프로젝트 루트·메인 워크트리 모두) | `PROFILE_MISSING` — `init` 안내 후 구현·브랜치 변경 없이 종료 |
| linked worktree에 profile 없음 + 메인 워크트리에 있음 | 메인 워크트리 profile 상속, `[Assumption] 메인 워크트리 profile 상속` 보고, 종료하지 않음 |
| Phase 1 중복 스캔 — 다른 worktree/open PR의 변경 파일이 Spec 대상과 교차 | 후보 목록 보고 후 `BLOCKED:DUPLICATE_IN_PROGRESS`, 스캔 전후 mutation 0 |
| Phase 1 중복 스캔 — 현재 브랜치/현재 PR만 매칭 | 차단하지 않음 |
| Phase 1 중복 스캔 — worktree·PR에 연결되지 않은 단독 로컬 브랜치만 매칭 | 차단하지 않음 |
| request 질문 기본값 승인 | 선택적 질문에 명시적 `skip`/"기본값으로 진행"이면 기본값 채택 + `[Assumption]` 표기. 미응답은 필수 결정·승인이 아님 |
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
| 세션 orchestrator | 현재 세션이 직접 orchestration, 별도 bootstrap/relay 없음; 하위 spawn만 `fork_turns:none` |
| Pre-flight 실패 | Phase 5 전이면 상태 파일·코드·git 효과 없이 중단 사유를 보고 |
| 고정 모델 미가용 | `model_unavailable(...)`은 진단에만 기록하고 타 모델로 조용히 대체하지 않음 |
| executor 사망 | Worker writer/external-effect가 두 번 실패하면 `BLOCKED:AGENT_DIED`, Orchestrator가 worktree/push를 대행하지 않음 |
| read-back 사망 | Phase 8.8 Readonly가 두 번 실패하면 `SKIPPED:AGENT_DIED`, orchestrator가 대체 복원하지 않음 |
| 상태 writer 경계 | Orchestrator만 `{STATE_FILE}`과 Phase Results를 쓰고 다른 역할은 구조화 결과만 반환 |
| Phase 4.3 advisor auto | UNKNOWN은 D floor 7; D 1~3은 `SKIPPED:ADVISOR_NOT_REQUIRED`, D 4~8은 xhigh, D≥9·동시성·데이터 정합성/이관·8+ 파일 설계·3 레이어·공유 구조는 각각 독립적으로 max; spawn에는 concrete effort만 전달 |
| Phase 4.3 경계 | D=3은 skip, D=4와 D=8은 xhigh, D=9는 max; UNKNOWN은 적어도 D=7이고 각 max 신호는 단독으로 max를 만든다 |
| Phase 4.3 fixed/rescore | fixed effort는 항상 실행하고 auto보다 우선; Phase 4.4 직전에는 최종 Plan·사용자 정정·승인 범위를 포함해 항상 재평가하고 minimum이 상승할 때만 Phase 4.3과 같은 light→standard 승격 순서와 유효 `{PLAN_MAX}`를 적용해 남은 다음 iteration을 소비하며, slot이 없으면 `BLOCKED:MAX_ITERATIONS`, 이미 높은 prior review는 재실행하지 않음 |
| Phase 4.3 advisor 사망 | Advisor가 두 번 사망하면 대체 모델 없이 `agent_died(...)` 진단과 `CODEX-UNAVAILABLE` 결과를 남기고 Phase 4.4로 진행 |
| Phase 12 remediation | 사용자 승인 remediation으로 diff가 바뀌면 Phase 10 Assumption Gate와 Phase 4.4 외부 효과 범위를 다시 확인 |
| E2E lifecycle | 같은 Worker가 중첩 spawn·직접 commit 없이 E2E와 실패 수정을 수행하고 PID/정리 결과를 반환하며 Orchestrator만 상태·commit을 조정 |
| config 전체 조회 | 조회만 수행하고 mutation 0 (profile·상태 파일·기타 파일 불변) |
| config 배치 수정 | 전건 검증 후 한 번의 치환 — 전건 `DONE` 또는 전건 미반영(부분 반영 없음) |
| config 상속 profile 수정 | linked worktree에서 메인 워크트리 profile을 수정하고 절대 경로 + `[Assumption] 메인 워크트리 profile 상속` 보고 |
| config 비지원 레이아웃 | 대상 키가 비지원 저장 형태면 `BLOCKED:UNSUPPORTED_LAYOUT`, 파일 바이트 불변 |
| config block 기존 무효 슬롯 | `topologyModels` 블록에 무효 슬롯이 남는 수정은 `BLOCKED:INVALID_PROFILE`·파일 불변; 입력이 그 슬롯을 덮어쓰거나 `{슬롯}=default`로 삭제하면 진행 |
| 락 acquire exit 1 (락 디렉토리 mkdir 비-EEXIST 실패 포함 — 대기 없음) | e2e-test는 `BLOCKED:LOCK_UNAVAILABLE`·서버 미기동 → e2e-test-loop는 즉시 종료·렌더링 생략·`E2E 리포트: 없음 (BLOCKED:LOCK_UNAVAILABLE)` → quality-loop 8.6 행 기록·루프 계속 → Phase 10 Gate 보류·3택(락 재시도 / E2E 없이 진행 / 중단) |
| `## Test Baseline` 완전성 | 헤더 1개 + (`수집 실패 — regression 판정 불가` 줄 1개(있으면 행 유무 무관 완료·우선; SKIP 줄과 공존은 불완전) 또는 SKIP 줄 1개 또는 스위트별 6셀 baseline 행 1개), 불완전하면 Implementation Notes 템플릿 헤더 확인 후 재수집·교체 |
| Phase 10 Gate 락 재시도 | 승격 ⑥ 미적용, `수정: N` ∧ DONE/WARN만 즉시 복귀, `수정: Y`이면 Phase 7 → 새 standard Phase 8 루프 → Phase 9 재판정 → Phase 10 |
| light 판정과 축소 | A ≤ 3 ∧ B ≤ 3 ∧ 금지 조건 0 ∧ TDD 활성 ∧ ≠ parallel-slices ∧ `--tier standard` 없음 → 4.2 Readonly 1역할·`{PLAN_MAX}` 2·`{QL_MAX}` 2·8.2 `SKIPPED:TIER_LIGHT`·8.6 `--smoke`·8.8 `SKIPPED:TIER_LIGHT` |
| 승격 latch | 루프 종료·상한 평가보다 먼저 적용, 단방향, 카운터 단조 증가; Phase 8 재진입(⑦·락 재시도 후 수정)만 새 루프 |
| `--smoke` 무효화 | 실효 full latch·`{MAX_ITER}` 5·`실행 수준: full(smoke 미적용)` |
| 렌더러·아카이버 exit ≠ 0 | 실제 stdout·원문·JSON 경로와 오류를 보존. 아카이버 실패 시 cp/cat/replace 폴백 금지 |
| 렌더러 실패 | `{RUN_DIR}`와 원문을 보존하고 생성되지 않은 리포트를 성공 경로로 보고하지 않음·루프 판정 불변 |
| `## Flags`와 CLI 인자 충돌 | `## Flags`가 우선하며 기록값 사용 + 충돌 고지 |
| 상태 파일 스키마 불일치(Build) | `## Flags` 부재·필수 키 누락·`## Profile Snapshot`/`## Verification Tier` 누락 시 `BLOCKED:STATE_SCHEMA_MISMATCH`; Build는 concrete advisor N/A 또는 effort와 Phase 4.3의 유효 Assignment status만 저장하고 raw unavailable/interrupted는 Plan log에 보존; Analyze/Verify 신규는 `executor=N/A,advisor=N/A`, legacy concrete advisor는 unused로 보존하며 resolve·availability 검사·spawn하지 않음 |
| Build 재개·형제 스킬 profile 해석 | `## Profile Snapshot`만 사용하며 config로 profile이 바뀌어도 실행 중 값 불변 |
| 상태 파일 생성 이전 중단 | Pre-flight 재시작 |
| Verify profile 변경 후 재개 | verify-commands.json의 원래 명령 4종 복원; 누락·다른 RUN·중복 키는 원본 보존 후 차단 |
| 토폴로지 슬롯 설정 적용 | profile `topologyModels`/`--topology-models`의 유효 슬롯은 해당 역할 spawn의 model/effort로 쓰이고 `## Flags` `TOPOLOGY_MODELS`·Phase Assignments에 확정값으로 기록, 라벨은 불변 |
| 무효 슬롯 | profile 무효 슬롯 → 그 슬롯만 기본값 + 경고(profile 불변, doctor `INVALID_SLOT`); 플래그 무효 → 대화형 재입력 1회 / 비대화형 무시 + 경고 |
| 설정 model/effort 거부 | `model_unavailable({슬롯}:{사유})` 진단 + 해당 Phase 기존 계약, 대체·강등 재시도 없음; orchestrator override는 경고 후 현재 세션 유지 |
| 플래그 ephemeral | `--topology-models`는 profile을 바꾸지 않으며 다음 실행에 남지 않음 |
| `SCHEMA: 2/3` Build 재개 | 자동 변환·원본 교체 없이 `BLOCKED:STATE_SCHEMA_MISMATCH`; 현재 SCHEMA:4 계약 필요 |

## Clean-room smoke prompts

독립 검증 agent는 임시 Git 저장소와 가짜 profile을 사용한다. 원격 push와 PR은 수행하지 않는다.

1. `$codex-be-harness:start-workflow --analyze .` — Phase A 보고 계약만 평가한다.
2. `$codex-be-harness:start-workflow 결제 취소 API와 화면을 함께 변경해줘` — fullstack handoff를 평가한다.
3. `$codex-be-harness:simplify-loop` — 변경 없는 저장소에서 즉시 수렴하는지 평가한다.
4. linked worktree(`git worktree add`)에서 `$codex-be-harness:start-workflow --analyze .` — 메인 워크트리 profile 상속 보고를 평가한다.
5. 다른 worktree에 같은 파일을 만지는 브랜치를 둔 뒤 `$codex-be-harness:start-workflow {같은 기능}` — Phase 1 `BLOCKED:DUPLICATE_IN_PROGRESS`와 mutation 0을 평가한다.

## 공통 실행 원칙 검토 시나리오

프롬프트 변경을 검토할 때 아래 입력과 기대 동작을 대조한다. 이 표는 자동화된 모델 실행 테스트 결과가 아니다.

| 입력·상황 | 기대 동작 |
|---|---|
| 요청 유형·문서 포맷·범위가 이전 대화에 이미 있음 | 같은 값을 다시 질문하지 않고 산출물을 완성 |
| 확정 Spec/Plan·효과를 승인한 사용자의 후속 입력을 fresh-context orchestrator에 전달 | 승인 근거 원문과 최신 지시를 재사용; 같은 승인 재요청 없음 |
| “끝까지 진행”만 있고 Phase 4.4의 구체적 Plan·효과는 미승인 | 현재 planning-only 범위의 준비를 마친 뒤 구체적인 실행 승인; Phase 5 편집 없음 |
| 로컬 작업만 승인됐는데 draft PR 또는 파괴적 변경이 새로 필요 | 허용된 준비를 완료하고 추가 효과의 승인 대기; 원격 반영·파괴적 변경 없음 |
| 스킬/override의 문구 때문에 중단 | 실제 읽은 파일 링크·문구·적용 이유와 명시 요구/해석 구분을 보고 |
| spec-only·Analyze/Verify·읽기 전용 역할에서 자율 완료 지침을 읽음 | 지정 산출물만 반환; 구현·다음 Phase로 임의 확대 없음 |
| Phase 8.8 격리 Read-back | 공통 envelope·승인 원문·Spec/Plan을 주입하지 않고 기존 소스만 전달 |
| 낮은 영향의 문서 수정, 필수 검사 통과, 새 변경·실패 없음 | 구현을 복제하는 테스트나 추가 반복 없이 완료; 필수 검증 생략 없음 |
| 진행 중 사용자가 상태 질문 또는 정정 전달 | 짧게 답하거나 정정을 반영하고 같은 작업 계속; 새 RUN을 만들지 않음 |
| upstream이 새 확인 단계·모델/도구 지시를 추가 | 공식 가이드와 계약으로 채택/변환/제외/보류 판정; 근거 기록; 무조건 복사·모델 교체 없음 |
| 새 worktree로 이슈/파일 정정과 승인된 작업 인계 | 정확한 대소문자·브랜치·식별자·최신 결정·미완료와 승인 근거 전달; 이전 CWD의 RUN을 강제 재사용하지 않음 |
| 현재 설계와 과거 기록·코드·테스트가 충돌 | 현재 요구·설계와 실제 동작의 차이를 드러내고 업무 의미의 미결만 질문; 과거 기록을 정본으로 승격하지 않음 |
| 권한 Spec AC/EC가 있고 관리자 토큰만 있는 smoke E2E | 일반/미인증/권한 없음/다른 소유자 각각 대조; 역할 증거 부족은 UNCOVERED, 관리자 성공으로 대체하지 않음; Spec EC 생략 없음 |
| 테스트 기대값이 현재 설계와 다르고 Green writer는 테스트 수정 금지 | 테스트 오류와 구현 오류를 구분해 TestConflict/기존 승인으로 처리; 통과 목적 기대값 완화·삭제 없음 |
| 사용자가 timeout을 의심하나 응답은 빠르고 전체 데이터 존재 | 지지·반박 근거와 대안 조사; 마스킹한 환경·재현·기대/실제만 인계·보고에 기록 |
| 모든 검증 통과 후 승인된 수정이 tree를 변경 | 새 tree의 관련 필수 검증 수행; 통과 뒤 새 근거 없는 추가 반복은 종료하고 미검증·미해결을 숨기지 않음 |

| 모델 추천 최신화 | 명시 요청 때만 refresh-models; 일반 실행은 offline resolve, 명시 profile override 보존 |
| 모델 추천 default | 플래그 default는 profile을 무시하고 추천, config default는 profile 슬롯 삭제 |
| 추천표 갱신 후 재개 | 기존 하위 배정과 advisor 결정을 재사용, 새 추천표 미조회 |
| 모델 최신 근거 부족 | 공식 근거·호스트 모델/effort 미확인 시 기존 파일 보존 |
