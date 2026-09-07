# Compatibility Contract

## 기준

- upstream: `kangmomin/harness-plugins`
- commit: `f9ce681427ccfbfd9194d3c3f204a445ae6f45dd` + 현재 미커밋 작업 트리 (파일별 실제 입력 해시는 UPSTREAM-SYNC.json)
- source plugin: `be-harness@1.5.4`; inlined common `common@0.14.2`
- target plugin: `codex-be-harness@0.6.0`

호환성은 문장 일치가 아니라 관찰 가능한 workflow 동작을 기준으로 한다. Phase 순서, 승인·차단 게이트, 상태 코드, 루프 상한, 보고서 머리글을 invariant로 본다.

### 이식 이력 (아래 과거 릴리스 계약은 0.6.0 변경으로 대체될 수 있음)

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
| 슬롯 레코드 | codexModels `{provider/agentType, model, effort}` | `topologyModels` `{model, effort?}` — provider·agentType 없음, `tiered`는 executor만 | Codex는 spawn 단위 provider 전환 미지원(실증 T3/T4) |
| 실행 플래그 | 플래그 값을 profile에 기록 | `--topology-models`는 실행 한정(ephemeral), profile 불변 | planning-only 경계 |
| 폴백 | 3계층 latch·Claude 패널 폴백 | 없음 — `model_unavailable({슬롯}:{사유})` + 기존 `CODEX-UNAVAILABLE`/`SKIPPED:AGENT_DIED`/`BLOCKED:AGENT_DIED`, bootstrap 실패는 상태 파일 없음 | 대체 금지 계약 |
| 무효 슬롯 | — | profile 무효 슬롯은 기본값 + 경고(doctor `INVALID_SLOT`), 플래그 무효는 재입력 1회/무시 + 경고 | profile 불변 |
| 역할 라벨 | 모델명 기반 표기 | Sol High / Terra High·Max / Luna xHigh / Sol Max 라벨 고정, model·effort만 교체 | 문서·계약 문자열 안정 |
| 상태 스키마 3 | — | `## Flags` `TOPOLOGY_MODELS`(Phase 5 기록 시 executor 확정값; 스키마 검사는 Build 상태 파일 한정, Analyze/Verify 최소 헤더는 `TOPOLOGY_MODELS`(executor=N/A) 1줄만 기록), Snapshot `topologyModels`; `SCHEMA: 2` 재개 시 기본값 보완 + 원자 교체(난이도 기록 없으면 차단) | 결정성 |

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
