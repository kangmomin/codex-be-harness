# Compatibility Contract

## 기준

- upstream: `kangmomin/harness-plugins`
- 전체 동기화 기준: `f9ce681427ccfbfd9194d3c3f204a445ae6f45dd` + 당시 미커밋 작업 트리 (파일별 실제 입력 해시는 UPSTREAM-SYNC.json)
- 2026-09-08 선택 반영: `80366fe4e83210368a9f3015fed73d1fbdafb878`의 AI 활용성 개선 커밋. `UPSTREAM-SYNC.json`의 `selective_updates`와 해당 파일의 `source_head`가 이 부분의 출처다. 전체 동기화 기준과 나머지 파일의 출처는 보존한다.
- 검증 개선 입력(2026-09-08): source `ae6900e4504a594bd6b9124043a59b7350ee33e8`에 커밋된 R1~R8. 해당 선택 기록은 `source_state:committed`와 실제 파일 해시를 사용한다. source plugin은 `be-harness@1.5.6`·`common@0.14.4`다.
- 전체 동기화 source plugin: `be-harness@1.5.4`; inlined common `common@0.14.2`
- 2026-09-08 선택 반영 source plugin: `be-harness@1.5.5`; `common@0.14.3`
- target plugin: `codex-be-harness@0.6.3`

호환성은 문장 일치가 아니라 관찰 가능한 workflow 동작을 기준으로 한다. Phase 순서, 승인·차단 게이트, 상태 코드, 루프 상한, 보고서 머리글을 invariant로 본다.

## 선택적 동기화 기준

Claude용 upstream을 동기화할 때는 [OpenAI 모델 가이드](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)의 현재 본문을 먼저 확인한다. 모델 가이드는 Codex의 행동 지침을 조정하는 근거이며, upstream 기능 명세나 이 저장소의 호환성 계약을 대신하지 않는다. 문서 접근이 불가하면 마지막 확인일과 미확인 범위를 기록하고 최신 권고를 확인했다고 보고하지 않는다.

1. `UPSTREAM-SYNC.json`의 source HEAD·파일 해시와 비교해 새 변경의 목적·관찰 가능한 효과를 파악한다. 미커밋 입력 포함 여부와 동기화 범위를 명시한다.
2. 아래 기준으로 각 변경을 판정한다. 계약에 필요한 변경을 단순히 “핵심 아님”으로 생략하지 않는다. 계약 변경이 필요하면 별도 근거와 영향·검증을 이 문서에 기록한다.
3. 프롬프트는 필요한 결정 기준만 남기고 공통 규칙은 한 곳에 둔다. 단독 스킬과 fresh-context 위임까지 읽기 경로를 연결하고, 기존 승인 재요청·사용자 지시와 충돌하는 파일 규칙·불필요한 테스트 반복을 점검한다.
4. `SYNC-REPORT.md`에 공식 가이드 URL·확인일, 변경별 채택/변환/제외/보류와 이유·적용 파일·검증 결과를 기록한다. 로컬 지침만 수정할 때는 기존 source 정보를 보존하고 변경된 매핑 파일의 target 해시만 갱신한다. 새 upstream 입력을 채택하면 실제 source HEAD·파일 해시와 적용 결과의 target 해시를 함께 기록한다. 로컬 전용 지침에 upstream 출처를 만들어 붙이지 않는다.
5. `AGENTS.md`의 필수 검증을 완료한다. 상태 전이·원격 효과·writer 격리·독립 리뷰·재개 동작은 [시나리오 계약](tests/scenario-contracts.md)과 대조한다. 정적 검사와 실제 실행 결과를 구분한다.

| 판정 | 가져올 내용과 처리 |
|---|---|
| 채택 | BE 기능·버그 수정, 데이터/상태 계약, 실패 보존, 검증 근거 등 관찰 가능한 품질에 필요한 변경. 호스트 중립 helper는 의존성과 호출 계약을 확인한 뒤 재사용 |
| 변환 | 도구 호출·경로·모델 배정·세션 관리처럼 호스트에 종속된 구현. Codex 도구, profile, topology, writer 계약에 맞게 변환 |
| 제외 | 중복 설명, 구체적 실패 근거 없이 늘어난 확인·위임·검증 단계, 기존 제품 범위 밖 기능. 이유를 기록하고 원문 전체나 모델 가이드를 복사하지 않음 |
| 보류 | 필요한 호스트 기능·입력이 없거나 계약 영향을 확인하지 못한 변경. 누락 영향과 해소 조건을 기록하고 동기화 완료로 보고하지 않음 |

가이드의 API 기능(async tool calling, configuration update 등)은 호스트 지원을 확인해야 한다. Markdown 지침만 추가하고 지원했다고 주장하지 않는다. 모델·effort 기본값을 자동 교체하지 않으며, 역할·비용 구조를 유지하고 교체 요청은 `topologyModels`/`--topology-models` 경로로 다룬다.

### AI 활용성 피드백의 Astra 적용 (2026-09-08)

근거는 `work-log:정리된 문서/AI 활용성/20260907-AI 활용성 리뷰.md` §6~7과 당일 확인한 공식 GPT-6 Astra prompting 가이드다. 요청에 맞춰 행동 기준을 조정했으며 모델 슬롯 교체는 하지 않았다.

| 피드백 | Codex 적용과 경계 |
|---|---|
| 완료·승인 범위를 시작에 확정 | 기존 Spec에 짧은 작업 계약을 추가하고 Phase 4.4는 동일 Spec·Plan·대상·효과의 승인 근거부터 확인. 미승인 차이만 질문하며 planning-only·원격 승인 Gate 유지 |
| 검증 반복·종료 근거 | 공통 execution-policy와 quality-loop에서 검사 범위·결함 기준·완료 증거 및 추가 검토 가설을 연결. 필수 Phase·티어 승격·상한·미해결 상태 보존 |
| 인계 시 대상 고정 | bootstrap·일반 envelope에 정확한 식별자·최신 기준·완료 증거·미결을 전달. 상태의 Spec/Context/Scope를 재사용하며 새 worktree의 RUN 검증과 Read-back 소스 격리 유지 |
| 선례·테스트·권한 | 현재 요구·설계 문서를 기대 동작 근거로 삼고 적합한 선례를 선택. 테스트 오류는 TestConflict/단일 writer 계약으로 처리. AC/EC별 역할 증거·UNCOVERED와 smoke 규칙 유지 |
| 로그·사용자 가설 | 재현 요약·발췌 마스킹·지지/반박 근거를 기록. 읽기 전용 역할은 부족한 측정을 반환하고 실행 권한을 확대하지 않음 |

Claude의 새 정책 파일은 복제하지 않고 기존 Codex [공통 실행 원칙](skills/start-workflow/references/execution-policy.md)에 필요한 결정 기준만 합쳤다. 이 파일과 topology/build-phases는 계속 로컬 전용이다. 기존 모델·effort 역할, host 도구, 상태 스키마·출력 머리글을 유지하며 별도 승인·검증 단계를 추가하지 않는다. 문구 검사와 모델 행동 검토 및 실제 테스트 실행 결과는 SYNC-REPORT에서 구분한다.

### 기본 high + 선택 advisor (0.6.3, 2026-09-08)

기본 executor는 `high`이며, 명시적 legacy executor `tiered`만 D 1~8 high / D 9~10 max로 유지한다. advisor 기본은
auto `tiered`다. Phase 4.2 뒤 UNKNOWN을 D floor 7로 처리해 D 1~3은 `SKIPPED:ADVISOR_NOT_REQUIRED`, D 4~8은 xhigh,
D≥9 또는 동시성·데이터 정합성/이관·8+ 파일 설계·3 레이어·공유 구조 신호는 각각 max로 resolve한다. fixed advisor effort는
항상 우선하며 symbolic `tiered`·`N/A`를 spawn하지 않는다. Phase 4.4 직전 재평가의 최소 effort 상승만 기존 iteration을 소비하고,
상한·상태 코드·Phase 순서를 보존한다. Build는 concrete advisor와 유효 Assignment status를 기록하고 raw unavailable/interrupted는
Plan log에 보존한다. 신규 Analyze/Verify는 `executor=N/A,advisor=N/A`이며 legacy advisor 기록도 unused로 보존한다.

### 검증 신뢰성과 재개 개선 (0.6.2, 2026-09-08)

| 계약 | 현재 동작과 호환성 경계 |
|---|---|
| 실제 내용 지문 v2 | HEAD/index/비무시 untracked에서 찾은 실제 파일의 경로·타입·내용·실행 비트·symlink 대상을 해시한다. textconv와 index 최적화 플래그는 변경을 숨기지 못한다. 초기화된 submodule의 HEAD·내용을 포함하고, 불완전 submodule·부모 symlink·특수 파일·unmerged index는 오류로 처리한다. ignored 파일이나 저장소 밖 입력 전체를 보장하는 지문은 아니다. |
| 커밋 후 재사용 | v2 내용이 같고 HEAD 비의존인 검증만 재사용한다. HEAD 의존 여부가 미확인이면 `--include-head`로 기록한다. 과거 이벤트는 보존하고, legacy 지문을 v2로 자동 변환하지 않는다. 기존 결과는 읽을 수 있지만 현재 v2와 대조하려면 새 검증이 필요하다. |
| 통합 테스트 결과 | 결과 schema 1에 `integration` kind와 regression_count를 추가했다. BE Phase 8.7 baseline 비교, 두 suite의 latest 합산, archive, 필수 검증 목록이 함께 소비한다. 이전 reader는 새 kind를 해석하지 못하므로 helper와 소비자를 같이 배포한다. TDD 생략은 실제 실패를 성공으로 바꾸지 않는다. |
| 태그 리터럴 | 오케스트레이터가 검토한 경로·줄·원래 줄 바이트 해시·이유가 정확히 맞는 경우만 선택적으로 제외한다. 기본 검사는 그대로 엄격하며, commit message나 파일 전체 예외는 없다. 실제 미해결 사항은 기존 사용자 결정 대상이다. |
| 테스트 후보 | 같은 Go 패키지와 지정 testDirs의 후보를 `candidate`로 반환한다. 후보 발견이나 파일명 대응만으로 관련 커버리지·light 자격을 인정하지 않는다. |
| Verify 재개 | 명령 4종과 CWD·RUN_ID·profile 출처를 한 번 저장하고 resume helper가 검증한다. live profile 변경·삭제와 무관하게 저장 명령을 사용한다. 스냅샷이 없는 구 Verify 실행은 원본을 보존하고 차단하며 새 실행이 필요하다. Build 전체 Snapshot과 Analyze 계약은 추가하지 않는다. |
| 포트 검증 | Codex 전용 `scripts/verify.sh`가 구조 검사·Python unittest·Node renderer를 실행하고 실패를 전달한다. source 저장소는 기존 전체 runner와 FE lock 정상화를 사용한다. |

공통 helper는 BE/FE/common과 같은 바이트를 사용하고, Phase 실행·경로·writer 지침만 Codex 호스트에 맞게 변환했다. 기존 모델 배정·승인 범위·루프 상한·Read-back 격리와 실패 이력 보존은 유지한다. 전체 source 동기화로 보고하지 않으며 선택한 변경과 로컬 전용 파일을 UPSTREAM-SYNC.json에 구분했다.

### 이식 이력 (아래 과거 릴리스 계약은 이후 변경으로 대체될 수 있음)

| upstream 버전 | 핵심 변경 | 포팅 상태 | 포팅 버전 |
|---|---|---|---|
| 1.2.0 | start-workflow 검증 티어·성찰 opt-in·md 리포트·결정적 단계 스크립트화 | 이식 — 0.4.0(`--reflect` opt-in은 0.2.0에 선반영) | 0.4.0 |
| 1.3.0 | start-workflow Codex 사용 모드 codexMode(none/mix/max)·Claude 패널 폴백 | N/A — 포팅은 고정 토폴로지(대체 금지) | — |
| 1.4.0 | Codex 위임 모델 슬롯화(codexModels)·provider/슬롯 범위 폴백 | 이식 — 0.5.0: `topologyModels` 슬롯 설정 + `--topology-models`(레코드 `{model, effort?}`; provider 전환은 Codex spawn 제약으로 미지원 — 에이전트 config 레이어의 `model_provider`가 무시됨을 실증(T3/T4)) | 0.5.0 |
| 1.5.0 | config 스킬 — profile 값 조회·수정 | 이식 — 0.3.0 | 0.3.0 |
| 1.5.1 | e2e-lock.sh 비-EEXIST 실패 즉시 종료·렌더러 `--level full-command` 제거 | 이식 — 0.5.1 | 0.5.1 |

## Source inventory mapping

### Skills

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `be-harness/skills/start-workflow/**` | `skills/start-workflow/**` | Codex planning gate와 subagent prompt로 변환 | Build Phase 1~12, Analyze A1~A4, Verify V1~V5 유지 |
| `be-harness/skills/request/**` | `skills/request/**` | 구조화 입력 fallback, 내부 `spec-only` 경계 | Spec·엣지 케이스·추적 ID 형식 유지 |
| `be-harness/skills/unit-test/**` | `skills/unit-test/**` | Codex 파일/명령 실행 표현 | Red 분류와 테스트 상한 유지 |
| `be-harness/skills/simplify-loop/**` | `skills/simplify-loop/**` | Workflow JS를 prompt/state machine으로 교체 | 최대 10회, 네 관점, DA→arbiter→writer와 종료 코드 유지 |
| `be-harness/skills/convention-check/**` | `skills/convention-check/**` | AGENTS/profile 경로 변환 | 검사 관점과 PASS/WARN/FAIL 유지 |
| `be-harness/skills/default-conventions/**` | `skills/default-conventions/**` | provider-neutral 호출 | 레이어·에러·트랜잭션 기본 규칙 유지 |
| `be-harness/skills/e2e-test/**` | `skills/e2e-test/**` | skill-relative asset, PTY/PID 정리, bounded polling | lock·server·시나리오·판정 계약 유지 |
| `be-harness/skills/e2e-test-loop/**` | `skills/e2e-test-loop/**` | Codex subagent 수정 loop | 최대 5회와 no-progress 차단 유지 |
| `be-harness/skills/init/**` | `skills/init/**` | `.codex` profile/override 생성 | preset과 non-destructive update 유지 |
| `be-harness/skills/doctor/**` | `skills/doctor/**` | Codex 경로·tool 진단 | 필수/선택 진단 분류 유지 |
| `be-harness/skills/config/**` | `skills/config/**` | `{PROFILE_PATH}` 해석·구조화 입력 fallback·frontmatter 1회 치환 | 조회/배치 수정 모드·상태 코드·키 parity 유지 |

### Agents

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `be-harness/agents/code-analyzer.md` | `skills/start-workflow/references/agents/code-analyzer.md` | read-only subagent prompt | Analyze 관점과 보고 형식 유지 |
| `be-harness/agents/code-verifier.md` | `skills/start-workflow/references/agents/code-verifier.md` | read-only subagent prompt | Verify 기준과 판정 유지 |
| `be-harness/agents/edge-case-analyzer.md` | `skills/request/references/edge-case-analyzer.md` | request 내부 분석 prompt | 다관점 edge-case 질문/출력 유지 |
| `be-harness/agents/scope-reviewer.md` | `skills/start-workflow/references/agents/scope-reviewer.md` | read-only subagent prompt | Spec-only scope 검증 유지 |
| `be-harness/agents/workflow-implementer.md` | `skills/start-workflow/references/agents/workflow-implementer.md` | writer subagent prompt | Plan/TDD 제약과 결과 보고 유지 |
| `be-harness/agents/workflow-pr.md` | `skills/start-workflow/references/agents/workflow-pr.md` | commit/PR skill orchestration prompt | Assumption Gate와 PR 결과 유지 |
| `be-harness/agents/workflow-reflection.md` | `skills/start-workflow/references/agents/workflow-reflection.md` | read-only reflection prompt | 회고 항목과 override 제안 유지 |

### References and assets

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `start-workflow/references/agent-prompts.md` | same relative target | Codex spawn/death semantics | Phase assignment 유지 |
| `start-workflow/references/analyze-verify-modes.md` | same relative target | sibling procedures와 subagent prompt 사용 | A/V phase 유지 |
| `start-workflow/references/quality-loop.md` | same relative target | bounded Codex subagents | Phase 8.1~8.7 유지 |
| `start-workflow/references/tdd.md` | same relative target | unit-test 절차를 sibling에서 로드 | Red barrier/Test Map 유지 |
| `start-workflow/references/templates.md` | same relative target | `.codex`와 feedback gap 반영 | 상태·최종 보고 머리글 유지 |
| `start-workflow/references/verification-tier.md` | same relative target | `{SKILL_DIR}`·Phase 4.4 승인·Luna 1역할·`CODEX-UNAVAILABLE` 어휘 치환 | 점수표·게이트·금지 조건·승격 ①~⑦ 유지 |
| `start-workflow/assets/risk_facts.py` | same relative target | 바이트 동일 사본(2d7a01c, SHA-256 고정) | 검증 티어 사실 수집 유지 |
| `start-workflow/assets/test_failures.py` | same relative target | 바이트 동일 사본(2d7a01c, SHA-256 고정) | baseline·rerun 회귀 대조 유지 |
| `start-workflow/assets/workflow_archive.py` | same relative target | 바이트 동일 사본(2d7a01c, SHA-256 고정) | Workflow Report md 아카이브 배타 생성 유지 |
| `simplify-loop/references/workflow-script.md` | same relative target | 실행 JS가 아닌 상태 머신 명세 | 기존 상태 필드와 종료 판정 유지 |
| `e2e-test/assets/e2e-lock.sh` | same relative target | work-log fallback 제거 | acquire/heartbeat/release/timeout 유지 |
| `e2e-test-loop/assets/render_e2e_report.py` | same relative target | 바이트 동일 사본(41142d7, SHA-256 고정) | md 렌더링·verdict·GAP·직답 규칙 유지 |

### Inlined common dependencies

| source | target | purpose |
|---|---|---|
| `common/skills/commit/**` | `skills/commit/**` | 논리 단위 커밋 canonical |
| `common/skills/commit-push/**` | `skills/commit-push/**` | 브랜치/base/Assumption/push canonical |
| `common/skills/commit-pr/**` | `skills/commit-pr/**` | VERSION과 PR canonical |
| `common/skills/commit-hard-push/**` | `skills/commit-hard-push/**` | `--hard` 경로 |
| `common/skills/resolve-assumption/**` | `skills/resolve-assumption/**` | 개발 중 Assumption 해소 |
| `common/skills/doc-gen/**` | `skills/doc-gen/**` | E2E·workflow 보고서 렌더링 |

## Runtime adaptations

- Phase 1~4는 planning-only다. Phase 4.4의 명시적 사용자 승인이 기존 Plan mode 종료의 의미적 대체다.
- workflow 상태는 run-scoped 임시 디렉토리에 저장하고 resolved path를 subagent에 전달한다.
- 일반 custom agent model은 고정하지 않고 parent 모델과 reasoning effort를 기본 상속한다. 다만
  `start-workflow`는 사용자 승인된 고정 topology(Sol High orchestrator, Terra High/Max executor,
  Luna xHigh read-only, Sol Max Phase 4.3 advisor)를 사용한다. 모든 고정 spawn은 `fork_turns:none`이며,
  모델 미가용/실행 중 사망은 구분해 기존 `CODEX-UNAVAILABLE`·`SKIPPED:AGENT_DIED`·
  `DONE + degraded_fallback`·`BLOCKED:AGENT_DIED` 계약을 적용하고 타 모델로 대체하지 않는다.
- project override agent 파일은 parent가 읽어 해당 subagent prompt에 추가한다.
- fullstack 판정은 Phase 3에서 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 종료한다. 자동 BE 축소를 금지한다.

## 0.2.0 deviations (observed-behavior changes vs upstream)

| 영역 | upstream 동작 | 0.2.0 동작 | 근거 |
|---|---|---|---|
| request 질문 | 한 턴에 질문 하나 | `spec-only`는 남은 질문 전부, `standalone`은 한 턴 최대 4개; 기본값 첨부, 무응답/`skip`은 기본값 + `[Assumption]` | 왕복 턴 수 절감 |
| profile 부재 | 즉시 종료 | 프로젝트 루트 → linked worktree의 메인 워크트리 상속 → 둘 다 없을 때만 종료 (`PROFILE.md` "profile 해석") | 워크트리 세션의 원격 DB 부팅·설정 재발명 차단 |
| Phase 1 | 없음 | 중복 작업 스캔, 강 신호는 `BLOCKED:DUPLICATE_IN_PROGRESS` | 동일 기능 병렬 착수 방지 |
| 서브에이전트 대기 | 명시 없음 | `agent-prompts.md` "대기 규약" (역할별 타임아웃, 재대기 1회, 폴링 금지) | 폴링·재촉 비용 제거 |
| e2e-test 호출 | standalone만 | `mode: workflow` 전달 시 인증 부재는 질문 없이 `SKIPPED:NO_AUTH` | 자율 구간 무질문 계약 |
| 기준 브랜치 | `main` 하드코딩 (e2e-test, simplify-loop) | profile `mainBranch` 우선 | `dev` 기반 레포의 과대 diff 방지 |
| Assumption Gate | diff·커밋 본문 | + `{IMPL_NOTES}` `## 편차` (Spec `[Assumption]` 이월분) | push 전 Spec 가정 해소 |

## 0.3.0 deviations (observed-behavior changes vs upstream)

| 영역 | upstream 동작 | 0.3.0 동작 | 근거 |
|---|---|---|---|
| config 쓰기 대상 | `.claude/be-harness.local.md` 고정 | `{PROFILE_PATH}` — linked worktree에서는 상속된 메인 워크트리 profile에 반영, 보고에 절대 경로 + `[Assumption]` | 워크트리 세션에서 값을 고칠 경로 유지(0.2.0 상속 의도) |
| config 수정 고지 | codexMode/codexModels 변경 시에만 "상태 파일 값 유지" 고지 | 모든 키 수정에 "진행 중·재개되는 워크플로우는 상태 파일 스냅샷 값을 유지하며 새 값은 다음 실행부터 적용" 고지 | 실행 중 값 고정 원칙의 일반화 |

## 0.4.0 deviations (observed-behavior changes vs upstream)

| 영역 | upstream 동작 | 0.4.0 동작 | 근거 |
|---|---|---|---|
| 검증 티어 | upstream 1.1.0 기준 없음 | 1.2.0과 동일한 `light`·`standard` — 4.2 light는 Luna xHigh 1역할, 승격 ⑤는 `CODEX-UNAVAILABLE` | 저위험 작업의 검증 비용 축소 |
| Phase 12 아카이브 | HTML 노트 + md 재렌더링(0.2.0) | 슬림 리포트 1회 + 마감 후 `workflow_archive.py` 1회 배타 생성, 재렌더링 없음 | 결정 이력을 부록에 포함, 산출물 규칙 단일화 |
| impl-notes HTML 제거 | `*-impl-notes.html` 독립 생성 | 아카이브 부록 C로 흡수 | 산출물 중복 제거 |
| E2E 리포트 | HTML 렌더링 프롬프트 | `render_e2e_report.py` md + 기록 시점 정직성 마커 | 결정적 렌더링과 판정 근거 보존 |
| profile 스냅샷 | 재개 시 profile 재독 | `## Profile Snapshot` 고정 — 재개·형제 스킬은 snapshot 값(resolved 경로 포함)만 사용, 본문(Project Notes)은 스냅샷 대상 아님(읽기 전용 참조) | 재개 사이 환경 변동 차단 |
| 상태 스키마 fail-closed | 없음 | `SCHEMA` 키 + 필수 섹션 검사, 위반 시 `BLOCKED:STATE_SCHEMA_MISMATCH`·마이그레이션 없음 | 결정성 |
| smoke 무효화 | full 폴백만 | 실효 full latch + `{MAX_ITER}` 5 복원 + `--level-note` | 상한 일관성 |
| 리포트 이중 실패 | `{RUN_DIR}` 정리 | 렌더러·폴백 모두 실패 시 `{RUN_DIR}` 보존 + 리포트 없음 보고 | 원시 기록 보존 |
| E2E 폴백 저장 | `cp`·raw branch·덮어쓰기 가능 | slug + `set -C` 배타 생성(base→-2→-3) | 파일명 규칙·덮어쓰기 방지 |
| 상태 파일 `SCHEMA` 키·Snapshot resolved 경로 | Flags에 없음 | `- SCHEMA: 2`, `resolved_report_dir`·`resolved_e2e_lock_dir` | 스키마 버전·해석 고정 |

## 0.5.0 deviations (observed-behavior changes vs upstream)

| 영역 | upstream 동작 | 0.5.0 동작 | 근거 |
|---|---|---|---|
| 슬롯 레코드 | codexModels `{provider/agentType, model, effort}` | `topologyModels` `{model, effort?}` — provider·agentType 없음, `tiered`는 executor·advisor만; executor 기본 high와 advisor auto의 현재 선택 규칙은 0.6.3 절을 따른다 | Codex는 spawn 단위 provider 전환 미지원(실증 T3/T4) |
| 실행 플래그 | 플래그 값을 profile에 기록 | `--topology-models`는 실행 한정(ephemeral), profile 불변 | planning-only 경계 |
| 폴백 | 3계층 latch·Claude 패널 폴백 | 없음 — `model_unavailable({슬롯}:{사유})` + 기존 `CODEX-UNAVAILABLE`/`SKIPPED:AGENT_DIED`/`BLOCKED:AGENT_DIED`, bootstrap 실패는 상태 파일 없음 | 대체 금지 계약 |
| 무효 슬롯 | — | profile 무효 슬롯은 기본값 + 경고(doctor `INVALID_SLOT`), 플래그 무효는 재입력 1회/무시 + 경고 | profile 불변 |
| 역할 라벨 | 모델명 기반 표기 | Sol High / Terra High·Max / Luna xHigh / Sol Max 라벨 고정, model·effort만 교체 | 문서·계약 문자열 안정 |
| 상태 스키마 3 | — | `## Flags` `TOPOLOGY_MODELS`는 Build의 concrete executor/advisor 결정을 기록하고, Analyze/Verify 최소 헤더는 `executor=N/A,advisor=N/A`를 기록한다. Snapshot `topologyModels`와 schema 4 resume 계약은 유지한다 | 결정성 |

## Explicit gaps in 0.1.0

- Minmos overlay는 포함하지 않는다.
- fullstack workflow 자체는 포함하지 않는다.
- 원격 `submit-feedback`은 포함하지 않는다. 로컬 override를 저장하고 `SKIPPED:NO_FEEDBACK_UPSTREAM`을 반환한다.
- public ChatGPT 배포보다 로컬 Codex의 shell·Git workflow를 우선한다.


## 0.6.0 동기화와 Codex 차이

현재 on-disk BE와 기존 공통 6개 스킬을 기준으로 한다. FE/fullstack/minmos와 common의 신규 merge/sync-base/how-to-use/submit-feedback는 기존 BE 제품 범위 밖이며 추가하지 않는다. installed cache와 marketplace는 수정하지 않는다.

| 영역 | 동기화 | Codex 경계 |
|---|---|---|
| run/entry | workflow_run·policy와 명시적 resume, Run metadata, publish policy | BE Build/Analyze/Verify만; 외부 CLI/provider/overlay 경로 미지원 |
| state | schema 4와 공통 Run(CWD/MODE/RUN_ID/RUN_DIR), PUBLISH_POLICY/ROUTE_TARGET | topologyModels·immutable Profile Snapshot 유지. schema 2→3 자동 보완은 폐지; 구 schema/없는 run.json은 차단 |
| results/finalization | v1 JSON, 실제 tested_tree, append-only events, 승인 수정 후 재검증·원격 반영·배타 archive | Sol High가 공유 결과/상태 유일 owner. FAIL/BLOCKED를 DONE으로 바꾸지 않음 |
| scope/writers | START_SHA+index/worktree/소유 untracked, 삭제/symlink, receipt/stop/scope | 실제 cwd 강제 없는 collaboration host는 순차 Terra. interrupt 접수는 종료 근거 아님. 고정 topology/model/effort 유지 |
| E2E | v2 lease helper·bind 자원·토큰·heartbeat, JSON renderer, 중단 이력, 빌드 후 재검증 | Codex PTY/session·55초 이하 poll·540초 총 대기, profile snapshot 유지. 기본 HTTP 범위 유지 |
| TDD | Go package/JS file 전체 ID·오류 전체 비교·재실행 실패 보존 | 같은 ID 규칙을 Test Map/baseline에 적용 |
| config/doctor | bounded parser·원자 apply·오프라인 활성 의존성 검사 | .codex 상속 경로, topologyModels 4슬롯/provider 없음, preset 임의 감지 없음 |
| common | git_checks·dirty index 보존·현재 HEAD Gate·base 분리·PR 재사용 | 동봉 skill 절차 사용; 기존 승인 범위 유지 |
| doc-gen | 실제 Mermaid renderer·offline SVG·twin 검증·배타 생성 | workflow/E2E 보고는 계속 md; doc-gen의 html/twin만 Node/Chromium 사용 |

순수 helper와 renderer/lock/git assets는 원본과 바이트 동일하다. policy/profile/doctor는 native adapter이며 원본/결과 해시를 각각 기록한다. profile parser는 typed JSON 배열의 쉼표도 지원한다. 모델/effort 허용값은 기존 native topology 표 그대로다.

새 lifecycle/result/scope/writer/finalization reference와 config/commit/doc-gen assets는 각 skill 또는 Phase 진입점에서 로드한다. E2E renderer는 Markdown 대신 JSON을 입력으로 받으며 workflow_archive에는 --results를 전달한다. 구 Markdown-only archive 출력은 helper의 DEGRADED 호환 경로일 뿐 신규 workflow에서 사용하지 않는다.

이전 이식 표의 2d7a01c/41142d7 SHA 고정은 릴리스 이력이다. 현재 기준은 [UPSTREAM-SYNC.json](UPSTREAM-SYNC.json)의 복사 당시 source_sha256/target_sha256이다. 검증은 플러그인 구조·native adapter·실제 로컬 Git/worktree/lock·오프라인 renderer까지이며 외부 모델 전체 workflow나 실제 서비스 API/push/PR를 실행했다는 뜻은 아니다.

### 0.6.0 공통 실행 지침 보강 (2026-09-07)

[공통 실행 원칙](skills/start-workflow/references/execution-policy.md)은 OpenAI 가이드와 사용자의 자율 실행 요청을 적용한 로컬 지침이다. 참조 전용 `default-conventions`를 제외한 16개 실행 스킬에서 읽는다.

| 영역 | 달라지는 동작 | 유지하는 계약 |
|---|---|---|
| 요청·승인 | 문맥에서 확정 가능한 내용은 알리고 진행; 같은 대상·효과의 기존 승인 재사용; 필요한 질문은 현재 Phase에서 허용된 준비 후 구체적으로 제시 | Phase 4.4의 구체적 Plan 승인, 미해소 Assumption Gate, 승인된 원격 효과 범위 |
| 지침 충돌 | 사용자 명시 지시 우선, 중단을 유발한 실제 파일·문구·해석 공개; 소비 프로젝트 override 규칙과 플러그인 유지보수 범위 구분 | 호스트 권한, 모드 범위, 명시된 종료 조건 |
| 위임 | bootstrap·일반 envelope에 최신 지시·승인 원문·미결 결정 전달 | 고정 topology·effort·단일 writer; Phase 8.8 소스 전용 격리 |
| 검증·보고 | 변경 규모에 맞는 검증, 근거 없는 추가 반복 생략, 간결한 일반 설명 | 프로젝트·티어별 필수 검증, 수정 후 재검증, 출력 머리글·결과 스키마 |

모델 기본값·API 요청·실행 자산은 이 지침 보강의 변경 대상이 아니다. 이후 upstream 동기화에서도 위 로컬 차이를 보존한다.


## 세션 기반 역할 배정과 명시적 모델 최신화

사용자 요청(2026-09-09)에 따라 고정 모델 orchestrator bootstrap/relay를 제거하고 현재 사용자 세션이
Orchestrator를 맡는다. 신규 실행은 `orchestrator=session@inherit`로 기록한다. 모델명에서 유래한 역할 라벨을
Orchestrator/Worker/Readonly/Advisor로 바꾸되 기존 `orchestrator`/`executor`/`readonly`/`advisor` 슬롯과
Phase 순서·상태 코드·루프 상한·출력 머리글·단일 writer·독립 검토 권한을 유지한다. 기존 상태의 역할 라벨은
과거 기록이며 재작성하지 않는다. legacy concrete orchestrator도 과거 값으로 보존하고 새 Phase는 현재 세션으로 수행한다.

초기 advisor 모델은 Astra로 바꾸고 기존 자동 `N/A|xhigh|max` 호출 정책을 유지한다. Worker=Terra,
Readonly=Luna는 유지한다. 공식 가이드는 설계 추론과 범위가 정해진 하위 작업을 구분하므로 역할별
모델 배정과 책임을 분리했다. 근거: [최신 모델 가이드](https://developers.openai.com/api/docs/guides/latest-model),
[하위 에이전트 가이드](https://learn.chatgpt.com/docs/agent-configuration/subagents). 직접 성능 비교 결과는 아니다.

`refresh-models`는 사용자 요청 시에만 조사·갱신하고 일반 workflow/doctor는 오프라인이다.
확정 profile의 부모 아래 `be-harness/models.json`에 추천 모델·effort·확인 날짜·공식 URL·역할별 이유·호스트가
노출한 지원 effort를 저장한다. profile을 메인 worktree에서 상속하면 추천표도 공유한다. 플러그인 캐시나
전역 설정을 수정하지 않는다. 호스트의 노출 정보는 dispatch 성공 증거와 구분한다.

새 우선순위는 flags > 사용자 profile > 저장된 추천 > 번들 표다. profile의 무효 슬롯은 경고 후 추천값으로
돌아가며(기존 bundled-only fallback에서 변경), 플래그 `slot=default`는 profile을 건너뛰고 추천을 선택한다.
config의 default는 override 삭제다. 명시 model-only override는 기존 번들 effort 정책을 유지하며 하위
레코드의 effort를 섞지 않는다. orchestrator override는 legacy 읽기 호환만 남기고 경고 후 현재 세션을 유지한다.
지원 effort enum에 `ultra`를 추가하지만 모델별 실제 지원은 호스트 근거/dispatch로 구분한다.

추천표는 preview/hash 비교 후 원자적으로 생성·교체한다. 손상·중복 키·비지원 schema·symlink·근거 부족은
원본 보존으로 종료한다. 누락된 추천표는 번들 표만 읽고 자동 파일 생성이나 온라인 갱신을 하지 않는다.
진행 중·재개 실행은 저장된 하위 배정/concrete advisor를 재사용하고 최신 추천을 읽지 않는다.
이 변경은 별도 reviewer 슬롯, 자동 모델 승격, 성능 벤치마크, 원격 게시를 추가하지 않는다.
