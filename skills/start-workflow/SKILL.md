---
name: start-workflow
description: "BE 개발 전 과정을 오케스트레이션한다. '워크플로우 시작', '기능을 전 과정으로 구현해줘' 요청에는 Build(기본), '코드 분석해줘'에는 --analyze, '보안·성능·버그를 검증해줘'에는 --verify로 사용한다."
---

# Start Workflow

BE 작업을 Build, Analyze, Verify 중 한 모드로 실행한다. 프로젝트 지침과
`.codex/be-harness/common.md`, `.codex/be-harness/skills/start-workflow.md`가 있으면 먼저 읽고,
프로젝트 오버라이드가 이 스킬보다 우선한다.

사용자와의 대화는 profile의 `language`(기본 `ko`)를 따른다.

모든 모드의 역할·모델·bootstrap·writer 경계는 [agent-topology.md](references/agent-topology.md)가
canonical이다. 이 스킬에만 적용하는 고정 토폴로지 예외다.

## 모드와 플래그

| 플래그 | 모드/효과 |
|--------|-----------|
| `--analyze`, `-a` | Analyze: 코드 수정 없이 Phase A1~A4 실행 |
| `--verify`, `-v` | Verify: Phase V1~V5 실행 후 `PASS/WARN/FAIL` 판정 |
| `--hard`, `-h` | Build에서 브랜치 생성 없이 현재 브랜치에 일반 push; PR 생략 |
| `--no-tdd` | Build의 Red 및 baseline 수집 생략. 검증 티어는 standard 강제. |
| `--tier standard` | Build: Phase 2 판정과 무관하게 검증 티어를 standard로 강제한다(light 축소 비활성). light 강제 플래그는 없다 |
| `--topology-models {슬롯}={model}[@{effort}],…` | 모든 모드: 이번 실행에 한해 토폴로지 슬롯의 model/effort를 교체한다(`{슬롯}=default` 허용). profile에는 기록하지 않는다 — 영구 변경은 `$codex-be-harness:config topologyModels=…`. 규칙: [agent-topology.md](references/agent-topology.md) "슬롯 설정" |
| `--reflect` | Build의 Phase 11 실행; 기본은 `SKIPPED:REFLECT_NOT_REQUESTED` |

`--analyze`와 `--verify`는 상호 배타적이다. 둘 다 있으면 하나를 선택받는다. `--hard`·`--no-tdd`·`--tier standard`·`--reflect`는
Build 전용이며 다른 모드에서는 무시한다. `--topology-models`는 모든 모드에 적용된다. 모드 플래그 뒤 경로는 범위이고, 없으면 profile의
`sourceDirs`를 기본 후보로 사용한다.

Analyze 또는 Verify라면 [analyze-verify-modes.md](references/analyze-verify-modes.md)를 읽고 그 절차만
실행한다. Build라면 아래 계약과 [build-phases.md](references/build-phases.md)를 따른다.

## Pre-flight

모든 모드에서 profile을 읽어 다음 값을 추출한다. profile 경로 `{PROFILE_PATH}`는 플러그인 루트 `PROFILE.md`의
"profile 해석" 규칙으로 확정한다 — 프로젝트 루트의 `.codex/be-harness.local.md`가 우선이고, linked worktree에
없으면 메인 워크트리의 것을 상속하며 `[Assumption] 메인 워크트리 profile 상속: {경로}`로 보고한다.

`preset`, `buildCommand`, `testCommand`, `lintCommand`, `typeCheckCommand`, `makeTestCommand`,
`runServerCommand`, `serverUrl`, `e2eEnabled`, `apiDocsPath`, `sourceDirs`, `testDirs`,
`mainBranch`, `featureBranchPrefix`, `hotfixBranchPrefix`, `commitPrefixes`, `commitCoAuthor`,
`projectConventions`, `reportDir`, `feedbackUpstreamRepo`, `e2eLockDir`, `language`, `topologyModels`.

프로젝트 루트와 메인 워크트리 어디에도 profile이 없으면(`PROFILE_MISSING`) 값을 추측하지 않고
`.codex/be-harness.local.md` 생성이 필요하다고 알린 뒤 mutation 없이 종료한다. Build에서는 누락된
명령 때문에 생략될 Phase와 위험을 승인 전에 알린다. `buildCommand`, `testCommand`, E2E 3종 값,
`apiDocsPath`, `makeTestCommand`을 검사한다. Analyze/Verify의 명령 누락은 해당 단계에
`SKIPPED:PROFILE_EMPTY`로 기록한다.

Build에 누락이 있으면 영향 Phase를 구체적으로 나열하고, 해당 Phase를 `SKIPPED:{사유}`로 기록한 채
진행할지 profile을 보완한 뒤(또는 `$codex-be-harness:config {키}={값}`으로 누락 값만 추가한 뒤) 재시작할지 결정받는다. 누락을 Phase 내부 실패로 뒤늦게 판정하지 않는다.

**토폴로지 슬롯 resolve**(모든 모드, 1회): [agent-topology.md](references/agent-topology.md) "슬롯 설정" 규칙대로 슬롯 레코드 단위 `--topology-models` > profile `topologyModels` > 기본값 순으로 `{TOPOLOGY_MODELS}`를 확정한다. profile의 무효 슬롯은 그 슬롯만 기본값으로 대체하고 경고한다(profile 불변, `$codex-be-harness:doctor`가 `INVALID_SLOT`으로 보고). 플래그가 무효면 대화형은 재입력 1회, 비대화형은 플래그를 무시하고 경고한다. executor effort는 profile/플래그가 고정 effort를 지정하지 않는 한 `tiered`로 두었다가 Phase 2에서 난이도로 확정한다(Analyze/Verify는 `executor=N/A`). Pre-flight 보고에 `토폴로지 모델: 기본 | {변경 슬롯 요약 — 슬롯=model@effort, …}` 1줄을 넣는다. spawn 인자로는 확정값만 전달한다(`tiered`·`N/A`·`-` 금지).

## 실행별 상태

Build는 Phase 4.4 승인 후 Phase 5 진입 시, Analyze/Verify는 모드 범위가 확정된 뒤 안전한 임시 루트
아래에 전용 디렉터리를 만든다. 고정 `/tmp` 파일명을 재사용하지 않는다.

```text
{RUN_DIR}=mktemp -d "${TMPDIR:-/tmp}/codex-be-workflow.XXXXXX"
{STATE_FILE}={RUN_DIR}/workflow-state.md
{IMPL_NOTES}={RUN_DIR}/implementation-notes.md
{WORK_REPORT}={RUN_DIR}/workflow-report.md
{RUN_ID}=`## Flags`의 RUN_ID (Phase 5에서 1회 생성)
{START_SHA}=`## Flags`의 START_SHA (Phase 5 기준 커밋)
{REPORT_DIR}=profile.reportDir 또는 .codex/harness-reports
{CWD}=검증된 프로젝트 루트 절대 경로
{PROFILE_PATH}=PROFILE.md의 "profile 해석"으로 확정한 profile 절대 경로
{SKILL_DIR}=이 SKILL.md가 있는 디렉터리의 절대 경로 (assets/·references/ 해석 기준)
{PLAN_MAX}=Phase 4.3 상한 — standard 5 / light 2
{QL_MAX}=Phase 8 상한 — standard 3 / light 2
{TOPOLOGY_MODELS}=Pre-flight 확정 슬롯 문자열 — Phase 5부터는 `## Flags`의 TOPOLOGY_MODELS(Phase 2 이후 executor 확정값 포함)
```

해결된 절대 경로를 모든 서브에이전트에 전달한다. 상태에는 `Flags`, `Run`, `Profile Snapshot`,
`Verification Tier`, `Current Phase`, `Phase Assignments`, `Remaining Phases`, `Final Decisions`, `Artifacts`,
`Phase Results`를 유지하고 Phase 전후에 `IN_PROGRESS`와 최종 상태를 기록한다.
서버를 띄운 Phase는 PID 또는 세션 핸들을 저장하고 성공·실패·중단 모든 종료 경로에서 정리한다.
상태와 노트는 기본 보관하며, 사용자가 정리를 요청했을 때만 검증된 `{RUN_DIR}` 내부를 삭제한다.

### 재개 규칙

- `## Flags`(SCHEMA·MODE·HARD_MODE·TDD·REFLECT·TIER·TOPOLOGY_MODELS·RUN_ID·START_SHA)는 컨텍스트 요약·세션 재개로 CLI 인자를 잃은 뒤 이어갈 때 **유일한 기준** — CLI 인자와 충돌하면 기록값 우선 + 고지. `RUN_ID`는 Phase 5에서 1회 생성하며 재생성하지 않는다.
- 재개 시 Phase dispatch 전에 **Build 상태 파일**(`MODE: be`)의 스키마를 검사한다(Analyze/Verify 상태 파일은 [analyze-verify-modes.md](references/analyze-verify-modes.md)의 최소 헤더만 확인한다): `## Flags` 정확히 1개 + 필수 키 9개 각 1회 + `SCHEMA: 3` / `## Profile Snapshot` 정확히 1개 + `profile_path`(비어 있지 않음)·`profile_sha256`(16진수 64자)·`resolved_report_dir`·`resolved_e2e_lock_dir`(절대 경로) + profile 키 23개(`topologyModels` 포함) 각 정확히 1회(`키: 값` 1줄, 배열은 인라인, 빈 값 허용) / `## Verification Tier` 정확히 1개 + `- 계산 티어:`·`- 최종 티어:` 각 1회 / `## Test Baseline` 헤더 0개 또는 1개. 하나라도 어긋나면 `BLOCKED:STATE_SCHEMA_MISMATCH`(누락·중복 항목 나열)로 종료하고 새 실행을 안내한다 — 구버전·쓰기 중단 상태 파일은 마이그레이션하지 않는다. **유일한 예외**: `SCHEMA: 2` 파일(0.4.0)은 `TOPOLOGY_MODELS`·`topologyModels`를 제외한 검사를 통과하면 Phase dispatch 전에 1회 보완한다 — `## Flags`에 `- TOPOLOGY_MODELS:`(기본값; executor effort는 상태 파일에 기록된 난이도 `[N]/10`으로 `high|max` 확정, 난이도 기록이 없으면 Phase 2 이전이므로 `BLOCKED:STATE_SCHEMA_MISMATCH`), `## Profile Snapshot`에 `- topologyModels: default`를 추가하고 `SCHEMA: 3`으로 올린다. 같은 디렉터리의 임시 파일 `mktemp "{RUN_DIR}/.workflow-state.XXXXXX"`에 전체를 쓰고 스키마 3 검사를 통과시킨 뒤 `mv -f`로 교체한다(실패 시 임시 파일만 삭제, 원본 불변, `BLOCKED:STATE_SCHEMA_MISMATCH`). 보완 사실을 고지하고 이후 Flags는 다시 불변이다(유일한 예외는 `TIER` — [verification-tier.md](references/verification-tier.md)의 단방향 승격 `light → standard` 갱신).
- 검사를 통과한 뒤 `## Test Baseline` 완전성([tdd.md](references/tdd.md) Phase 5 canonical)이 미완이면 스키마 차단이 아니라 Phase 5 미완 재개로 처리한다.
- 형제 스킬·서브에이전트·재개된 오케스트레이터는 `## Profile Snapshot` 값(resolved 경로 포함)만 쓰고 profile을 다시 읽지 않는다(live 아님). `profile_sha256`은 출처 기록용이며 재개 시 비교하지 않는다. 본문(Project Notes)은 스냅샷 대상이 아니며 읽기 전용 참조만 허용한다(frontmatter 값 재독 금지).
- 상태 파일 생성 이전 중단은 재개 대상이 아니라 Pre-flight부터 재시작한다(profile 재확정).

상태 템플릿과 최종 보고는 [templates.md](references/templates.md)를 사용한다.

## Build 불변 계약

- Phase 1~4.4는 planning-only 구간으로 읽기·질문·Spec·Plan만 수행한다. 파일 편집, 브랜치, 커밋,
  push, PR을 금지한다.
- Phase 4.4에서 확정 Spec/Plan과 이후의 브랜치·코드 변경·커밋·push·PR 효과를 명시하고 사용자에게
  실행 승인을 받는다. 승인 전에는 Phase 5로 넘어가지 않는다.
- Phase 3에서 FE+BE 범위를 감지하면 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 종료한다. FE/BE 근거와
  영향 파일을 보고한다. 사용자가 BE-only를 선택하면 FE 범위를 Spec에서 제거하고 Phase 2부터 재개한다.
- 자율 구간은 Phase 6~11이다. Phase가 끝나면 같은 실행 흐름에서 다음 Phase로 진행하며,
  Build 실패처럼 명시된 중단 조건 외에는 중간 진행 확인을 요구하지 않는다.
- Spec 밖 동작 변경은 적용하지 않고 `[Assumption]`과 구현 노트 `## 편차`에 기록해 Phase 12에서
  결정받는다.
- TDD baseline은 불변이다. Red/Green, Test Map, TestConflict, 회귀 분류 계약은
  [tdd.md](references/tdd.md)를 따른다.
- 검증 티어(`light`/`standard`)는 Phase 2에서 판정하고 Phase 4.4에서 함께 승인받는다. 티어 승격(light → standard, 단방향 latch)은 항상 해당 루프의 종료 조건·상한 평가보다 **먼저** 적용한다. 규칙은 [verification-tier.md](references/verification-tier.md)가 canonical이다.
- Phase 8은 최대 `{QL_MAX}`회이며 single-writer 수정과 격리 Read-back을 보장한다.
  [quality-loop.md](references/quality-loop.md)를 따른다.
- 외부 상태를 바꾸는 commit/push/PR 절차는 승인된 Phase 5 이후에만 실행한다. Phase 10 직전
  Assumption Gate를 다시 적용한다.
- 독립 리뷰는 Phase 4.2 Luna 리뷰어(최대 3)와 Phase 4.3 Sol Max advisor다. 전역 지침의 이중/교차 리뷰
  요건은 이로써 충족되며, `claude -p`·`gemini` 등 **외부 CLI 리뷰어를 호출하지 않는다**. 스킬 밖 작업이면
  fresh-context 서브에이전트 1개로 대체한다.
- 사용자 입력이 필요하면 `USER_INPUT_REQUIRED: {질문}`으로 사용자 대면 턴을 끝내고, 응답은
  [agent-topology.md](references/agent-topology.md)의 계약대로 **같은 orchestrator task**에 follow-up한다(새
  bootstrap 금지). 자율 구간 Phase 6~11에서는 질문하지 않고 `[Assumption]` 또는 `SKIPPED:{사유}`로 기록한다.
- Phase 진입 체크: Phase 5는 `{STATE_FILE}`·`{IMPL_NOTES}` 생성과 baseline 수집(또는 명시적 `SKIPPED:*`
  기록) 없이 Phase 6으로 가지 않는다(`## Test Baseline` 완전성은 [tdd.md](references/tdd.md) Phase 5 정의). Phase 8은 [quality-loop.md](references/quality-loop.md)를 읽은 뒤
  시작하며 8.4와 8.8은 생략하지 않는다. Phase 12는 슬림 Workflow Report를 `{WORK_REPORT}`에 쓴 뒤 결정 마감 후
  md 아카이브(`*-workflow-report.md`)를 `{REPORT_DIR}`에 1회 남긴다.
- Phase 1의 중복 작업 스캔에서 강 신호가 나오면 `BLOCKED:DUPLICATE_IN_PROGRESS`로 종료한다. 사용자가
  계속을 지시하면 Phase 1부터 재개한다.

## 서브에이전트와 형제 스킬

고정 모델·effort·`fork_turns:none`·재시도/대체 금지 규칙은
[agent-topology.md](references/agent-topology.md)를 따른다. executor effort가 `tiered`(기본)이면 난이도 1~8 `high`(Terra High), 9~10 `max`(Terra Max)로 확정하고,
profile/플래그의 고정 effort는 그대로 쓴다. Phase 2의 리스크 산정에는 보안, 데이터 이관, 복잡한 API/계약 변경을 반드시
반영한다. 각 프롬프트에는 `{CWD}`, `{STATE_FILE}`, `{IMPL_NOTES}`, 현재/남은 Phase, 파일 소유권,
읽기/쓰기 허용 범위를 넣는다. 공통 프롬프트와 사망 처리는 [agent-prompts.md](references/agent-prompts.md)를,
역할별 판정 계약은 [references/agents/](references/agents/) 문서를 사용한다.

모든 고정 spawn의 model/effort는 `{TOPOLOGY_MODELS}`의 해당 슬롯 확정값이며 역할 라벨(Sol High / Terra High·Max / Luna xHigh / Sol Max)은 슬롯 설정과 무관하게 유지된다.

다른 기능이 필요할 때 호출 문자열에 위임하지 않는다. 해당 형제 스킬의 `SKILL.md`를 읽고 그 절차를
현재 컨텍스트에서 수행하거나, 필요한 계약을 서브에이전트 프롬프트에 포함한다.

| 기능 | 읽을 형제 절차 |
|------|----------------|
| 명세 수집 | `../request/SKILL.md` (start-workflow 내부에서는 spec-only) |
| Red 테스트 | `../unit-test/SKILL.md` |
| 단순화 dry-run | `../simplify-loop/SKILL.md` |
| 컨벤션 검사 | `../convention-check/SKILL.md` |
| E2E 루프 | `../e2e-test-loop/SKILL.md` |
| 일반 PR | `../commit-pr/SKILL.md` |
| hard push | `../commit-hard-push/SKILL.md` |

## Phase 요약

1. Phase 1: 범위 수집 및 Technical Spec 사용자 확인
2. Phase 2: 코드 복잡도와 영향 리스크 난이도 산정 + 검증 티어(light/standard) 판정 + executor effort 확정
3. Phase 3: `sequential` / `parallel-slices` / fullstack handoff 판정
4. Phase 4: Plan 작성 → 다관점 보강 → 최대 `{PLAN_MAX}`회 독립 검증 → 4.4 실행 승인
5. Phase 5: 브랜치, 상태/노트, TDD baseline 생성
6. Phase 6: Red 테스트 후 Green 구현
7. Phase 7: 강제 빌드, 실패 수정 최대 3회
8. Phase 8: 품질 루프 최대 `{QL_MAX}`회 후 격리 Read-back 1회(light: 8.2·8.8 SKIP, 8.6 smoke)
9. Phase 9: API 변경일 때 파일 기반 API 문서 동기화
10. Phase 10: Assumption Gate 후 PR 또는 hard push
11. Phase 11: `--reflect`일 때만 성찰
12. Phase 12: 슬림 Workflow Report, 이연 결정(Final Decisions), md 아카이브, 정리

세부 순서·판정·상한은 [build-phases.md](references/build-phases.md)가 canonical이다.

## 상태 코드

Phase 상태는 `DONE`, `IN_PROGRESS`, `PENDING`, `SKIPPED:{사유}`, `BLOCKED:{사유}`만 사용한다.
검증 판정은 `PASS/WARN/FAIL`이다. 다음 계약 상태를 보존한다.

- `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`, `BLOCKED:MAX_ITERATIONS`, `BLOCKED:BUILD_FAIL`
- `BLOCKED:DUPLICATE_IN_PROGRESS`
- `BLOCKED:NO_VALID_RED`, `BLOCKED:REGRESSION_AT_RED`, `BLOCKED:TEST_NOT_GREEN`
- `BLOCKED:AGENT_DIED`, `BLOCKED:ASSUMPTION_UNRESOLVED`, `BLOCKED:STATE_SCHEMA_MISMATCH`
- `SKIPPED:PROFILE_EMPTY`, `SKIPPED:TIER_LIGHT`, `SKIPPED:USER_OPT_OUT`, `SKIPPED:NO_TEST_BASIS`
- `SKIPPED:REFLECT_NOT_REQUESTED`, `SKIPPED:BUDGET_PRESERVED`, `SKIPPED:AGENT_DIED`
- Phase 12 feedback: `SKIPPED:NO_FEEDBACK_UPSTREAM` when `feedbackUpstreamRepo` is absent

`red_assertion`, `already_satisfied`, `cannot_compile`, `deferred_e2e`, `regression`,
`pre_existing`, `new_red`, `flaky`, `agent_retry`, `degraded_fallback`, `tier_escalated`, `script_fallback`,
`unparsed`, `rerun_incomplete`는 진단 데이터이며 Phase 상태가 아니다.

## Reference routing

- Build 상세: [build-phases.md](references/build-phases.md)
- 검증 티어: [verification-tier.md](references/verification-tier.md)
- Analyze/Verify: [analyze-verify-modes.md](references/analyze-verify-modes.md)
- TDD와 baseline: [tdd.md](references/tdd.md)
- Phase 8: [quality-loop.md](references/quality-loop.md)
- 위임 프롬프트: [agent-prompts.md](references/agent-prompts.md)
- 고정 토폴로지: [agent-topology.md](references/agent-topology.md)
- 상태·보고·아카이브: [templates.md](references/templates.md)
