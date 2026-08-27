---
name: e2e-test
description: "기능 추가/수정 후 연관 HTTP API를 실제 요청으로 E2E 테스트한다. 'API 실제로 테스트해줘', 구현 검증이 필요할 때 사용. profile의 runServerCommand/serverUrl 기반, Bash+curl만 사용."
---

> **Project Overrides**: 실행 전 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/e2e-test.md`를 읽는다.
> 존재하면 추가 규칙/예외로 흡수하고 충돌 시 오버라이드가 우선한다. 상세 규약: 플러그인 루트 `OVERRIDES.md`.


# E2E API 테스트

프로젝트 profile에 지정된 서버를 기동하고, 변경된 API에 실제 HTTP 요청을 보내 응답을 검증한다.
외부 MCP/전용 CLI에 의존하지 않고 **shell + curl + profile** 조합만 사용한다.

실행 시작 시 다음 경로와 핸들을 확정한다.

- `{SKILL_DIR}`: 현재 `SKILL.md`가 있는 디렉토리의 절대 경로. 설치 위치나 현재 작업 디렉토리에서 추측하지 않는다.
- `{LOCK_SCRIPT}`: `{SKILL_DIR}/assets/e2e-lock.sh`.
- `{RUN_DIR}`: `mktemp -d`로 만든 이번 실행 전용 디렉토리. 응답 파일과 락 소유 토큰에 사용한다.
- `{SERVER_SESSION}` / `{SERVER_PID}`: 이번 실행이 서버를 시작했을 때만 보관하는 PTY session handle과 숫자 PID.

정상·실패·SKIP·중단 어느 경로든 종료 전에 이번 실행이 만든 서버 세션, 획득한 락, `{RUN_DIR}`을 이 순서로 정리한다. 실행 중 예외가 생겨도 이 cleanup 규칙은 생략하지 않는다.

## Language Rule

유저와의 모든 대화는 **한국어** (profile의 `language` 기준).

---

## Prerequisites

- profile의 아래 필드가 유효해야 한다 — 내부 호출자(e2e-test-loop/start-workflow)가 `## Profile Snapshot`(resolved 경로 포함)을 넘겼으면 그 값을 쓰고 파일을 다시 읽지 않는다(`{PROFILE_PATH}`는 식별·보고용); 단독 실행이면 플러그인 루트 `PROFILE.md`의 "profile 해석" 규칙으로 `{PROFILE_PATH}`를 확정해 읽는다:
  - `e2eEnabled: true`
  - `serverUrl: "http://..."`
  - `runServerCommand`: 로컬 서버 기동 명령 (이미 서버가 떠 있으면 비워도 됨)
- profile이 없으면 `SKIPPED:NO_PROFILE`, `e2eEnabled: false`면 `SKIPPED:DISABLED`를 반환하고 종료한다 (SKIP 조건 표 참조).

## 플래그

| 플래그 | 단축 | 효과 |
|--------|------|------|
| `--doctor` | | prerequisite 상태 진단 후 종료 |
| `--skip-server` | `-ss` | 서버 기동/종료를 건너뛰고 이미 떠있는 서버를 사용 (**실행 락은 그대로 획득한다** — Step 3.5 참조) |
| `--tag <id>` | | 특정 시나리오 ID(`EC-03`, `BASE-01` 등)만 실행 |
| `--no-lock` | | 실행 락을 건너뛴다. 단독 실행/디버깅 전용 — 다른 에이전트와 동시에 돌면 포트·DB 시드가 충돌한다 |
| `--smoke` | | Spec 유래 시나리오만 실행 — `BASE-01` + `EC-*` 전수. `BASE-02~05`는 `SMOKE_OMITTED`로 기록(판정 영향 없음). 실행 가능 케이스 0건 또는 EC 표 없음이면 Step 2에서 즉시 무시하고 full로 실행한다 |
| `mode: workflow` | | 내부 호출자(`start-workflow` 자율 구간, `e2e-test-loop`)가 명시한다. 인증 토큰을 확보하지 못하면 사용자에게 묻지 않고 `SKIPPED:NO_AUTH`. 없으면 `standalone` |

### `--doctor`

1. profile 읽고 `e2eEnabled`, `serverUrl`, `runServerCommand` 유효성 확인
2. `curl --version` 확인
3. 포트 충돌 여부 (`ss -tlnp` 또는 `lsof -i :PORT`) 확인
4. 실행 락 현황 확인 — `bash "{LOCK_SCRIPT}" status`
5. 결과 표 출력 후 종료

---

## Step 1: 대상 API 수집

사용자의 요청 또는 현재 브랜치의 `git diff`에서 변경된 API를 추출한다:

1. `git diff --name-only {mainBranch}...HEAD` 로 변경 파일 목록 (`{mainBranch}`는 profile 값, 없으면 `main`).
2. profile의 `sourceDirs` 중 handler/route 계층에서 HTTP 엔드포인트(Method + Path) 변경을 찾는다.
3. 각 엔드포인트에 대해 아래를 정리한다:
   - Method, Path
   - Request 형태 (JSON body / query / path param)
   - Response 형태 (status code, 주요 필드)
   - 인증 필요 여부

## Step 2: 시나리오 구성

각 API에 대해 아래 시나리오를 구성하고, **모든 시나리오에 ID를 부여한다**. ID는 Step 7 리포트와 커버리지 판정의 대조 키다.

### 기본 시나리오 (`BASE-*`)

| ID | 시나리오 | 기대 |
|----|----------|------|
| `BASE-01` | Happy Path — 정상 입력 | 2xx |
| `BASE-02` | Required field 누락 | 4xx |
| `BASE-03` | 타입 불일치 (문자열 자리에 숫자 등) | 4xx |
| `BASE-04` | 권한 부족 (토큰 없이 / 다른 권한으로) | 401/403 |
| `BASE-05` | 존재하지 않는 리소스 (잘못된 ID) | 404 |

해당 API에 적용되지 않는 항목(예: 인증이 없는 공개 엔드포인트의 `BASE-04`)은 제외하고 사유를 리포트에 적는다.

**`--smoke`**: `BASE-02~05`는 Spec 비유래 범용 시나리오이므로 실행하지 않고 커버리지에 `SMOKE_OMITTED`로 적는다. `BASE-01`(Happy Path = Spec 정상 흐름)은 필수.

### Spec 엣지 케이스 (`EC-*`)

Spec의 엣지 케이스 표(`$codex-be-harness:request` Phase 4 산출물 — start-workflow에서 호출된 경우 상태 파일의 `## Edge Cases`, 단독 실행이면 사용자가 제공한 Spec)의 **각 행을 빠짐없이** 시나리오로 만든다.
**ID는 Spec의 `EC-nn`을 그대로 승계한다** — 새 번호를 붙이거나 순서를 바꾸지 않는다.

전수 매핑이 원칙이다. 물리적으로 실측 불가능한 케이스(외부 서비스 장애 유발, 동시성 재현 불가, 시간 경과 필요 등)만 예외로 두고, 실행 대신 `UNCOVERED:{사유}`로 리포트에 남긴다.
**"검증이 번거롭다", "코드를 보면 맞는 것 같다"는 예외 사유가 아니다.**

Spec에 엣지 케이스 표가 없거나 ID가 없으면(구버전 Spec) `EC-*` 매핑을 건너뛰고 기본 시나리오만 실행한다. 이 경우 리포트 커버리지 섹션에 `대조 기준 없음`으로 표기한다.

**`--smoke` 무효화 (Step 2에서 즉시 판정)**: 실행 가능 케이스가 0건(`BASE-01` UNCOVERED ∧ EC 0건)이거나 Spec에 EC 표가 없으면(`대조 기준 없음`) `--smoke`를 무시하고 full로 실행하고, Step 7에 `- 실행 수준: full(smoke 미적용: {사유})`를 적는다. 검증 근거가 부족한 상태에서 범위를 줄이지 않는다.

호출 인자에 ID(`EC-03`, `BASE-01` 등)가 있으면 해당 시나리오만 실행한다.

## Step 3: 인증 토큰 확보

프로젝트마다 방식이 다르므로 **profile/프로젝트에 정의된 방식**을 따른다. 순위:

1. 환경 변수 (`$E2E_AUTH_TOKEN` 등)가 있으면 사용
2. profile 본문(Project Notes — 스냅샷 대상이 아니므로 `{PROFILE_PATH}` 본문만 읽기 전용 참조, frontmatter 값은 스냅샷)이 가리키는 발급 절차/발급기(예: 작업 로그 공유 디렉토리의 토큰 발급 바이너리)가 있으면 그것을 실행
3. 프로젝트 `Makefile` 또는 `scripts/` 디렉토리에 토큰 발급 스크립트가 있으면 실행
4. 위 어느 것도 없으면 — `mode: workflow`면 묻지 않고 `SKIPPED:NO_AUTH`를 반환한다. `standalone`일 때만 사용자에게 한 번 묻는다:
   > "E2E 테스트용 인증 토큰을 어떻게 발급받나요?
   > 1. 발급 명령 입력 → 실행해 토큰 확보
   > 2. 토큰 직접 입력 → 그대로 사용
   > 3. 모름/제공 불가 → `SKIPPED:NO_AUTH` 반환 후 종료"

입력받은 방법은 `projectNotes` 업데이트를 제안한다 (사용자 승인 시에만).

## Step 3.5: 실행 락 획득

여러 에이전트가 동시에 E2E를 돌리면 같은 포트와 DB 시드를 두고 충돌한다. 서버를 건드리기 전에 **실행 락**을 잡고, 잡을 때까지 기다린다.

> Step 번호를 소수로 둔 이유: 특화 하네스(minmos 등)의 오버레이가 베이스 Step 번호를 앵커로 참조하므로 기존 번호를 재부여하지 않는다.

`--no-lock` 이면 이 Step 전체를 건너뛴다.
**`--skip-server` 여도 이 Step은 수행한다** — 이미 떠 있는 공유 서버를 여러 에이전트가 두드리는 상황이야말로 락이 가장 필요하다.

대기 총 상한은 기존 계약대로 540초다. 단일 명령을 540초 동안 점유하지 말고, 다음 절차로 최대 55초씩 분할한다.

1. 최초 시각과 총 deadline(최초 시각 + 540초)을 기록한다.
2. 남은 시간이 0보다 크면 `slice = min(55, 남은 초)`로 계산한다.
3. 다음 명령을 실행한다. `TMPDIR={RUN_DIR}`은 획득·heartbeat·해제 호출에 동일하게 사용해야 이번 실행의 소유 토큰이 다른 실행과 섞이지 않는다.

   ```bash
   TMPDIR="{RUN_DIR}" bash "{LOCK_SCRIPT}" acquire "{serverUrl}" \
     --timeout "{slice}" --label "e2e-test {브랜치명 또는 대상 요약}"
   ```

4. `ACQUIRED` 또는 `ALREADY_HELD`면 Step 4로 진행한다. slice timeout이면 누적 경과 시간을 갱신하고, 사용자에게 대기 중임을 알린 뒤 다음 slice를 실행한다.
5. 누적 540초가 끝나면 `SKIPPED:LOCK_TIMEOUT`을 반환한다. 마지막 출력의 `holder_label`을 함께 보고한다.

각 대기 호출과 후속 poll은 60초 안에 제어권을 돌려줘야 한다. 도구가 session handle을 반환하면 같은 handle을 55초 이하 단위로 poll한다.

락 디렉터리: 스냅샷을 받았으면 `HARNESS_E2E_LOCK_DIR={resolved_e2e_lock_dir}`를 앞에 붙여 실행한다. 단독 실행이면 profile에 `e2eLockDir`이 지정돼 있을 때 `HARNESS_E2E_LOCK_DIR={e2eLockDir}`을 앞에 붙인다(비어있으면 자동 해석).

| 종료 코드 | 처리 |
|-----------|------|
| 0 (`ACQUIRED` / `ALREADY_HELD`) | Step 4로 진행 |
| 2 (`TIMEOUT`) | 총 deadline 전이면 다음 slice, 총 540초 소진이면 `SKIPPED:LOCK_TIMEOUT` |
| 그 외(`1` — 락 루트/락 디렉토리 생성 불가·권한 오류 등 획득 자체 불가; 스크립트는 `mkdir`의 비-EEXIST 실패를 대기 없이 즉시 `ERROR` exit 1로 끝낸다) | `BLOCKED:LOCK_UNAVAILABLE` — 서버를 기동하지 않고 즉시 종료(락 미획득이라 Step 6.5 해제 대상 아님). SKIP이 아니라 차단이며 호출자가 Gate 보류로 처리한다 |

대기 중이면 사용자에게 한 줄로 알린다: "다른 에이전트가 `{serverUrl}` E2E 실행 중 — 순번을 기다립니다."

락 키는 `serverUrl` 의 host:port 라, 다른 서비스를 테스트하는 에이전트끼리는 서로 기다리지 않는다.
보유자가 heartbeat 없이 15분을 넘기면(에이전트가 죽은 경우) 락은 자동 회수된다.

## Step 4: 서버 기동

`--skip-server`가 아니고 `runServerCommand`가 있으면 PTY 세션으로 기동한다. 단순 background shell로 분리하지 않는다.

1. PTY를 켜고 `bash -lc 'printf "__E2E_SERVER_PID__=%s\\n" "$$"; exec bash -lc "$1"' e2e-server {RUN_SERVER_ARG}` 형태로 실행한다. `{RUN_SERVER_ARG}`는 profile의 `runServerCommand` 전문을 shell-safe한 단일 positional argument로 인코딩한 값이며 문자열 연결로 삽입하지 않는다. 환경 변수 할당이나 복합 명령은 안쪽 shell이 해석한다.
2. 반환된 session handle을 `{SERVER_SESSION}`에, marker의 숫자 PID를 검증해 `{SERVER_PID}`에 저장한다. 둘 중 하나라도 확보하지 못하면 해당 세션에 interrupt를 보내고 `SKIPPED:SERVER_START_FAIL`로 정리한다.
3. PTY 출력은 55초 이하 단위로만 poll한다. 서버 로그가 계속 발생해도 session handle을 잃지 않는다.

기동 후 `serverUrl` 이 응답할 때까지 대기 (최대 30초). `curl -sf {serverUrl}/healthz` 또는 루트 경로에 대한 HEAD 요청으로 확인.

30초 내 응답이 없거나 서버 세션이 먼저 종료되면 최근 PTY 로그와 exit 정보를 읽어 실패 원인을 보고하고, Step 6과 Step 6.5 cleanup 뒤 `SKIPPED:SERVER_START_FAIL`을 반환한다.

## Step 5: 요청 실행

> 락을 잡았다면(`--no-lock` 아님) 시나리오를 몇 개 처리할 때마다 heartbeat를 보낸다 —
> `TMPDIR="{RUN_DIR}" bash "{LOCK_SCRIPT}" beat "{serverUrl}"`.
> heartbeat 가 15분 끊기면 다른 에이전트가 죽은 락으로 보고 회수한다.

각 시나리오에 대해:

```bash
curl -sS -o "{RUN_DIR}/response.json" \
  -w "HTTP %{http_code}\nTime %{time_total}s\n" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN"  \  # 해당 시만
  -X {Method} \
  -d '{body json}' \
  "{serverUrl}{path}"
```

응답을 파일에 저장한 뒤 읽어서 검증한다.

### 응답 검증

| 검증 항목 | 방법 |
|----------|------|
| HTTP status | 기대값과 비교 |
| Content-Type | `application/json` 등 기대 타입 |
| 필수 필드 존재 | `jq`로 키 추출 후 null/빈 체크 (`jq`가 없으면 Python/Read로 파싱) |
| 값 제약 | ID 포맷, 범위, 길이 등 |
| 시간 | 500ms 초과 시 warn |

`apiDocsPath` 에 OpenAPI 스펙이 있으면 해당 엔드포인트의 response schema와 구조를 비교한다 (초과 필드 / 누락 필드). 스펙이 없으면 이 단계는 생략.

## Step 6: 서버 종료

Step 4에서 만든 서버만 종료한다. `--skip-server`이거나 이번 실행이 만든 `{SERVER_SESSION}`이 없으면 기존 서버는 건드리지 않는다.

1. `{SERVER_SESSION}`에 interrupt를 보내고 최대 5초 동안 짧게 poll한다.
2. 아직 실행 중이면 검증한 `{SERVER_PID}`에 `TERM`을 보내고 최대 5초 기다린다. 자식 프로세스가 남으면 해당 PID의 자식에도 `TERM`을 보낸다.
3. 그래도 살아 있으면 이번 실행에서 기록한 PID와 그 자식에만 `KILL`을 보내고 PTY가 종료될 때까지 poll한다.
4. 이미 종료된 session은 exit 결과만 수집한다. 숫자로 검증되지 않은 PID, 재사용 가능성이 있는 임의 PID, 기존 서버에는 kill을 보내지 않는다.

서버 정리는 락 해제보다 먼저 수행하며 모든 종료 경로의 cleanup에서 한 번만 실행한다.

## Step 6.5: 실행 락 해제

Step 3.5에서 락을 잡았다면 반드시 해제한다. **정상 종료·SKIP·실패 어느 경로에서도 빠뜨리지 않는다** —
TTL(15분) 자동 회수는 안전망이지 해제 수단이 아니며, 그동안 다른 에이전트가 대기한다.

```bash
TMPDIR="{RUN_DIR}" bash "{LOCK_SCRIPT}" release "{serverUrl}"
```

`RELEASE_DENIED` 가 나오면 이미 TTL 회수 후 다른 에이전트가 락을 가져간 것이다 (해당 실행 결과는 오염 가능성이 있으므로 리포트에 경고로 남긴다).

## Step 7: 리포트

```markdown
## E2E Test Report

### 환경
- serverUrl: {serverUrl}
- 실행 수준: smoke | full | full(smoke 미적용: {사유})
- 실행 시나리오: N개
- 경과 시간: {total_time}

### 결과 요약
| ID | 시나리오 | Method | Path | 기대 | 실제 | 판정 |
|----|----------|--------|------|------|------|------|
| BASE-01 | Happy path | POST | /v1/users | 201 | 201 | PASS |
| BASE-02 | Required field 누락 | POST | /v1/users | 400 | 500 | FAIL |
| EC-03 | 중복 이메일 가입 | POST | /v1/users | 409 | 409 | PASS |

### 커버리지
| Spec 엣지 케이스 | 대응 시나리오 | 상태 |
|-----------------|--------------|------|
| EC-01 | EC-01 | 실행됨 |
| EC-02 | — | `UNCOVERED:외부 결제사 타임아웃 재현 불가` |
| EC-03 | EC-03 | 실행됨 |

- Spec 엣지 케이스 [N]건 중 [M]건 실행, [K]건 미커버
- 생략 시나리오: `SMOKE_OMITTED` BASE-02, BASE-03, BASE-04, BASE-05 (--smoke) / 없음
- 판정: [PASS / WARN / FAIL]

### 실패 상세
- BASE-02: 서버가 500을 반환. 로그 발췌: [...]

### 수정 제안
- [파일:라인, 제안 수정]
```

### 판정 기준

| 판정 | 조건 |
|------|------|
| `PASS` | 시나리오 실패 0건 **AND** 미커버 0건 |
| `WARN` | 시나리오 실패 0건 **AND** 미커버 1건 이상 (사유가 명시된 것만) |
| `FAIL` | 시나리오 실패 1건 이상 |

미커버는 **구현 결함이 아니라 검증 공백**이므로 수정 루프의 트리거가 아니다. 사유와 함께 리포트에 남겨 호출자가 판단하게 한다. `SMOKE_OMITTED`는 판정에 영향을 주지 않는다(커버리지 데이터).

`- 실행 수준:` 줄은 **항상** 출력한다 — 호출자(e2e-test-loop·start-workflow)가 승격 판단과 리포트 렌더링 인자에 그대로 사용한다.

실패가 있으면 호출자(start-workflow 또는 e2e-test-loop)가 수정 루프를 돌 수 있도록 `"이슈: N건, 수정: Y/N, 미커버: K건, 실행 수준: {smoke|full|full(smoke 미적용: 사유)}"` 형식 요약을 마지막 줄에 포함한다 (기존 파서 호환을 위해 앞의 두 필드 순서와 표기는 고정).

## SKIP 조건

| 조건 | 반환 |
|------|------|
| profile 없음 | `SKIPPED:NO_PROFILE` |
| `e2eEnabled: false` | `SKIPPED:DISABLED` |
| `serverUrl` 없음 | `SKIPPED:NO_SERVER_URL` |
| `runServerCommand` 없고 `--skip-server`도 아님, 기존 서버도 응답 없음 | `SKIPPED:NO_SERVER` |
| 인증 토큰 확보 실패 | `SKIPPED:NO_AUTH` |
| 변경된 HTTP API 없음 | `SKIPPED:NO_CHANGED_API` |
| 실행 락 대기 시간 초과 (다른 에이전트가 계속 보유) | `SKIPPED:LOCK_TIMEOUT` |

SKIP은 오케스트레이터의 루프 재시작 트리거가 아니다.

**SKIP 경로의 락 해제**: Step 3.5 이후에 발생하는 `SERVER_START_FAIL`은 종료 전에 반드시 Step 6.5를 수행한다.
Step 3.5 이전의 SKIP(`NO_PROFILE`, `DISABLED`, `NO_SERVER_URL`, `NO_SERVER`, `NO_AUTH`, `NO_CHANGED_API`)과 `LOCK_TIMEOUT`은 락을 잡지 않았으므로 해제할 것이 없다. `LOCK_UNAVAILABLE`도 락을 잡지 않았으므로 해제할 것이 없다.

락 해제 뒤 `{RUN_DIR}`을 제거한다. 서버 또는 락 cleanup이 실패하면 원래 테스트 판정을 덮어쓰지 말고 리포트에 cleanup 경고를 추가한다.

## 주의사항

- DB 시드/정리는 **프로젝트의 기존 스크립트**를 그대로 호출한다. be-harness는 DB를 직접 조작하지 않는다.
- gRPC 테스트는 `grpcurl` 등 전용 도구가 필요하므로 이 스킬에서 다루지 않는다 (프로젝트에서 별도 스크립트로 처리).
- PubSub/큐 메시지 검증도 범위 밖이다.
