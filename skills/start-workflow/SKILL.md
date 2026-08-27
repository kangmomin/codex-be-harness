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
| `--no-tdd` | Build의 Red 및 baseline 수집 생략 |
| `--reflect` | Build의 Phase 11 실행; 기본은 `SKIPPED:REFLECT_NOT_REQUESTED` |

`--analyze`와 `--verify`는 상호 배타적이다. 둘 다 있으면 하나를 선택받는다. 나머지 세 플래그는
Build 전용이며 다른 모드에서는 무시한다. 모드 플래그 뒤 경로는 범위이고, 없으면 profile의
`sourceDirs`를 기본 후보로 사용한다.

Analyze 또는 Verify라면 [analyze-verify-modes.md](references/analyze-verify-modes.md)를 읽고 그 절차만
실행한다. Build라면 아래 계약과 [build-phases.md](references/build-phases.md)를 따른다.

## Pre-flight

모든 모드에서 profile을 읽어 다음 값을 추출한다. profile 경로 `{PROFILE_PATH}`는 플러그인 루트 `PROFILE.md`의
"profile 해석" 규칙으로 확정한다 — 프로젝트 루트의 `.codex/be-harness.local.md`가 우선이고, linked worktree에
없으면 메인 워크트리의 것을 상속하며 `[Assumption] 메인 워크트리 profile 상속: {경로}`로 보고한다.

`buildCommand`, `testCommand`, `lintCommand`, `typeCheckCommand`, `makeTestCommand`,
`runServerCommand`, `serverUrl`, `e2eEnabled`, `apiDocsPath`, `sourceDirs`, `testDirs`,
`mainBranch`, `featureBranchPrefix`, `hotfixBranchPrefix`, `commitPrefixes`, `commitCoAuthor`,
`projectConventions`, `reportDir`, `feedbackUpstreamRepo`, `language`.

프로젝트 루트와 메인 워크트리 어디에도 profile이 없으면(`PROFILE_MISSING`) 값을 추측하지 않고
`.codex/be-harness.local.md` 생성이 필요하다고 알린 뒤 mutation 없이 종료한다. Build에서는 누락된
명령 때문에 생략될 Phase와 위험을 승인 전에 알린다. `buildCommand`, `testCommand`, E2E 3종 값,
`apiDocsPath`, `makeTestCommand`을 검사한다. Analyze/Verify의 명령 누락은 해당 단계에
`SKIPPED:PROFILE_EMPTY`로 기록한다.

Build에 누락이 있으면 영향 Phase를 구체적으로 나열하고, 해당 Phase를 `SKIPPED:{사유}`로 기록한 채
진행할지 profile을 보완한 뒤(또는 `$codex-be-harness:config {키}={값}`으로 누락 값만 추가한 뒤) 재시작할지 결정받는다. 누락을 Phase 내부 실패로 뒤늦게 판정하지 않는다.

## 실행별 상태

Build는 Phase 4.4 승인 후 Phase 5 진입 시, Analyze/Verify는 모드 범위가 확정된 뒤 안전한 임시 루트
아래에 전용 디렉터리를 만든다. 고정 `/tmp` 파일명을 재사용하지 않는다.

```text
{RUN_DIR}=mktemp -d "${TMPDIR:-/tmp}/codex-be-workflow.XXXXXX"
{STATE_FILE}={RUN_DIR}/workflow-state.md
{IMPL_NOTES}={RUN_DIR}/implementation-notes.md
{REPORT_DIR}=profile.reportDir 또는 .codex/harness-reports
{CWD}=검증된 프로젝트 루트 절대 경로
{PROFILE_PATH}=PROFILE.md의 "profile 해석"으로 확정한 profile 절대 경로
```

해결된 절대 경로를 모든 서브에이전트에 전달한다. 상태에는 `Current Phase`, `Phase Assignments`,
`Remaining Phases`, `Phase Results`를 유지하고 Phase 전후에 `IN_PROGRESS`와 최종 상태를 기록한다.
서버를 띄운 Phase는 PID 또는 세션 핸들을 저장하고 성공·실패·중단 모든 종료 경로에서 정리한다.
상태와 노트는 기본 보관하며, 사용자가 정리를 요청했을 때만 검증된 `{RUN_DIR}` 내부를 삭제한다.

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
- Phase 8은 최대 3회이며 single-writer 수정과 격리 Read-back을 보장한다.
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
  기록) 없이 Phase 6으로 가지 않는다. Phase 8은 [quality-loop.md](references/quality-loop.md)를 읽은 뒤
  시작하며 8.4와 8.8은 생략하지 않는다. Phase 12는 Implementation Notes HTML과 Workflow Report md를 둘 다
  `{REPORT_DIR}`에 남긴다.
- Phase 1의 중복 작업 스캔에서 강 신호가 나오면 `BLOCKED:DUPLICATE_IN_PROGRESS`로 종료한다. 사용자가
  계속을 지시하면 Phase 1부터 재개한다.

## 서브에이전트와 형제 스킬

고정 모델·effort·`fork_turns:none`·재시도/대체 금지 규칙은
[agent-topology.md](references/agent-topology.md)를 따른다. 난이도 1~8은 Terra High, 9~10은 Terra Max로
Executor를 배정한다. Phase 2의 리스크 산정에는 보안, 데이터 이관, 복잡한 API/계약 변경을 반드시
반영한다. 각 프롬프트에는 `{CWD}`, `{STATE_FILE}`, `{IMPL_NOTES}`, 현재/남은 Phase, 파일 소유권,
읽기/쓰기 허용 범위를 넣는다. 공통 프롬프트와 사망 처리는 [agent-prompts.md](references/agent-prompts.md)를,
역할별 판정 계약은 [references/agents/](references/agents/) 문서를 사용한다.

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
2. Phase 2: 코드 복잡도와 영향 리스크 난이도 산정
3. Phase 3: `sequential` / `parallel-slices` / fullstack handoff 판정
4. Phase 4: Plan 작성 → 다관점 보강 → 최대 5회 독립 검증 → 4.4 실행 승인
5. Phase 5: 브랜치, 상태/노트, TDD baseline 생성
6. Phase 6: Red 테스트 후 Green 구현
7. Phase 7: 강제 빌드, 실패 수정 최대 3회
8. Phase 8: 품질 루프 최대 3회 후 격리 Read-back 1회
9. Phase 9: API 변경일 때 파일 기반 API 문서 동기화
10. Phase 10: Assumption Gate 후 PR 또는 hard push
11. Phase 11: `--reflect`일 때만 성찰
12. Phase 12: HTML 노트, Workflow Report(md), 이연 결정, 정리

세부 순서·판정·상한은 [build-phases.md](references/build-phases.md)가 canonical이다.

## 상태 코드

Phase 상태는 `DONE`, `IN_PROGRESS`, `PENDING`, `SKIPPED:{사유}`, `BLOCKED:{사유}`만 사용한다.
검증 판정은 `PASS/WARN/FAIL`이다. 다음 계약 상태를 보존한다.

- `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`, `BLOCKED:MAX_ITERATIONS`, `BLOCKED:BUILD_FAIL`
- `BLOCKED:DUPLICATE_IN_PROGRESS`
- `BLOCKED:NO_VALID_RED`, `BLOCKED:REGRESSION_AT_RED`, `BLOCKED:TEST_NOT_GREEN`
- `BLOCKED:AGENT_DIED`, `BLOCKED:ASSUMPTION_UNRESOLVED`
- `SKIPPED:PROFILE_EMPTY`, `SKIPPED:USER_OPT_OUT`, `SKIPPED:NO_TEST_BASIS`
- `SKIPPED:REFLECT_NOT_REQUESTED`, `SKIPPED:BUDGET_PRESERVED`, `SKIPPED:AGENT_DIED`
- Phase 12 feedback: `SKIPPED:NO_FEEDBACK_UPSTREAM` when `feedbackUpstreamRepo` is absent

`red_assertion`, `already_satisfied`, `cannot_compile`, `deferred_e2e`, `regression`,
`pre_existing`, `new_red`, `flaky`, `agent_retry`, `degraded_fallback`은 진단 데이터이며 Phase 상태가 아니다.

## Reference routing

- Build 상세: [build-phases.md](references/build-phases.md)
- Analyze/Verify: [analyze-verify-modes.md](references/analyze-verify-modes.md)
- TDD와 baseline: [tdd.md](references/tdd.md)
- Phase 8: [quality-loop.md](references/quality-loop.md)
- 위임 프롬프트: [agent-prompts.md](references/agent-prompts.md)
- 고정 토폴로지: [agent-topology.md](references/agent-topology.md)
- 상태·보고·HTML: [templates.md](references/templates.md)
