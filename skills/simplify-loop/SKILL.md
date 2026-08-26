---
name: simplify-loop
description: "변경 코드의 동작을 보존하는 단순화 후보를 네 관점으로 독립 리뷰하고 최대 10회까지 수렴시킨다. 구현 직후 코드 정리, '심플리파이 돌려줘', '코드 간소화' 요청과 start-workflow 품질 루프에서 사용한다."
---

> **Project Overrides**: 실행 전 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/simplify-loop.md`를 읽는다.
> 존재하면 추가 규칙/예외로 흡수하고 충돌 시 오버라이드가 우선한다. 상세 규약: 플러그인 루트 `OVERRIDES.md`.

# Simplify Loop

변경된 코드에서 동작 보존 단순화 후보를 찾고, Correctness / Readability / Performance / Stability 독립 리뷰와 Devil's Advocate, Arbiter, 단일 writer를 거쳐 수렴할 때까지 반복한다. 반복·중복 제거·재시도·종료 판정은 오케스트레이터가 [상태 머신 규약](references/workflow-script.md)에 따라 직접 관리한다.

기본값:

- `{MAX_ITER}` = 10
- `{CANDIDATE_CAP}` = 8
- `{RETRY_LIMIT}` = 1

핵심 상태 `seen`, `pendingRetry`, `holds`, `noProgressStreak`는 한 실행 동안 유지하며 iteration 사이에 초기화하지 않는다. 전체 필드와 전이는 reference가 정의한다.

## Flags

| 플래그 | 효과 |
|--------|------|
| `--dry-run` | 스캔을 한 번만 수행해 후보를 보고하고 파일은 수정하지 않는다. 상위 호출자가 dry-run 관점을 지시한 경우도 동일하다. |
| `--max-iter N` | `{MAX_ITER}`를 양의 정수 N으로 재정의한다. 유효하지 않으면 기본값 10을 유지한다. |

## Phase 1: 범위 판별

git 저장소 안에서 다음 순서로 `{DIFF_CMD}`를 확정한다.

1. `git status --porcelain`이 비어 있지 않으면 `git diff HEAD`를 사용한다.
2. clean이면 profile의 `mainBranch`(`origin/{mainBranch}` → `{mainBranch}`), 없으면 `origin/main`, `main` 순으로 기준 브랜치를 탐색하고 `git diff $(git merge-base {기준브랜치} HEAD)`를 사용한다. 커밋 범위 `base..HEAD`는 쓰지 않는다. 루프가 적용한 작업 트리 변경이 다음 스캔에 포함되어야 하기 때문이다.
3. 기준 ref를 해석하지 못하면 대화형 실행에서는 비교 ref를 한 번 요청한다. ref를 받지 못하거나 비대화형 실행이면 `SKIPPED:BASE_REF_UNRESOLVED`로 종료한다.
4. diff가 비어 있으면 `SKIPPED:NO_CHANGES`로 종료한다. dry-run에서는 `후보: 0건`도 함께 출력한다.

`{DIFF_CMD}`는 변경 범위 식별 전용이다. 후보의 `current`는 반드시 작업 트리의 실제 파일에서 읽는다.

## Phase 2: 실행 규약 로드

[상태 머신 규약](references/workflow-script.md)을 반드시 끝까지 읽고 `{DIFF_CMD}`, `{MAX_ITER}`, `{CANDIDATE_CAP}`, `{RETRY_LIMIT}`, 저장소 절대 경로를 입력으로 사용한다.

- 일반 실행: 규약의 상태를 실행 컨텍스트에서 유지하며 최대 `{MAX_ITER}`회 반복한다.
- dry-run: 빈 `seen`으로 Scan 한 번만 실행하고 후보를 중요도 순 최대 `{CANDIDATE_CAP}`건 보고한 뒤 종료한다. 리뷰 서브에이전트와 writer를 만들지 않는다.
- 여러 리뷰를 위임할 수 없는 환경에서는 네 관점을 한 컨텍스트에서 순차 평가하되 이를 `degraded_review`로 명시한다. DA, Arbiter, 단일 writer 순서와 상태 전이는 생략하지 않는다.

dry-run 출력:

```text
후보: {N}건
- {file}:{line} — {summary} / 제안: {proposed 한 줄 요약} / 근거: {rationale}
```

## Phase 3: 결과 처리

상태 머신의 반환값 `{ status, iterations, applied[], rejected[], holds[], failed[], iterLog[], note }`를 아래 형식으로 렌더링한다.

- `총 수정 횟수`는 `applied.length`다.
- `failed[]` 또는 `holds[]`가 비어 있지 않으면 status가 `DONE`이어도 경고 섹션을 포함한다.
- `FAIL`이며 note에 `적용 내역 미확인`이 있으면 현재 `git diff`를 함께 보여 주고 수동 대조가 필요함을 알린다.
- `holds[]`는 자동 적용하지 않는다. 대화형 실행에서만 현재 스니펫을 다시 확인한 뒤 개별 적용할지 물을 수 있으며, 응답이 없거나 비대화형이면 미적용 상태를 유지한다.

## 종료 조건

| 조건 | 결과 |
|------|------|
| 신규 후보 없음 + `pendingRetry` 소진 + 리뷰 미완결 아님 | `DONE` |
| `{MAX_ITER}`까지 수렴하지 못함 | `BLOCKED:MAX_ITERATIONS` |
| 승인 후보가 STALE을 제외하고 2회 연속 전부 적용 실패 | `BLOCKED:NO_PROGRESS` |
| 적용 0건이고 보류가 1건 이상이며 모두 `REVIEWER_FAILURE`, `ARBITER_FAILURE`, `MISSING_VERDICT` 계열 | `BLOCKED:REVIEW_INCOMPLETE` |
| 변경 코드 없음 | `SKIPPED:NO_CHANGES` |
| 기준 ref 미해결 | `SKIPPED:BASE_REF_UNRESOLVED` |
| Scan 재시도 실패 또는 적용 결과 화해 실패 | `FAIL` |

차단 상태에서는 자동으로 상한을 늘리거나 실패 후보를 적용하지 않는다. `MAX_ITERATIONS`는 상한을 높여 재실행하거나 현재 결과로 종료, `NO_PROGRESS`는 실패 목록을 수동 검토하거나 제외 후 종료, `REVIEW_INCOMPLETE`는 재실행하거나 현재 결과로 종료하는 선택지를 제공한다.

## 출력 형식

```text
Simplify Loop 완료
- 총 iteration: {N}회
- 총 수정 횟수: {M}회
- 상태: {status}

## Simplify Review Report
| # | 파일 | 요약 | Correctness | Readability | Performance | Stability | 판정 |
|---|------|------|-------------|-------------|-------------|-----------|------|
| {id} | {file}:{line} | {summary} | {V(C)} | {V(C)} | {V(C)} | {V(C)} | {decision} |

### Devil's Advocate / Arbiter (만장일치 후보만)
- {id}: 반론 강도 {strength} → Arbiter {verdict} — {reasoning 요약}

### 미적용 보류 목록 (holds)
- {id} {file}:{line} — {summary} / 사유: {reason}

### 경고 (failed/holds 존재 시 필수)
- {실패·보류 요약 및 후속 안내}
```

## References

- 일반 실행과 dry-run 모두 [references/workflow-script.md](references/workflow-script.md)를 읽는다. 이 파일이 후보 계약, 네 관점 프롬프트, 상태 필드와 전이의 canonical 정의다.
