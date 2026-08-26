# simplify-loop Codex State Machine

이 문서는 `simplify-loop`의 Codex 네이티브 실행 규약이다. 별도 런타임에 전달하거나 단독 실행하지 않는다. 오케스트레이터가 상태를 소유하고, 리뷰 서브에이전트는 읽기 전용이며, 승인 변경은 writer 한 명만 순차 적용한다.

## 입력과 반환 계약

필수 입력:

| 키 | 타입 | 의미 |
|----|------|------|
| `diffCommand` | string | 범위 식별 전용 diff 명령 |
| `maxIterations` | positive integer | 반복 상한, 기본 10 |
| `candidateCap` | positive integer | iteration당 후보 상한, 기본 8 |
| `retryLimit` | non-negative integer | 인프라 실패·재제안 허용 횟수, 기본 1 |
| `repositoryRoot` | absolute path | 모든 서브에이전트가 사용할 작업 루트 |

반환값은 다음 필드를 모두 가진다.

```text
{ status, iterations, applied[], rejected[], holds[], failed[], iterLog[], note }
```

`status`는 `DONE`, `BLOCKED:MAX_ITERATIONS`, `BLOCKED:NO_PROGRESS`, `BLOCKED:REVIEW_INCOMPLETE`, `FAIL` 중 하나다. Phase 1의 조기 종료 코드는 `SKIPPED:NO_CHANGES`, `SKIPPED:BASE_REF_UNRESOLVED`다.

## 후보와 키

Scan 후보는 다음 필드를 가진다.

```text
file, line, summary, current, proposed, rationale,
matchedSeenId?, revisesId?
```

- `file`은 저장소 루트 기준 상대 경로다.
- `current`는 diff가 아니라 실제 작업 트리에서 읽은 정확한 스니펫이다.
- `contentKey = file + "#" + stableHash(normalizeWhitespace(current))`
- `proposedKey = file + "#" + stableHash(normalizeWhitespace(proposed))`
- stableHash 구현은 실행 중 하나를 정해 계속 동일하게 사용한다. 해시가 없으면 정규화 문자열 자체를 키로 사용해도 된다.

## 상태

반복 시작 전에 아래 상태를 초기화한다. 실행 중 상태를 임의로 재구성하거나 iteration 사이에 버리지 않는다.

```text
seen: contentKey -> {
  id, file, line, summaryLine, disposition, retryCount, contentKey, proposedKey
}
pendingRetry: [{ candidate, reason }]
applied: []
rejected: []
holds: []
failed: []
iterLog: []
iterations: 0
converged: false
noProgressStreak: 0
candidateSequence: 0
exitStatus: null
exitNote: null
```

`seen.disposition`은 `APPLIED`, `REJECTED`, `SUGGESTION`, `HOLD`, `FAILED`, `STALE`, `RECONSIDER` 중 하나다. `pendingRetry`는 `seen`과 별도이며 Scan에 `PENDING`으로 노출한다.

## 역할 계약

모든 서브에이전트에 `repositoryRoot`, diff 명령, 후보 ID와 필요한 후보 데이터만 전달한다. 리뷰 역할은 파일을 수정하거나 다른 리뷰 결과를 읽지 않는다.

### Scan

다음 기준으로 후보를 찾는다.

- `diffCommand`로 변경 파일과 영역만 식별하고 `current`는 작업 트리 파일에서 다시 읽는다.
- 중복 코드, 불필요한 추상화, 죽은 코드, 더 단순한 동등 표현만 제안한다.
- 기존 동작을 완전히 보존해야 하며 기능 추가, 동작 변경, 스타일 취향, 무관한 범위 리팩터링은 제외한다.
- 전체 발견 수를 `totalFound`에 기록하고 중요도 순 최대 `candidateCap`건을 반환한다.
- `seen`과 `pendingRetry` 요약을 받고 다음 disposition 규칙을 지킨다.
  - `APPLIED`, `REJECTED`, `SUGGESTION`, `HOLD`, `FAILED`, `PENDING`은 재제안하지 않는다.
  - `STALE` 재제안은 `matchedSeenId`를 지정한다.
  - `RECONSIDER` 수정안은 `revisesId`를 지정하고 기존 기각 사유를 반영한다.

반환 형식: `{ diffEmpty: boolean, totalFound: integer, candidates: [...] }`. 결과가 없으면 같은 조건으로 한 번만 재시도하고, 다시 실패하면 `FAIL`, note=`스캔 에이전트 재시도 후에도 실패 — 수렴 미확인`으로 종료한다.

### 네 관점 독립 리뷰

동일한 batch에 대해 네 서브에이전트를 가능하면 동시에 실행한다. 동시 슬롯이 네 개보다 적으면 여러 batch로 나누되 각 관점은 fresh context에서 실행하며, 완료된 verdict를 아직 실행하지 않은 리뷰어에게 전달하지 않는다. 각 에이전트는 다른 판정을 보지 않고 모든 candidate ID에 정확히 한 verdict를 반환한다.

| 관점 | 핵심 질문 |
|------|-----------|
| Correctness | 기존 동작을 완전히 보존하며 엣지 케이스 누락이 없는가? |
| Readability | 실제로 더 읽기 쉽고 팀 컨벤션에 맞는가? |
| Performance | 성능 저하 없이 동일하거나 더 나은 효율인가? |
| Stability | blast radius와 의존 코드 영향이 허용 가능한가? |

각 판정: `{ candidateId, verdict: CHANGE|KEEP|CONDITIONAL, confidence: High|Medium|Low, rationale, risks }`. 확신 부족은 `CONDITIONAL`이다.

리뷰 역할 하나라도 최초 호출과 한 번의 재시도 모두 응답하지 않으면 batch 전원을 적용하지 않고 `pendingRetry`로 보낸다(`REVIEWER_FAILURE`). 네 결과는 왔지만 특정 후보 verdict가 누락되면 해당 후보만 `MISSING_VERDICT`로 보낸다.

### Devil's Advocate

네 관점이 모두 `CHANGE`인 후보만 받는다. 후보마다 반드시 다음을 반환한다.

```text
candidateId, reasonsToKeep, riskScenario, alternative,
strength: Strong|Moderate|Weak
```

형식적인 무반론은 허용하지 않는다. 현재 코드의 숨은 의도, 실제 위험 시나리오, 전면 변경보다 나은 대안을 각각 검토한다.

### Arbiter

Devil's Advocate가 끝난 뒤 별도의 읽기 전용 서브에이전트가 찬성 근거와 반론을 함께 평가한다. 구체성, 재현 가능성, 비용 대비 이점으로 판정하고 `{ candidateId, verdict, reasoning, action }`을 반환한다.

- `PROCEED`: 변경 진행
- `RECONSIDER`: 수정 제안만 다음 Scan에서 한 번 재제안 가능
- `HOLD`: 자동 적용하지 않고 사용자 판단에 맡김

DA 또는 Arbiter 결과가 누락되면 `ARBITER_FAILURE`로 `pendingRetry`에 보낸다.

### 단일 writer와 화해

한 iteration의 승인 후보 전체를 writer 한 명에게 넘겨 후보 순서대로 적용한다. 다른 역할은 파일을 수정하지 않는다.

1. 파일을 다시 읽어 `current`가 정확히 일치하는지 확인한다.
2. 불일치하면 수정하지 않고 `STALE`을 반환한다.
3. 일치하면 `current`에서 `proposed`로 필요한 부분만 수정한다.
4. 결과는 후보마다 `APPLIED`, `FAILED`, `STALE`과 실패 reason을 반환한다.

writer가 결과 없이 종료하면 새 읽기 전용 화해 에이전트가 파일 내용을 확인한다.

- `proposed`가 존재하고 `current`가 사라짐: `APPLIED`
- `current`가 그대로 존재: `FAILED`
- 둘 다 아님: `STALE`

화해도 실패하면 즉시 `FAIL`, note=`적용 내역 미확인 — git diff 수동 검토 필요`로 종료한다.

## 반복 전이

`while !converged && !exitStatus && iterations < maxIterations`를 다음 순서로 수행한다.

### 1. Scan과 필터

1. `iterations`를 증가시키고 Scan을 실행한다.
2. 두 번째 iteration 이후 `diffEmpty=true`이고 `pendingRetry`가 비어 있으면 수렴한다.
3. 반환 후보마다 순번 ID를 부여하고 키를 계산한다.
4. `revisesId`는 해당 `RECONSIDER`, `matchedSeenId`는 해당 `STALE` entry일 때만 링크한다. 명시 링크가 없으면 다음 auto-link만 허용한다.
   - STALE: `proposedKey` 동일, line 차이 40 이하
   - RECONSIDER: `contentKey` 동일, proposed 변경
5. 링크된 entry의 `retryCount < retryLimit`일 때만 후보를 허용하고 증가시킨다.
6. 링크되지 않은 후보는 `seen` 또는 `pendingRetry`에 같은 `contentKey`가 있으면 버린다.
7. fresh와 `pendingRetry`가 모두 비어 있으면 수렴한다. 아니면 둘을 합쳐 batch를 만들고 기존 `pendingRetry`를 비운다.

### 2. 리뷰 집계와 결정

네 관점 리뷰를 barrier로 모은다. 미지 ID와 중복 verdict는 버리고 `iterLog`에 기록한다. 후보별 `CHANGE` 수로 결정한다.

| CHANGE 수 | 결정 |
|-----------|------|
| 4 | DA 후 Arbiter 판정 |
| 3 | 승인. minority rationale을 경고로 기록 |
| 2 | `holds`에 `SPLIT_2_2 — 사용자 판단 위임`, disposition `HOLD` |
| 1 | `rejected`에 `SUGGESTION`, disposition `SUGGESTION` |
| 0 | `rejected`에 `REJECTED`, disposition `REJECTED` |

Arbiter `PROCEED`는 승인, `RECONSIDER`는 rejected 기록과 disposition `RECONSIDER`, `HOLD`는 holds 기록과 disposition `HOLD`다.

### 3. 적용과 진전 판정

승인 후보를 단일 writer가 순차 적용한다.

- `APPLIED`: `applied`에 추가하고 disposition `APPLIED`.
- `STALE`: disposition `STALE`. 다음 Scan에서 retryLimit 안에서만 재제안 가능.
- `FAILED`: `failed`에 reason과 함께 추가하고 disposition `FAILED`.
- 승인 후보가 있고, `APPLIED=0`이며 STALE을 제외한 `FAILED>0`이면 `noProgressStreak += 1`; 그 외에는 0으로 초기화한다.
- `noProgressStreak >= 2`이면 `BLOCKED:NO_PROGRESS`로 종료한다.

iteration 말에 인프라 재처리 후보를 다음 `pendingRetry`로 옮기고 상세 verdict, confidence, DA strength, Arbiter 판정, apply 결과를 `iterLog`에 남긴다.

## 인프라 재시도와 종료 flush

`REVIEWER_FAILURE`, `ARBITER_FAILURE`, `MISSING_VERDICT` 후보는 후보별 infra retry count를 증가시킨다.

- count가 `retryLimit` 이하: `pendingRetry`.
- 초과: `holds`에 `{reason} (재시도 소진)`으로 추가하고 disposition `HOLD`.

어떤 종료 경로든 남은 `pendingRetry`를 `holds`로 옮기고 reason 뒤에 `종료 시 미처리(flush)`를 붙인다. 침묵 상태로 버리지 않는다.

flush 뒤 status 우선순위:

1. 명시적 `exitStatus` (`FAIL`, `BLOCKED:NO_PROGRESS`)
2. 적용 0건이고 hold가 1개 이상이며 모든 hold가 인프라 reason이면 `BLOCKED:REVIEW_INCOMPLETE`
3. `converged=true`면 `DONE`
4. 그 외 `BLOCKED:MAX_ITERATIONS`

`holds`와 `failed`는 status가 `DONE`이어도 반환하고 경고에 노출한다.
