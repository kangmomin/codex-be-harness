> 이 문서는 `start-workflow` 스킬의 Phase 5(상태 파일·라이브 노트 생성)와 Phase 12(HTML 렌더링·최종 보고·보완점 적용)에서 로드된다. 단독 실행 금지.
> `{RUN_DIR}`, `{STATE_FILE}`, `{IMPL_NOTES}`, `{REPORT_DIR}` 등 플레이스홀더 정의는 SKILL.md 본문을 따른다.
> 상태와 노트는 실행별 `{RUN_DIR}` 안에 있으며 고정 임시 경로를 사용하지 않는다.

# 템플릿 모음

## Phase 5: 상태 파일 템플릿

Write tool로 `{STATE_FILE}`을 생성한다:

```markdown
# Workflow State

## Run
- run_dir: {RUN_DIR}
- project_root: {CWD}
- approved_at: {Phase 4.4 사용자 승인 시각}
- approved_effects: {branch / edits / commits / push / PR}

## Spec
[Technical Spec 전문 그대로 복사]

## Task Type
[생성/수정/검토/디버깅]

## Difficulty
[N]/10

## Current Phase
Phase 5 - 자율 실행 시작 (agent: Sol High orchestrator, model: gpt-5.6-sol, effort: high)

## Phase Assignments
| Phase | Agent | Model | Effort | Status |
|-------|-------|-------|--------|--------|
| 1 | Sol High orchestrator + Luna edge-case | gpt-5.6-sol / gpt-5.6-luna | high / xhigh | DONE |
| 2 | Sol High orchestrator | gpt-5.6-sol | high | DONE |
| 3 | Sol High orchestrator | gpt-5.6-sol | high | DONE |
| 4.2 | Luna reviewers + Sol High | gpt-5.6-luna / gpt-5.6-sol | xhigh / high | DONE |
| 4.3 | fresh Sol Max advisor | gpt-5.6-sol | max | DONE |
| 4.4 | Sol High approval relay | gpt-5.6-sol | high | DONE |
| 5 | Sol High orchestrator | gpt-5.6-sol | high | IN_PROGRESS |
| 6.1 | Terra executor | gpt-5.6-terra | high / max | PENDING |
| 6.2 | Terra executor | gpt-5.6-terra | high / max | PENDING |
| 7 | Sol High command + Terra fix | gpt-5.6-sol / gpt-5.6-terra | high / high-or-max | PENDING |
| 8 | Sol High barriers + Luna review + Terra single writer | gpt-5.6-sol / gpt-5.6-luna / gpt-5.6-terra | high / xhigh / high-or-max | PENDING |
| 9 | Terra documentation executor | gpt-5.6-terra | high / max | PENDING |
| 10 | Sol High Gate + Terra approved push/PR | gpt-5.6-sol / gpt-5.6-terra | high / high-or-max | PENDING |
| 11 | Luna reflection | gpt-5.6-luna | xhigh | PENDING |
| 12 | Sol High report + Terra approved remediation | gpt-5.6-sol / gpt-5.6-terra | high / high-or-max | PENDING |

## Remaining Phases
- Phase 6.1: 테스트 우선 (Red)
- Phase 6.2: 구현 (Green)
- Phase 7: 빌드 체크
- Phase 8: 품질 루프
- Phase 9: 문서 동기화
- Phase 10: PR / Push
- Phase 11: 성찰
- Phase 12: 최종 보고

## Execution Strategy
[sequential/parallel-slices]

## Acceptance Criteria
[Spec의 정상 흐름 표(`AC-nn`)를 그대로 복사. 없으면 `없음`. Phase 6.1 테스트 근거의 일부다]

## Edge Cases
[Spec의 엣지 케이스 표를 **ID·참조 구현 열까지 그대로** 복사. Phase 8.6 커버리지 대조와 Phase 8.8 Diff 판정의 기준이므로 ID를 생략하거나 다시 매기지 않는다]

## Test Baseline
[Phase 5에서 수집. TDD SKIP 시 사유만 기록 — 예: `SKIPPED:NO_TEST_COMMAND`]

- 커밋: {SHA}   |   수집 Phase: 5 (자율 실행 진입 전)   |   **불변 — 이후 갱신하지 않는다**

| suite | 명령 | 러너 완주 | 통과 | 실패 | 실패 목록 (식별자 :: 정규화 시그니처) |
|-------|------|----------|------|------|--------------------------------------|
| unit | {testCommand} | Y | 142 | 2 | `TestFoo` :: `nil pointer` / `TestBar` :: `want 3 got 2` |

**Tombstone** (Spec이 승인한 테스트 이름 변경·삭제만 기록. 대조 시 매핑에만 쓰고 위 판정 데이터는 바꾸지 않는다):
- `{구 식별자}` → `{신 식별자}` 또는 `삭제({근거})`

## TDD Test Map
[Phase 6.1에서 기록. Phase 8 회귀 대조와 Phase 12 보고서의 기준]
> **Phase 8.8 read-back 에이전트에 이 표를 전달하지 않는다** — Spec 역추론으로 격리가 무너진다.

| Spec ID | 테스트 | 파일 | Red | Green |
|---------|--------|------|-----|-------|
| AC-01 | Test_Create_정상 | user_test.go:12 | red_assertion | PASS |
| EC-01 | Test_Create_중복이메일 | user_test.go:42 | already_satisfied | PASS |
| EC-02 | — | — | deferred_e2e | - |

## Plan
[확정된 Plan 전문 그대로 복사]

## Plan Verification Log
[Phase 4.3 검증 루프의 Iteration Diff Log]

## Readback Diff
[Phase 8.8 결과. Phase 8.8 실행 전에는 `미실행`]

## Phase Results
[Phase 완료 시 아래 표에 행 append. `Status`는 상태 코드(8.2/8.3처럼 Phase Assignments에 개별 행이 없는 하위 단계도 여기에 기록).
`진단` 열은 발생 시에만 — `agent_retry({원인})` / `degraded_fallback({원인} / {축소 내용})`, 없으면 `-`]

| Phase | Status | 결과 요약 | 진단 |
|-------|--------|----------|------|
```

`parallel-slices`인 경우 아래를 추가한다:

```markdown
## Slices
[Plan에서 정의한 Slice 정보 그대로 복사]
```

`--reflect` 미지정 시(기본): 생성 시점에 Phase 11 행의 Status를 `SKIPPED:REFLECT_NOT_REQUESTED`로 기록하고, `Remaining Phases`에서 "Phase 11: 성찰"을 제외한다.

## Phase 5: Implementation Notes 라이브 파일 초기화

상태 파일과 별개로 `{IMPL_NOTES}`를 Write tool로 생성한다. 기존 파일이 있으면 덮어쓴다.

```markdown
# Implementation Notes — {작업 요약}

> 자율 실행 중 발생한 판단·편차·트레이드오프·미결 질문이 실시간으로 누적됩니다.
> 유저는 언제든 이 파일을 열어 비동기로 피드백할 수 있으며, Phase 12에서 HTML로 일괄 렌더링됩니다.

## 설계 결정
<!-- "- {Phase} | {file:line 또는 범위} — 선택: {택1} (대안: {택2}) — 근거: {1~2줄}" -->

## 편차
<!-- "- {Phase} | {file:line 또는 범위} — Spec: {원래 기대 동작} → 실제: {바뀐 동작} — 사유: {1~2줄}" — [Assumption] 보고와 1:1 대응 -->

## 트레이드오프
<!-- "- {Phase} | {결정} — 채택안: {A} / 기각안: {B,C} — 이유: {1~2줄}" -->

## 미결 질문
<!-- "- [ ] {Phase} | {질문} — 영향: {핵심 동작/주변 영향/판단 보류}" -->
```

> 4개 섹션 헤더(`## 설계 결정`, `## 편차`, `## 트레이드오프`, `## 미결 질문`)는 정확히 이 형태로 유지한다. Phase 12 HTML 렌더링이 헤더 텍스트로 섹션을 식별한다.

## Phase 12 실행 절차

> SKILL.md Phase 12의 "절차 요약" ①~⑤의 상세 규칙이다. 순서를 바꾸지 않는다.

1. **HTML 렌더링**: `{IMPL_NOTES}` → `{REPORT_DIR}/{YYYYMMDD}-{task-name-kebab}-impl-notes.html` (아래 템플릿 준수, 디렉토리 없으면 생성).
   그 다음 Phase 6~11 결과를 종합해 **Workflow Report**를 작성한다 (템플릿 준수 — 섹션 머리글 변경 금지). `## 미결 질문`이 1건 이상이면 보고서 최상단에 "사용자 확인 필요" 블록을 자동 삽입한다.
2. **TDD 미해결 항목 처리** (보고서 4.1 섹션이 비어있지 않을 때만): 자율 실행 중 이연된 `BLOCKED:*`·`[TestConflict]`·`[Breaking]`·`cannot_compile`을 각각 제시하고 결정을 받는다.
   Phase 6~8에서 유저 질문이 금지되어 이연된 항목들이므로 **여기가 첫 결정 지점**이다.
   - 결정에 따른 작업 트리 수정이 필요하면 Terra executor가 수행하고 Sol High가 승인·상태·commit 조정을 한다. 승인 전에는 수정하지 않는다.
   - "이번 범위 외" 판단 항목은 보고서에 `보류`로 남긴다.
3. **Read-back Diff 처리** (Phase 8.8 판정이 `WARN`/`FAIL`일 때만): 보고서 8번 섹션의 각 항목을 유저에게 제시하고 결정을 받는다.
   보완점 질문보다 **먼저** 처리한다 — 코드·Spec에 직접 영향을 주는 결정이기 때문이다.
   - 결정에 따른 코드/Spec 수정이 필요하면 Terra executor가 수행하고 Sol High가 승인·상태·commit 조정을 한다. 유저가 승인하기 전에는 수정하지 않는다 (Spec 외 변경 금지 원칙).
   - 유저가 "이번 범위 외"로 판단한 항목은 보고서에 `보류`로 남기고 넘어간다.
4. **보완점 적용** (Phase 11이 `DONE`일 때만): ① `.codex/be-harness/**` 로컬 저장 ② 건너뛰기 중
   결정받는다. 적용 절차·append 규칙은 아래 "보완점 적용 상세"를 따른다. 플러그인 원본은 절대
   수정하지 않는다. `feedbackUpstreamRepo`가 없으면 `SKIPPED:NO_FEEDBACK_UPSTREAM`을 기록하고,
   외부 feedback 제출은 첫 릴리스에서 수행하지 않는다.
   Phase 11이 `SKIPPED:*`면 이 단계를 건너뛰고 보고서 §6에 **실제 상태 코드**로 스킵 사유를 기입한다 (§6 템플릿의 사유별 분기 문구를 따른다).
5. **정리**: 상태 파일의 모든 Phase를 `DONE`/`SKIPPED:{사유}`로 갱신하고 `Remaining Phases`를 `없음`으로 기록.
   기본은 상태 파일과 라이브 노트를 **보관** (HTML 산출물은 `{REPORT_DIR}`에 영구 저장). 사용자가
   정리를 요청한 경우에만 `{RUN_DIR}`가 이번 실행의 검증된 임시 디렉터리인지 확인한 뒤 그 내부의
   `{STATE_FILE}`과 `{IMPL_NOTES}`를 삭제한다. 실행 중 시작한 서버 PID/세션도 모든 종료 경로에서 정리한다.
   HTML 산출물(`*-impl-notes.html`, `*-e2e-report.html`)은 자동 삭제하지 않는다.

Phase 12에서 사용자 승인 remediation으로 diff가 바뀌면 Sol High는 Phase 10 Assumption Gate와 Phase 4.4의
승인된 외부 효과 범위를 다시 확인한다. 필요한 작업 트리 수정과 승인된 push/PR은 Terra executor가 수행하고
Sol High는 승인·상태·commit 조정만 한다.

## Phase 12: Implementation Notes HTML 렌더링

보고서 작성 직전, 라이브 노트를 HTML 산출물로 변환한다.

1. **출력 디렉토리 보장**: `mkdir -p {REPORT_DIR}`
2. **출력 경로 결정**: `{REPORT_DIR}/{YYYYMMDD}-{task-name-kebab}-impl-notes.html`
   - `YYYYMMDD`: 현재 날짜 (Bash `date +%Y%m%d`)
   - `task-name-kebab`: Phase 5 브랜치명 또는 Spec 제목을 kebab-case로 변환
3. **렌더링**: `{IMPL_NOTES}`를 Read한 뒤, 4개 섹션을 각각 색상 카드로 변환하여 Write tool로 HTML 파일을 생성한다. 권장 템플릿:

```html
<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>Implementation Notes — {task}</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:880px;margin:32px auto;padding:0 16px;color:#222;line-height:1.55}
 h1{font-size:1.5rem;margin-bottom:.25rem}
 .meta{color:#666;font-size:.9rem;margin-bottom:1.5rem}
 section{border-left:4px solid;padding:12px 16px;margin:16px 0;border-radius:6px;background:#fafafa}
 section.decision{border-color:#2563eb}
 section.deviation{border-color:#ea580c}
 section.tradeoff{border-color:#16a34a}
 section.open{border-color:#dc2626}
 section h2{margin:0 0 8px;font-size:1.1rem}
 ul{margin:0;padding-left:1.2rem}
 .empty{color:#888;font-style:italic}
 .alert{background:#fef2f2;border:1px solid #fecaca;padding:12px 16px;border-radius:6px;margin-bottom:16px}
</style></head><body>
<h1>Implementation Notes — {task}</h1>
<div class="meta">생성: {ISO timestamp} · 브랜치: {branch} · 워크플로우: codex-be-harness/start-workflow</div>
{미결 질문이 1건 이상이면 아래 alert 블록 삽입}
<div class="alert"><strong>사용자 확인 필요</strong> — 미결 질문 {N}건이 있습니다. 아래 빨간 카드 참고.</div>
<section class="decision"><h2>설계 결정</h2>{ul 또는 empty}</section>
<section class="deviation"><h2>편차</h2>{ul 또는 empty}</section>
<section class="tradeoff"><h2>트레이드오프</h2>{ul 또는 empty}</section>
<section class="open"><h2>미결 질문</h2>{ul 또는 empty}</section>
</body></html>
```

> 각 섹션이 비어 있으면(헤더 외에 항목 없음) `<p class="empty">기록 없음</p>`로 표기한다.
> `## 미결 질문`의 체크박스(`- [ ]`)는 `<input type="checkbox" disabled>`로 변환해 시각적으로 유지한다.

4. **결과 경로를 메모**: Phase 12 보고서의 `Implementation Notes` 섹션에 절대 경로를 명시.

## Phase 12: Workflow Report 템플릿

```markdown
## Workflow Report

### 1. 작업 요약
- **작업 유형**: [생성/수정/검토/디버깅]
- **난이도**: [N]/10 (산정) → [M]/10 (체감)
- **PR**: [PR URL]

### 2. 구현 내역
- **변경 파일**: [N]개
- **커밋 수**: [N]개
- **핵심 로직**: [요약]

### 3. 요구사항 대응
| ID | 케이스 | 대응 방법 | Unit | E2E | Read-back |
|----|--------|----------|------|-----|-----------|
| AC-01 | [정상 흐름] | [대응] | PASS | PASS | 일치 |
| EC-01 | [케이스] | [대응] | PASS | PASS | 일치 |
| EC-02 | [케이스] | [대응] | deferred_e2e | `UNCOVERED:{사유}` | A 검증 누락 |

- `Unit` 열: Phase 6.1 TDD Test Map의 Green 결과 또는 진단 분류. TDD SKIP이면 `-`
- `E2E` 열: Phase 8.6 리포트의 해당 ID 판정. 미실행이면 `-`
- `Read-back` 열: Phase 8.8 Diff 유형(A~E) 또는 `일치`. Phase 8.8이 SKIP이면 `-`

### 4. 품질 루프 결과
| 단계 | 루프 횟수 | 수정 건수 |
|------|----------|----------|
| simplify | N | M |
| convention | N | M |
| e2e | N | M |
| scope-review | N | M |

**테스트 판정**: [PASS/WARN/FAIL] — regression [n]건 / new_red [n]건 / flaky [n]건 / pre_existing [n]건(범위 밖)

### 4.1 TDD 미해결 항목 (유저 결정 필요)
> TDD가 SKIP이거나 미해결 항목이 없으면 "없음"으로 적고 이 섹션을 비운다.

| 유형 | 항목 | 상세 | 필요한 결정 |
|------|------|------|------------|
| `BLOCKED:TEST_NOT_GREEN` | 품질 루프 3회 후에도 테스트 미통과 | [실패 목록] | 추가 수정 / 범위 제외 |
| `BLOCKED:NO_VALID_RED` | 유효 Red를 만들지 못함 | [사유] | 테스트 재작성 / TDD 없이 유지 |
| `BLOCKED:REGRESSION_AT_RED` | 테스트 추가만으로 기존 동작이 깨짐 | [테스트명] | 원인 조사 / 기존 테스트 수정 승인 |
| `[TestConflict]` | Spec 조항이 모호해 판정 보류 | [테스트 ↔ 조항] | Spec 확정 |
| `[Breaking]` | 기존 테스트의 기대 동작을 변경함 | [테스트명, 변경 내용] | 호환성 검토 |
| `cannot_compile` | 3회 시도 후 되돌린 테스트 | [Spec ID] | 수동 작성 / 범위 제외 |

**Read-back 판정**: [PASS/WARN/FAIL] — A [n]건 / C [n]건 / E [n]건 (소스: 테스트 파일 / E2E 리포트 / 구현 코드)

### 5. 문서 동기화
- API 문서 동기화: [Y/N/SKIPPED, 요약]

### 6. 성찰
[성찰 에이전트 결과. Phase 11이 `SKIPPED:*`면 "성찰 생략(`{실제 상태 코드}`)" 한 줄만 기입하고 사유별 안내를 덧붙인다 —
`REFLECT_NOT_REQUESTED`: "`--reflect`로 주기 실행 권장(워크플로우 5~10회마다 1회)" / 그 외(`BUDGET_PRESERVED`, `AGENT_DIED` 등): "§9 축소 실행 내역 참조"]

### 7. 보완점 (프로젝트 오버라이드로 반영)
> Phase 11이 `SKIPPED:*`면 표 대신 "없음 (성찰 생략)"으로 적는다.

| # | 대상 스킬/에이전트 | 보완 내용 | 저장 경로 | 적용 여부 |
|---|----------|----------|----------|----------|
| 1 | request 절차 | [내용] | `.codex/be-harness/skills/request.md` | Y/N |
| 2 | implementation 역할 | [내용] | `.codex/be-harness/agents/workflow-implementer.md` | Y/N |

### 8. Read-back Diff (유저 결정 필요)
> Phase 8.8이 SKIP이거나 판정이 PASS면 "없음"으로 적고 이 섹션을 비운다.

| 유형 | 항목 | Spec | 실제 보장 | 참조 구현 | 필요한 결정 |
|------|------|------|----------|----------|------------|
| C 기대값 불일치 | 중복 리뷰 (EC-05) | 400 | 409 | `order_handler.go:88` → 409 | 어느 쪽으로 통일할지 |
| A 검증 누락 | 일일 5회 제한 (EC-07) | 429 | 검증 없음 | - | 테스트 추가 / 범위 제외 |
| B Spec 밖 | body 길이 2000자 제한 | 없음 | 400 반환 | - | Spec에 반영 / 제거 |
| E 컨벤션 이탈 | `now == startAt` (EC-02) | 예정 | 예정 | `promotion.go:41` → 진행중 | 기존 컨벤션 따를지 |
| D 해석 불가 | `assert.Eventually` (`x_test.go:103`) | - | 불명 | - | 의도 확인 |

### 9. 축소 실행 내역
> `agent_retry`·`degraded_fallback`·`SKIPPED:BUDGET_PRESERVED`·`SKIPPED:AGENT_DIED`가 한 건도 없으면 "없음"으로 적고 이 섹션을 비운다.
> `Status`는 상태 코드, `진단`은 진단 분류 — 두 어휘를 한 열에 섞지 않는다.

| Phase | Status | 진단 | 원인·축소 내용 | 재실행 권장 |
|-------|--------|------|---------------|------------|
| 8.4 | DONE | `degraded_fallback` | 세션 한계 사망 ×2 — 오케스트레이터 직접 scope 검토 (독립성 상실) | Y — `start-workflow --verify` |
| 9 | SKIPPED:BUDGET_PRESERVED | - | 검증 예산 보존 | Y — 문서 동기화 별도 실행 |
```

## Phase 12: 보완점 적용 상세

플러그인 원본(`skills/...` 아래 파일)은 **절대 수정하지 않는다**. 첫 릴리스는 로컬 오버라이드
`.codex/be-harness/{common,skills,agents}/...`만 쓴다.

> "보완점 반영 방식을 선택하세요:
> 1. **로컬에만 저장** (기본값) — `.codex/be-harness/...` 에 append. 이 프로젝트에만 적용.
> 2. **건너뛰기** — 보고서만 출력하고 종료."

- 옵션 선택 후 각 보완점마다 Y/N 선택.
- profile의 `feedbackUpstreamRepo`가 없으면 Phase 결과에 `SKIPPED:NO_FEEDBACK_UPSTREAM`을 기록한다.
- 값이 있어도 upstream 제출 기능은 첫 릴리스에서 제공하지 않는다. 로컬 저장 결과와 이 제한을 보고한다.

### append 규칙

| 대상 | 경로 |
|------|------|
| 스킬 | `.codex/be-harness/skills/{skill-name}.md` |
| 에이전트 | `.codex/be-harness/agents/{agent-name}.md` |
| 공통 (여러 스킬에 적용) | `.codex/be-harness/common.md` |

파일이 없으면 새로 생성하고 frontmatter를 헤더로 넣는다:

```markdown
---
scope: skill:{name}          # 또는 agent:{name} / common
applies-to: codex-be-harness@{버전}+
updated: {YYYY-MM-DD}
---

# Project Override: {대상}

## 보완점 (auto-appended {YYYY-MM-DD HH:mm})
- [보완 내용 1]
- [보완 내용 2]
```

파일이 이미 있으면 기존 `## 보완점 (auto-appended ...)` 뒤에 새 섹션을 append (중복 판단은 내용 일치 여부로, 동일 내용이면 건너뜀).

추가 후 해당 파일 경로를 유저에게 보고한다:

> "프로젝트 오버라이드 업데이트 완료:
>  - `.codex/be-harness/skills/request.md` (+2줄)
>  - `.codex/be-harness/agents/workflow-implementer.md` (신규 생성)
> 다음 워크플로우 실행 시 자동으로 로드됩니다. Git에 커밋을 권장합니다."
