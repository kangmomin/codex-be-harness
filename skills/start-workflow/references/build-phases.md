> Build 모드의 Phase 1~12 순서, 게이트, 상한을 정의한다. 단독 실행하지 않는다.
> 플레이스홀더와 상태 어휘는 상위 `SKILL.md`가 canonical이다.

# Build Mode — Phase 1~12

## Planning-only boundary

Phase 1~4.4 동안 허용되는 것은 읽기 전용 탐색, 사용자 질문, Technical Spec과 Plan 작성뿐이다.
프로젝트 파일·git refs·원격 상태를 변경하지 않는다. Spec/Plan 초안은 대화에 유지하고, 실행별 상태
파일은 승인 후 Phase 5에서 만든다. 승인 전 임시 디렉터리를 만든 경우에도 코드나 git은 변경하지 않는다.

## Phase 1: 작업 범위와 Technical Spec

상세 Spec이 이미 제공되어 작업 유형, 대상 API/기능, 핵심 요구사항이 모두 명확하면 그것을 Technical
Spec으로 정리한다. 아니면 형제 `../../request/SKILL.md`를 읽고 **spec-only** 절차로 질문한다. standalone
request의 즉시 실행 규칙은 사용하지 않는다.

어느 경로든 기존 코드를 읽어 참조 구현을 찾고 다음을 포함한다.

- 작업 유형: 생성/수정/검토/디버깅
- 정상 흐름 `AC-nn`, 엣지 케이스 `EC-nn`, 디버깅 재현 `RC-nn`
- Request/Response, 비즈니스 규칙, DB/외부 의존, 호환성
- 각 엣지 케이스의 참조 구현 `file:line` 또는 `-`

엣지 케이스 보강이 필요하면 [agents/edge-case-analyzer.md](agents/edge-case-analyzer.md)를 읽고 API당 한
Luna xHigh 읽기 전용 역할에 `incremental` 모드로 전달한다. 고정 spawn은 `fork_turns:none`이며 질문은 역할이 사용자에게 직접 보내지 않고
오케스트레이터에게 반환한다.

Spec 전문을 사용자에게 보여주고 확인받는다. 불명확한 요구는 대안을 제시하고 결정받으며 임의로
확정하지 않는다.

### 중복 작업 스캔

Spec 확인 전에 같은 기능이 이미 진행 중인지 확인한다. 먼저 `{CURRENT_WORKTREE}`(`git rev-parse --show-toplevel`)와
`{CURRENT_BRANCH}`(`git branch --show-current`)를 확정한다.

- 후보 집합 = (`git worktree list --porcelain`에서 현재 경로가 아닌 worktree에 checkout된 브랜치) ∪
  (`gh pr list --state open --limit 100 --json headRefName,title,files`의 head 브랜치). 현재 브랜치와 그 PR은
  제외하고 브랜치명으로 dedupe한다. `gh`가 없거나 미인증이면 진단 한 줄을 남기고 계속한다.
- `git branch --list 'feat/*' 'codex/*'`는 ref 존재 확인에만 쓴다. worktree나 open PR에 연결되지 않은 단독
  로컬 브랜치는 후보가 아니다.
- **강 신호**: 후보의 변경 파일(`git diff --name-only {mainBranch}...{branch}` 또는 PR files)이 Spec 대상
  파일/엔드포인트와 교집합을 가진다 → 후보 목록을 보고하고 `BLOCKED:DUPLICATE_IN_PROGRESS`로 턴을 끝낸다.
  사용자가 계속을 지시하면 재개한다.
- **약 신호**: 브랜치/PR 제목의 키워드만 겹친다 → Phase 1 질문 1개(계속/중단)로 결정받는다.
- 신호 없음 → 진행. 스캔은 읽기 전용이며 어떤 mutation도 하지 않는다.

## Phase 2: 난이도와 검증 티어

> Phase 2 진입 시 MUST: 같은 폴더의 [verification-tier.md](verification-tier.md)를 읽고 A/B 점수표·게이트·금지 조건·light 축소 항목·승격 규칙을 따른다.

코드 복잡도 A와 영향 범위 리스크 B를 각각 1~10으로 산정하고 `max(A,B)`를 종합 난이도로 사용한다.
각 축 = 요소별 밴드 최댓값(평균 금지), 근거 없는 요소는 `UNKNOWN`(= 높음). B축 근거는 Spec `참조 구현`
경로로 `python3 {SKILL_DIR}/assets/risk_facts.py --paths {경로들} --report-dir {REPORT_DIR}`를 실행한
사실(존재·최근 변경 커밋 수·동반 테스트·과거 워크플로우 이력)로 뒷받침한다(스크립트 exit ≠ 0이면 해당 행 `UNKNOWN`).

**검증 티어**: A ≤ 3 ∧ B ≤ 3 ∧ 금지 조건 0건 ∧ TDD 활성(`--no-tdd` 미지정) ∧ 전략 ≠ parallel-slices ∧
`--tier standard` 미지정 → `light`(추가 리뷰 레이어·루프 상한·E2E 범위만 축소). 그 외 `standard`(기존 절차
무변경). 풀스택은 Phase 3에서 종료되므로 판정 대상이 아니다.

출력: `난이도: 코드 [A]/10 + 리스크 [B]/10 — [근거]` / `검증 티어: light|standard — A [a]/B [b], 금지 조건 [해당 없음|{항목}], [사유]`

## Phase 3: 실행 전략

기본은 `sequential`이다. 다음 5개를 모두 충족할 때만 2~3개 `parallel-slices`를 허용한다.

1. 각 슬라이스가 독립 endpoint/feature의 수직 슬라이스다.
2. 파일 소유권이 겹치지 않고 공유 DTO, middleware, DI wiring 변경이 없다.
3. 기존 테이블 변경이나 공통 계약 변경이 없다.
4. 슬라이스별로 빌드와 테스트가 가능하다.
5. 순서 의존이 없다.

FE와 BE 변경이 모두 필요하면 더 진행하지 않는다. 상태/보고에 다음을 포함하고 종료한다.

```text
상태: BLOCKED:FULLSTACK_HANDOFF_REQUIRED
FE 근거: 요청 조항, 후보 파일, 필요한 변경
BE 근거: 요청 조항, 후보 파일, 필요한 변경
영향 파일: 발견한 경로 목록
후속: fullstack 오케스트레이터로 handoff / BE-only로 범위 축소 / 종료
```

BE-only를 사용자가 선택하면 FE 조항과 파일을 Spec에서 제거하고 Phase 2부터 다시 산정한다. 이 첫
릴리스는 fullstack 실행을 자체 수행하지 않는다.

출력: `실행 전략: [sequential/parallel-slices] — [근거]`

## Phase 4: Plan과 리뷰

### Phase 4.1: Plan 작성

Spec 아래에 파일 단위 구현 순서, 각 변경, 최종 구조, 의존 관계, 위험, 테스트/검증을 추가해 하나의
Spec+Plan 산출물로 만든다. 중복 로직이 예상되면 최종 단순 구조를 여기서 확정한다.

`parallel-slices`면 `## Slices`에 제목·파일 범위·설명을 최대 3개로 적는다. 파일 범위가 겹치면
`sequential`로 되돌린다.

### Phase 4.2: 다관점 보강 1회

최대 3개 Luna xHigh 독립 리뷰어를 두 배치로 실행한다(standard). 모든 고정 spawn은 `fork_turns:none`이고,
모두 읽기 전용이며 Spec+Plan 전문을 받는다.

- Batch 1: 유지보수성, 성능, 엣지 케이스
- Batch 2: 데이터 정합성, 보안, 기존 코드 영향
- **light**: 배치 없이 Luna xHigh 읽기 전용 1역할(`fork_turns:none`)이 3관점(엣지 케이스 · 기존 코드 영향 · 더 단순한 경로)을 한 번에 리뷰한다.

반환 형식은 `Verdict: APPROVE|CONCERN|REJECT`, `Issues`, `Suggestions`다. REJECT는 Plan에 반영하고,
CONCERN은 근거가 타당한 항목만 반영한다. 결과를 Plan v1으로 고정한다.

### Phase 4.3: 독립 Plan 검증 루프

매 iteration `fork_turns:none`으로 새로 만든 Sol Max fresh-context advisor로 최대 `{PLAN_MAX}`회(standard 5 / light 2) 검증한다. 매회 Spec, Plan vN, 전략, 난이도 근거를 전달하고,
2회차부터 이전 diff와 기각 피드백/사유도 전달한다. 검토 관점은 Spec 추적성, 레이어 책임, 파일 소유권,
테스트 누락, 더 단순한 경로다.

매회 verdict, 반영, 기각 사유, Plan 변경 요약을 `Plan Verification Log` 초안에 누적한다.

| 조건 | 결과 |
|------|------|
| `APPROVE` | `PROCEED` 후 4.4 |
| 사용자 명시 중단 | `USER-INTERRUPTED`; 잔존 이슈 기록 후 4.4 가능 |
| 독립 리뷰 실행 불가 | `CODEX-UNAVAILABLE`; 사유 기록 후 4.4 가능(light면 승격 ⑤ → standard 기록 후 진행) |
| `{PLAN_MAX}`회 미승인 (light는 상한 평가 **전에** 승격 ① → `{PLAN_MAX}` = 5로 계속, iteration·동일 이슈 카운터 승계) | `BLOCKED:MAX_ITERATIONS`; 현재 Plan 진행/카운터·동일 이슈 횟수를 유지한 채 유효 상한만 `현재 iteration + 5`로 확장(`{PLAN_MAX}` 값 불변)/종료 결정 |

카운터는 티어와 무관한 단조 증가값이며 승격으로 초기화하지 않는다. 순서는 항상 `iteration 카운터 증가 → 승격 판정(latch) → 새 상한 조회 → 종료 조건·상한 판정`이다(Phase 8 루프도 동일 — [quality-loop.md](quality-loop.md)).

동일 이슈가 3회 반복되면 사용자 판단을 받는다. 반영·기각·변경이 모두 0건인 iteration은 즉시
중단해 무한 반복을 막는다.

### Phase 4.4: 명시적 실행 승인

Plan 모드 전환 명령에 의존하지 않는다. Plan의 파일 목록으로 금지 조건을 재점검한다(발견 시 즉시 standard).
티어 판정을 Plan과 함께 승인받는다. 아래 승인 블록을 사용자에게 보여주고 명시적 승인을 받는다.

```markdown
## 실행 승인 요청
- 확정 Spec/Plan: [요약과 잔존 이슈]
- 미해소 [Assumption]: [Spec의 [Assumption] 목록 또는 없음 — Phase 5에서 구현 노트 `## 편차`로 이월되고 Phase 10 Gate가 검사한다]
- 예상 변경 파일: [목록]
- 검증 티어: [light|standard] — 금지 조건 재점검 [해당 없음|{항목}]
- 브랜치: [생성할 이름 / --hard로 현재 브랜치 유지]
- 로컬 변경: 코드·테스트·문서 편집, 논리 단위 커밋
- 외부 변경: [일반 모드] push + draft PR / [--hard] 현재 브랜치 push, PR 없음
- 자동 구간: Phase 6~11; Assumption Gate에 걸리면 push/PR 보류

이 Plan과 부작용으로 실행을 시작해도 될까요?
```

승인 거부/수정 요청은 Phase 1~4 안에서 처리한다. **승인 전에는 Phase 5의 브랜치·파일·커밋 동작을
하나도 수행하지 않는다.** 승인 후 `Plan Verification Summary`(iterations, convergence, 잔존 이슈)를
확정한다.

## Phase 5: 브랜치, 상태, baseline

승인 직후 시작한다.

- 일반 모드: 현재 브랜치가 `feat/**`/`hotfix/**`가 아니면 profile prefix로 feature 브랜치를 만든다.
  보호 브랜치에 직접 커밋하지 않는다.
- `--hard`: 브랜치를 만들지 않고 현재 브랜치를 사용한다.
- `RUN_ID`·`START_SHA`를 [templates.md](templates.md)의 bash로 1회 계산한다(재생성 금지).
- 초기 생성 Write는 [templates.md](templates.md) 앵커 안 템플릿 전체 — `## Flags`(`SCHEMA: 2`, MODE·HARD_MODE·TDD·REFLECT·TIER·RUN_ID·START_SHA), `## Profile Snapshot`(Pre-flight 확정값 22키 + `profile_path`·`profile_sha256`·`resolved_report_dir`·`resolved_e2e_lock_dir`), `## Verification Tier`(Phase 2 판정·승격 이력)를 반드시 함께 포함한다. `## Test Baseline`은 초기 템플릿에 없다. 이어서 같은 문서의 Implementation Notes 템플릿을 `{IMPL_NOTES}`에 생성한다. Spec에 `[Assumption]`이 있으면 각 항목을 `{IMPL_NOTES}` `## 편차`에 태그 그대로 이월한다(없으면 섹션은 비워 둔다).
- [tdd.md](tdd.md)의 적용 판정과 baseline 수집을 수행한다.
- 수집(또는 SKIP 판정) 직후 `## Test Baseline` 블록을 `## TDD Test Map` 앞에 정확히 1회 삽입한다(완전성 canonical: [tdd.md](tdd.md) Phase 5).

baseline 수집 실패는 자율 구간 전 마지막 결정 지점이다. 회귀 판정 저하를 감수하고 진행, 중단,
`--no-tdd` 전환 중 결정받는다. 진행을 택하면 `수집 실패 — regression 판정 불가`를 기록하고, light면 승격 ④로 standard 전환을 `## Verification Tier`와 진단 `tier_escalated(④)`에 기록한다.

순서는 상태 파일 생성 → `{IMPL_NOTES}` → TDD 판정·baseline 수집 → `## Test Baseline` 삽입이며, 이 절이 끝나기 전 중단은 Phase 5 미완 재개([tdd.md](tdd.md))다.

## Phase 6: TDD 구현

[tdd.md](tdd.md)와 [agent-prompts.md](agent-prompts.md)를 읽는다.

### Phase 6.1: Red

TDD가 활성일 때만 `AC-nn`/`EC-nn`/`RC-nn` 근거의 실패 테스트와 최소 스텁을 작성한다. 형제
`../../unit-test/SKILL.md`의 Red 절차를 읽어 적용한다(profile 값은 envelope의 `## Profile Snapshot`, 재독 없음).

- sequential: Terra executor 테스트 작성자 1명, 커밋 조정과 상태 기록은 Sol High 소유
- parallel-slices: Terra executor 각 작성자는 자기 테스트/스텁만 편집하고 실행·상태 기록·커밋하지 않는다.
  모두 끝난 뒤 오케스트레이터가 전역 Red 검증과 단일 커밋을 수행한다.

| 결과 | 상태/진행 |
|------|-----------|
| 모든 ID가 `red_assertion`/`already_satisfied`/`deferred_e2e` | `DONE` → 6.2 |
| 일부 `cannot_compile` | `DONE`; 해당 ID 제외 후 6.2 |
| 전체 `cannot_compile` | `BLOCKED:NO_VALID_RED`; TDD 생략 후 6.2 |
| baseline 밖 기존 테스트 실패 | `BLOCKED:REGRESSION_AT_RED`; 기록 후 6.2 |

Red 커밋은 `Test: {요약} — 실패 테스트 선작성 (Red)`다. pre-commit이 실패 테스트를 거부하면 Red
커밋을 생략하고 Green과 합친다.

### Phase 6.2: Green

- sequential: Terra executor implementer가 Plan 순서대로 구현하고 구조화 결과를 반환한다. Sol High가 논리 단위 커밋을 조정한다.
- parallel-slices: 파일 범위를 겹치지 않게 Terra executor에 배정하고 각 작성자는 커밋·빌드를 하지 않는다.
  오케스트레이터가 결과를 대조한 뒤 한 번 커밋한다.

TDD 활성 시 테스트 파일 수정은 금지한다. 테스트가 잘못됐다고 판단하면 `[TestConflict]`만 보고하고
[tdd.md](tdd.md)의 오케스트레이터 판정을 따른다.

완료 직후 **승격 ② 평가**(`START_SHA` 기준 변경 소스 파일 > 3 또는 금지 조건 발견 — [verification-tier.md](verification-tier.md) §4 집계 규칙) → light면 standard 전환을 `## Verification Tier` 승격 이력과 `Phase Results` 진단 `tier_escalated(②)`로 기록하고 Phase 7로.

## Phase 7: 빌드 강제 검증

`buildCommand`가 없으면 `SKIPPED:PROFILE_EMPTY`다. 있으면 Sol High가 구현 직후 실행한다. 실패할 때마다
Terra executor build-fix가 원인 범위만 수정하고 결과를 반환한 후 Sol High가 다시 실행한다. 총 3회 실패하면
`BLOCKED:BUILD_FAIL`로 중단하고 오류를 보고한다.

## Phase 8: 품질 루프

[quality-loop.md](quality-loop.md)가 canonical이다. 최대 `{QL_MAX}`회(standard 3 / light 2) 동안 읽기 전용 병렬 스캔 → 단일 작성자
통합 수정 → E2E/통합 테스트 순으로 수행한다. 종료 조건은 `modified == false`와 테스트 `PASS`다.
TDD가 생략됐으면 수정 0건만으로 종료할 수 있다. `{QL_MAX}`회 뒤에도 green이 아니면
`BLOCKED:TEST_NOT_GREEN`을 기록하되 Phase 8.8 이후를 계속한다.

**light**: 8.2 = `SKIPPED:TIER_LIGHT`(Luna 통합 스캔을 convention만으로 실행), 8.6 = `e2e-test-loop --smoke`,
8.8 = `SKIPPED:TIER_LIGHT`. 승격 ③(8.1 회귀·판정 불가)·⑥(8.6 BLOCKED 또는 `full(smoke 미적용)`)·⑦(iteration 종료 시 재집계)은
[verification-tier.md](verification-tier.md) §4 — 티어 전환은 종료 조건·상한 평가보다 **먼저** 적용하고, ⑥·⑦은 standard iteration을 최소 1회 추가한다. 상세는 [quality-loop.md](quality-loop.md).

루프 밖에서 격리된 Phase 8.8 Read-back을 정확히 한 번 실행한다(light: `SKIPPED:TIER_LIGHT` — 승격됐다면 실행). `FAIL`이어도 수정하지 않고 Phase
12 결정으로 이연한다.

## Phase 9: API 문서

작업 유형이 API 생성/수정/삭제이고 `apiDocsPath`가 실제 파일일 때만 Terra executor가 문서 파일을 외과적으로
동기화하고 결과를 반환한다. Sol High는 상태만 기록한다. 외부 플랫폼으로 push하지 않는다. 아니면 구체적인 `SKIPPED:{사유}`를 기록한다.

## Phase 10: Assumption Gate와 PR/push

진입 직전 light면 승격 ⑦ 재평가([verification-tier.md](verification-tier.md) §4) — 발화 시 Phase 8을 standard 루프로 1회 재진입(카운터 0부터, `{QL_MAX}` = 3, 이력 `⑦: Phase 8 재진입`)한 뒤 돌아온다.

base diff의 추가 라인, 미push 커밋 본문, `{IMPL_NOTES}`의 `## 편차`에서 `[Assumption]`을 검색한다. 하나라도 있으면 push/PR을
금지하고 `BLOCKED:ASSUMPTION_UNRESOLVED`와 위치 목록을 기록한 뒤 Phase 11~12로 간다. 사용자가
결정하고 태그가 제거된 후 Phase 10만 재실행한다.

`Phase Results`의 최신 8.6 행이 `BLOCKED:LOCK_UNAVAILABLE`이면(다른 검사가 green이어도) push/PR 전에
`USER_INPUT_REQUIRED: {질문}` relay로 세 선택지를 받는다 — (1) `락 재시도`: 마지막 8.6과 같은 인자로 형제
`../../e2e-test-loop/SKILL.md` 절차를 1회 재실행하고 `Phase Results`에 8.6 행을 append(최신 8.6 행이 Gate 기준)·
`## Artifacts` `e2e-report:`를 갱신한다. Gate-local 재시도이므로 승격 ⑥은 적용하지 않는다. 결과 분기: 다시
`BLOCKED:LOCK_UNAVAILABLE` → 재질문 / `수정: N` ∧ `DONE`·`WARN` → 행·Artifacts 갱신만 하고 Phase 10 복귀 /
`수정: Y`(결과 코드 무관 — diff가 바뀜) → Phase 7 → 새 standard Phase 8 루프(⑦ 재진입과 동일: 카운터 0부터,
`{QL_MAX}` = 3, `Phase Results`에 재진입 사유 `락 재시도 후 수정` 기록, 8.8·Phase 10 진입 검사 갱신) → Phase 9
재판정(기존 규칙대로 실행 또는 SKIP) → Phase 10 복귀 / `수정: N` ∧ 그 외 `BLOCKED:*`(`MAX_ITERATIONS`·
`NO_PROGRESS`) → 기존 규칙대로(진행을 막지 않고 Phase 12 결정으로 이연) Gate 재판정. (2) `E2E 없이 진행`:
즉시 `{STATE_FILE}` `## Final Decisions`에 `| E2E 미실행 승인 | BLOCKED:LOCK_UNAVAILABLE — E2E 없이 진행 | {시각} |`을
기록하고 Phase 10만 재실행한다(Assumption Gate의 "결정 후 Phase 10만 재실행" 패턴). 이후 Gate 재진입(Phase 12
remediation 뒤 포함)은 이 결정을 재사용해 자동 재질문하지 않는다(사용자가 명시적으로 `락 재시도`를 지시하면
승인을 override해 재시도 경로로 진입). 승인 행은 최신 8.6 행이 `BLOCKED:LOCK_UNAVAILABLE`인 동안만 유효하며,
재시도로 8.6이 `DONE`이 되면 `SUPERSEDED`로 취급한다. Workflow Report §4 `- **E2E**:`는 항상 최신 8.6 행을
우선하고 미실행 승인 문구는 승인이 유효할 때만 렌더링한다. (3) `중단`: 워크플로우를
`BLOCKED:LOCK_UNAVAILABLE`로 종료한다.

- 일반 모드: 형제 `../../commit-pr/SKILL.md`를 읽고 논리 커밋, base/branch 결정, VERSION patch bump,
  기존 PR 처리, 일반 push, draft PR을 수행한다. PR URL은 필수 결과다.
- `--hard`: 형제 `../../commit-hard-push/SKILL.md`의 Assumption Gate와 일반 push 절차를 읽고 현재
  브랜치에 push한다. PR은 만들지 않는다.

Phase 4.4에서 승인되지 않은 원격 효과가 새로 필요하면 여기서 멈춰 추가 승인을 받는다. 승인된 push/PR의 실제 실행은 Terra executor가 한다.

## Phase 11: 성찰

`--reflect`일 때만 Luna xHigh [agents/workflow-reflection.md](agents/workflow-reflection.md) 역할로 커밋 로그와 Phase
결과를 분석한다. 아니면 `SKIPPED:REFLECT_NOT_REQUESTED`다. 보완점은 plugin 원본이 아니라
`.codex/be-harness/**` 후보로만 제안한다.

## Phase 12: 최종 보고

[templates.md](templates.md)의 순서를 바꾸지 않는다.

1. 슬림 Workflow Report를 `{WORK_REPORT}`에 1회 Write(채팅에는 경로·§1·유저 결정 항목만)
2. TDD 미해결 항목 결정
3. Read-back Diff 결정
4. Phase 11이 DONE이면 보완점의 로컬 저장 여부 결정
   2~4의 결정은 받는 즉시 `## Final Decisions`에 기록한다(재개 시 재질문 금지).
5. 상태 마감 **후** `{SKILL_DIR}/assets/workflow_archive.py`로 `{REPORT_DIR}`에 md 아카이브(`*-workflow-report.md`) 1회 배타 생성(부록 A 실행 요약 / B 상태 파일 전문 / C Implementation Notes), stdout `경로:`/`상태:`를 `## Artifacts`에 기록하고 경로 보고 — 재렌더링 없음

전역 보고 양식이 따로 있어도 Workflow Report의 섹션 머리글(§1~§9)은 바꾸지 않는다.

`feedbackUpstreamRepo`가 없으므로 첫 릴리스는 feedback PR을 만들지 않고
`SKIPPED:NO_FEEDBACK_UPSTREAM`을 기록한다. 값이 있더라도 Phase 4.4 승인 범위를 벗어난 외부 제출은
별도 승인을 받는다. 실행 중 띄운 서버가 남아 있지 않은지 확인하고 PID/세션 핸들을 정리한다.

Phase 12의 사용자 승인 remediation이 작업 트리 diff를 바꾸면, Sol High는 Phase 10 Assumption Gate와
Phase 4.4에서 승인된 push/PR 범위를 다시 확인한다. 재확인 뒤 필요한 수정 또는 승인된 외부 효과는 Terra
executor만 수행한다.
