---
name: e2e-test-loop
description: "E2E 테스트 → 이슈 수정 → 재테스트를 반복한다 (최대 5회). 종료 시 정직한 자기 점검 md 리포트를 스크립트로 생성한다. 기능 구현 후 'E2E 돌려줘', '테스트 통과할 때까지 고쳐줘' 요청 시 사용. start-workflow 품질 루프에서 자동 호출됨."
---

> **Project Overrides**: 실행 전 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/e2e-test-loop.md`를 읽는다.
> 존재하면 추가 규칙/예외로 흡수하고 충돌 시 오버라이드가 우선한다. 상세 규약: 플러그인 루트 `OVERRIDES.md`.

# E2E Test Loop

`$codex-be-harness:e2e-test` 를 실행하고, 실패가 있으면 수정한 뒤 다시 실행한다. 최대 `{MAX_ITER}`회 반복하고, 종료 시 실행 전체를 **정직한 자기 점검 md 리포트**로 남긴다(렌더링은 스크립트 — 오케스트레이터/에이전트가 리포트를 직접 쓰지 않는다).

**플레이스홀더 정의** (본문·assets 공통, 값 변경은 여기 한 곳만 수정):

- `{SKILL_DIR}` = 현재 `SKILL.md`가 있는 디렉토리의 절대 경로
- `{RENDERER}` = `{SKILL_DIR}/assets/render_e2e_report.py`
- `{RUN_DIR}` = 실제 루프 진입 시 `mktemp -d`로 만드는 실행 전용 임시 디렉토리
- `{RUN_REPORT}` = `{RUN_DIR}/e2e-run-report.md` (루프 중 누적하는 원시 기록)
- `{REPORT_DIR}` = 내부 호출자가 넘긴 profile 스냅샷의 `resolved_report_dir`(workflow 호출); 단독 실행이면 profile의 `reportDir`(없으면 `.codex/harness-reports`)
- `{MAX_ITER}` = 5 (`--smoke` 시 3; smoke 무효화 latch 시 5로 복원)
- `{CWD}` = 현재 작업 디렉토리 (프로젝트 루트)

## Flags

| 플래그 | 단축 | 효과 |
|--------|------|------|
| `--skip-doctor` | `-sd` | 루프 진입 전 환경 probe를 건너뛴다 (사용자 책임) |
| `--no-lock` | | 하위 `e2e-test` 에 그대로 전달해 실행 락을 건너뛴다 (단독 실행/디버깅 전용) |
| `--smoke` | | 하위 `e2e-test --smoke` 전달(`BASE-01` + `EC-*` 전수만) + `{MAX_ITER}` = 3. 실효 수준은 e2e-test가 Step 2에서 확정한다(0건·EC 표 없음이면 full 폴백 → 아래 latch) |
| `mode: workflow` | | 내부 호출자가 명시하면 하위 `e2e-test` 에 그대로 전달한다 (인증 토큰 부재 시 질문 없이 `SKIPPED:NO_AUTH`) |

## Language Rule

유저와의 모든 대화는 profile의 `language` 값(기본 `ko`, 한국어)을 따른다.

## Step 1: Pre-flight Probe (Fast SKIP Gate)

`--skip-doctor` / `-sd` 가 **없으면**, 루프 진입 전 빠른 환경 probe를 실행한다.
**환경 부재가 확정되면 루프를 한 번도 돌지 않고 즉시 `SKIPPED`를 반환한다** — 실패 후 판정이 아니라 진입 게이트에서 끊어낸다.

profile 값을 확정하고 아래를 확인한다 — 내부 호출자(start-workflow)가 `## Profile Snapshot`(resolved 경로 포함)을 넘겼으면 그 값을 profile 값으로 쓰고 파일을 다시 읽지 않는다(`{PROFILE_PATH}`는 식별·보고용). 단독 실행이면 플러그인 루트 `PROFILE.md`의 "profile 해석" 규칙으로 `{PROFILE_PATH}`를 확정해 읽는다:

| 점검 항목 | 실패 시 |
|----------|--------|
| profile 존재 | `SKIPPED:NO_PROFILE` |
| `e2eEnabled: true` | `SKIPPED:DISABLED` |
| `serverUrl` 비어있지 않음 | `SKIPPED:NO_SERVER_URL` |
| `runServerCommand` 비어있지 않음 (또는 기존 서버가 `serverUrl`에 응답) | `SKIPPED:NO_SERVER` |

처리 규칙:
- 모두 OK → Step 2로 진행
- 하나라도 FAIL → **루프 진입 없이** 즉시 아래 형식으로 종료 (리포트 파일 생성·md 렌더링 없음):
  ```
  ## E2E Test Loop — SKIPPED
  사유: SKIPPED:{REASON}
  누락 항목: {항목}
  복구 방법: `$codex-be-harness:init` 으로 profile 재설정 또는 `$codex-be-harness:doctor` 로 진단
  ```

## Step 2: 실행 리포트 초기화

> Probe를 통과해 **실제 루프에 진입하는 경우에만** 수행한다. Step 1 SKIP 종료 경로에서는 임시 디렉토리나 리포트 파일을 만들지 않는다.

`mktemp -d`로 `{RUN_DIR}`을 만들고 절대 경로를 고정한다. 루프 동안 수행하는 모든 테스트 케이스의 요청 데이터·기대·실제·판정과 실패→수정 내역을 `{RUN_REPORT}`에 누적한다. 루프 종료 후 이 파일이 Step 4 md 렌더링(스크립트)의 유일한 입력이 된다 — 여기에 적히지 않은 것은 리포트에 없다. 서브에이전트에는 두 경로를 모두 절대 경로로 전달한다.

`{RUN_REPORT}`를 생성한다(실행 전용 경로이므로 이미 파일이 있으면 덮어쓴다):

```markdown
# E2E 테스트 실행 리포트 — {브랜치명 또는 작업 요약}

> 생성: {ISO timestamp}
> E2E 메인 플로우: {제공된 메인 플로우 전문 또는 "자동 도출 (git diff 기반)"}
> 수준: {첫 iteration e2e-test의 `- 실행 수준:` 값 그대로 — 기록 전에는 "미정"}

## 테스트 대상 엔드포인트
<!-- Step 3 첫 iteration에서 e2e-test가 도출한 엔드포인트 목록을 1회 채운다 -->

## Iteration 기록
<!-- 매 iteration 결과를 아래로 append -->
```

**E2E 메인 플로우 출처 (단일 출처 원칙)**: 호출 컨텍스트(상위 워크플로우 상태 파일의 `## E2E 메인 플로우` 섹션, 또는 사용자 대화)에 메인 플로우가 제공되면 그 텍스트를 **그대로** 헤더에 옮겨 적는다 — 재해석·재가공·요약하지 않는다. 제공되지 않았으면 `자동 도출 (git diff 기반)`으로 기록한다.

**케이스 블록 형식** — Step 3에서 매 테스트 케이스를 `## Iteration 기록` 아래에 이 형식으로 append 한다:

```markdown
### Iteration {N}

#### {분류} — {케이스명}
- 요청: `{METHOD} {PATH}` · body: `{request body 전문, 없으면 "(없음)"}`
- 기대: {기대 status / 응답}
- 실제: {실제 status / 응답 요약}
- 판정: ✅ 통과 / ❌ 실패 / ⚠️ INCONCLUSIVE({사유}) / ⚠️ PARTIAL({사유})
```

> `{분류}`는 `Happy Path` / `Validation` / `Edge Case` / `인증·권한` / `Status 정합성` 중 하나. `### Iteration {N}` 헤더는 iteration당 1회만 적는다.

**정직성 규칙 (append 시점에 판정한다 — 렌더러는 기록된 마커만 믿는다)**:
- 응답이 본 변경 유무와 무관하게 같다면 ✅ 대신 `⚠️ INCONCLUSIVE(응답이 본 변경과 무관)`. 입력의 일부만 커버했다면 `⚠️ PARTIAL({커버한 범위})`.
- `- 요청:` `- 기대:` `- 실제:` `- 판정:` 네 줄은 **필수** — 하나라도 빠진 케이스는 렌더러가 `INCONCLUSIVE(필수 필드 결여)`로 집계한다.
- **케이스명은 iteration 간 동일하게 유지**한다 — TC 식별 키는 `{분류} + {케이스명}`이다. 이름을 바꾸면 다른 케이스로 집계된다.

**실패→수정 블록 형식** — Step 3의 수정 단계에서 실패한 케이스마다 해당 케이스 블록 끝에 이 형식으로 append 한다:

```markdown
**실패 → 수정 ({케이스명})**
- 실패 원인: {root cause}
- 수정: {file:line — 변경 요약}
- 귀속: 본 변경 코드 | 검증 인프라 | 혼합
- 재빌드/재시작: 예 / 아니오
```

> `- 귀속:` 줄은 선택 — 생략하면 렌더러가 `- 수정:` 줄의 경로로 추정한다(테스트·mock·fixture·env·docker·헬퍼·scripts → 검증 인프라, 그 외 → 본 변경 코드). 수정 블록은 반드시 **해당 케이스 블록 직후**에 둔다.

**최종 요약 블록 형식** — Step 4에서 리포트 하단에 1회 append 한다:

```markdown
## 최종 요약
- 총 iteration: {N}회
- 총 테스트: {M}건 (통과 {X} / 실패 {Y})
- 미해결 이슈: {목록 또는 "없음"}
- 커버리지: UNCOVERED {ID}({사유}) … / SMOKE_OMITTED {IDs} / 없음
```

> `- 커버리지:` 줄은 마지막 e2e-test 리포트의 커버리지·생략 시나리오를 한 줄로 옮긴다(렌더러의 GAP 입력 — 1회만).

> 누적 규칙: 모든 기록은 **append-only**. 이전 iteration 블록이나 이미 적힌 케이스 블록을 수정하지 않는다. 마크다운만 작성한다(HTML 직접 작성 금지 — Step 4 스크립트 파싱이 깨진다).

## Step 3: 루프 (최대 {MAX_ITER}회)

1. 같은 플러그인에 포함된 `$codex-be-harness:e2e-test`를 실행한다(`--smoke`면 `--smoke`를, 스냅샷을 받았으면 같은 스냅샷을 그대로 전달). 현재 플러그인의 실제 등록 이름으로 resolve하고, 다른 설치나 사용자 전역 스킬로 대체하지 않는다.
   - 첫 iteration이면 e2e-test 리포트의 `- 실행 수준:` 값을 헤더 `> 수준:`에 옮겨 적는다.
   - 헤더의 E2E 메인 플로우가 `자동 도출 (git diff 기반)`이 아니면, 해당 플로우를 Happy Path 필수 시나리오로 포함하도록 e2e-test에 전달한다.
   - 첫 iteration이면 e2e-test가 도출한 엔드포인트 목록을 리포트의 `## 테스트 대상 엔드포인트` 섹션에 채운다.
   - **smoke 무효화 latch**: 하위 e2e-test가 `- 실행 수준: full(smoke 미적용: {사유})`를 보고하면 그 즉시 실효 수준 = full로 latch한다 — `{MAX_ITER}` 3 → 5(현재 iteration 번호 유지), 헤더 `> 수준:` = 그 값, Step 4 렌더러 인자 `--level full --level-note "{사유}"`(렌더러가 `smoke 미적용:` 접두사를 붙인다). 상한 평가는 latch 뒤에 한다.
   - 하위 스킬이 `SKIPPED:*`를 반환하면 루프를 추가 진행하지 않는다. `{RUN_DIR}`을 정리하고 동일 SKIP 사유로 보고한다. **Step 4(md 렌더링)는 건너뛴다.**
   - **하위 `BLOCKED:LOCK_UNAVAILABLE`**(락 미획득·서버 미기동·케이스 0건): 루프를 즉시 종료한다. `rm -f {RUN_REPORT}` 후 `rmdir {RUN_DIR}`(산출물 확인 규칙의 예외 — SKIP 경로와 동일), Step 4 렌더링 생략, 종료 출력은 `- 종료 상태: BLOCKED:LOCK_UNAVAILABLE` / `- 실행 수준: {요청 수준 smoke|full}` / `- E2E 리포트: 없음 (BLOCKED:LOCK_UNAVAILABLE)`.
   - 정상 실행되면, 이번 iteration의 **모든 테스트 케이스**(통과·실패 무관)를 Step 2의 "케이스 블록 형식"으로 append 한다.
2. 결과를 확인한다:
   - **판정 `PASS`** (모든 시나리오 통과 + 미커버 0건) → 루프 종료 → Step 4
   - **판정 `WARN`** (실패 0건 + `UNCOVERED:{사유}` 1건 이상) → 루프 종료 → Step 4. 미커버는 검증 공백이지 구현 결함이 아니므로 수정 루프를 돌리지 않고, 사유를 리포트에 남긴 채 상위에 전달한다.
   - **판정 `FAIL`** → 3번으로 진행
3. 발견된 이슈를 Terra executor에게 위임한다:
   ```
   아래 E2E 실패를 수정하세요. 프로젝트 루트: {CWD}.
   실행 리포트: {RUN_REPORT}
   failures: {실패 목록 전체}
   - 원인 추적: 서버 로그 / 코드 흐름 / Spec 차이 중 무엇인지 먼저 특정하고 수정.
   - 파일 수정 후 {buildCommand} (비어있지 않으면) 로 빌드 통과 확인.
   - 서버를 시작하거나 종료하지 마세요. 각 e2e-test 호출이 자신의 PTY/PID 세션을 정리합니다.
   - 수정 후 "수정: N건, 파일: [목록]" 형식으로 보고.
   ```
   - 다음 e2e-test 호출이 수정된 코드로 새 서버 세션을 시작하므로, 오케스트레이터도 별도로 서버를 재시작하지 않는다.
   - 실패한 각 케이스에 대해 Step 2의 "실패→수정 블록 형식"으로 append 한다.
   - 커밋: `git add [수정 파일] && git commit -m "Fix: E2E 실패 수정 (반복 {iteration})"`
4. iteration 카운트를 1 증가시키고 1번으로 돌아간다.

| 종료 조건 | 결과 |
|----------|------|
| 판정 `PASS` | 루프 탈출 → Step 4 |
| 판정 `WARN` (미커버만) | 루프 탈출 → Step 4, 미커버 사유를 상위에 전달 |
| `e2e-test`가 `SKIPPED:*` 반환 | 루프 미진행, SKIPPED 그대로 보고 (Step 4 생략) |
| `e2e-test`가 `BLOCKED:LOCK_UNAVAILABLE` 반환 | 루프 즉시 종료, `{RUN_DIR}` 정리, Step 4 생략, 상태 그대로 보고 |
| `{MAX_ITER}`회 도달, 이슈 잔존 | `BLOCKED:MAX_ITERATIONS` — 미해결 이슈 목록과 함께 Step 4로 강제 진행 |
| 같은 실패 시나리오가 연속 2회 동일 에러로 반복 | `BLOCKED:NO_PROGRESS` — 즉시 중단하고 Step 4로 진행 (같은 파일을 같은 방향으로 반복 수정 중) |

## Step 4: 리포트 md 렌더링 (정직한 자기 점검 형식)

루프가 종료되면(전체 통과로 탈출 / 상한 도달 무관) `{RUN_REPORT}`를 **스크립트로** 정직한 자기 점검(self-check) md로 렌더링한다. 오케스트레이터/에이전트가 리포트를 직접 쓰지 않는다 — verdict 5종·시도별 raw 기록·"본 변경 코드 vs 검증 인프라" 귀속·GAP·"아무 의심 없이 성공인가?" 직답은 모두 `{RUN_REPORT}`의 기록에서 결정적으로 계산된다. 정직성은 Step 2의 append 시점 규칙(마커·귀속 줄·케이스명 불변·필수 4줄)이 담보한다.

> **건너뛰는 경우**: Step 1 Probe SKIP, Step 3에서 `e2e-test`가 `SKIPPED:*`를 반환해 **테스트가 한 번도 실행되지 않은 경우**, 또는 `BLOCKED:LOCK_UNAVAILABLE`. e2e-test가 1회 이상 정상 실행됐다면 통과/실패와 무관하게 항상 렌더링한다.

1. 리포트 하단에 Step 2의 "최종 요약 블록 형식"으로 `## 최종 요약`을 append 한다(`- 커버리지:` 줄 포함).
2. `mkdir -p {REPORT_DIR}` 후 렌더러를 실행한다:
   ```bash
   python3 {RENDERER} {RUN_REPORT} --out-dir {REPORT_DIR} --branch "$(git branch --show-current)" \
     --level {smoke|full} [--level-note "{사유}"] --status {DONE|BLOCKED:MAX_ITERATIONS|BLOCKED:NO_PROGRESS}
   ```
   - 헤더 `> 수준:` 매핑: `smoke` → `--level smoke`, `full` → `--level full`, `full(smoke 미적용: X)` → `--level full --level-note "X"`(접두사는 렌더러가 붙인다).
   - `--status`는 종료 표의 결과이며, 판정 `PASS`/`WARN` 탈출은 `DONE`이다. `--level`·`--status`는 둘 다 필수다.
   - 출력 파일: `{REPORT_DIR}/{YYYYMMDD-HHMMSS}-{slug(branch)}-e2e-report.md`(스크립트가 결정·배타 생성, 기존 파일이 있으면 `-2`/`-3` 접미). **파일명 컨벤션 고정** — 상위 워크플로우가 `*-e2e-report.md` 패턴에 의존한다.
   - stdout 두 줄 `경로: …` / `상태: OK|DEGRADED({사유})`를 그대로 캡처한다 — `DEGRADED`여도 파일은 생성된다.
3. **폴백**(exit ≠ 0 — python3 부재·인자 오류·쓰기 실패): 목적지 이름은 렌더러와 같은 규칙 `{REPORT_DIR}/{YYYYMMDD-HHMMSS}-{slug(branch)}-e2e-report.md`(slug = `[^A-Za-z0-9._-]+` → `-`, 양끝 `-` 제거; 브랜치를 못 구하면 `e2e`)를 따른다. 배타 생성은 셸 리다이렉션으로 `(set -C; cat "{RUN_REPORT}" > "{후보}")`를 base → `-2` → `-3` 순으로 시도한다(성공 = exit 0 **그리고** 비어 있지 않음; 정리는 **이번 시도가 실제로 생성한 후보**(리다이렉션이 열린 뒤 `cat`이 실패한 경우)만 `rm -f` — noclobber로 열리지 않은 기존 파일은 손대지 않고 다음 접미로). 셋 다 실패하면 폴백 실패(4의 이중 실패)다. 성공 시 "E2E 리포트 렌더링 스크립트 실패({사유}) — 원시 실행 기록을 그대로 저장했습니다."라고 고지하고 종료 출력 `E2E 리포트:` 줄에 `(원시 기록, 렌더링 실패: {사유})`를 병기한다.
4. **산출물 확인 후 정리**: 렌더러 또는 폴백이 만든 파일이 **존재하고 비어 있지 않음을 확인한 뒤에만** `{RUN_DIR}`을 정리한다(정리 실패는 판정을 덮어쓰지 않고 cleanup 경고). 둘 다 실패하면 `{RUN_DIR}`을 보존하고 `- E2E 리포트: 없음 (렌더링 실패: {사유}; 원시 기록: {RUN_REPORT})`로 출력한다 — 종료 상태는 루프 판정 그대로(리포트 실패는 테스트 판정을 바꾸지 않는다).
5. 렌더러가 계산하는 것(참고 — 규칙은 스크립트 상단 주석이 canonical): TC = `{분류} + {케이스명}` 동일성으로 iteration 순 통합(`TC-01`, `TC-02`…) · verdict = `CLEAN PASS` / `PASS (after N fixes)` / `FAIL` / `INCONCLUSIVE({사유})` / `PARTIAL({사유})`(마커 우선, 수정 없이 재시도 통과·수정 후 재검증 기록 없음은 INCONCLUSIVE) · 귀속 = `- 귀속:` 줄 우선, 없으면 `- 수정:` 경로 추정 · GAP = 미해결 이슈 + FAIL TC + 미호출 엔드포인트 + `UNCOVERED`/`SMOKE_OMITTED`(없으면 "기록 없음 — 리포트는 실행된 케이스만 증명한다") · 직답 = 경성 결함 0건 ∧ 수정 후 통과 0건 ∧ `SMOKE_OMITTED` 0건 ∧ `DONE`일 때만 `예`, smoke는 최대 `조건부 예 (smoke 범위)`.

## 종료 시 출력

```
E2E Test Loop 완료
- 총 iteration: N회
- 발견된 이슈: M건
- 수정된 이슈: X건
- 미해결 이슈: Y건 (있으면 목록)
- 종료 상태: DONE | BLOCKED:MAX_ITERATIONS | BLOCKED:NO_PROGRESS
- 실행 수준: {헤더 `> 수준:` 값 그대로}
- E2E 리포트: {절대 경로} [(원시 기록, 렌더링 실패: {사유})] [/ 상태: DEGRADED({사유})]
```

> `E2E 리포트:` 줄은 **의무 출력**이다. 상위 워크플로우가 이 경로를 **유일한 채널**로 전달받아 최종 보고서에 참조한다. 서브 에이전트로 실행될 때도 이 줄이 stdout에 반드시 포함돼야 경로가 오케스트레이터까지 전파된다.

probe SKIP / 테스트 미실행인 경우(렌더러를 호출하지 않는다 — 산출물 없음이 정직한 결과):
```
E2E Test Loop — SKIPPED
- 사유: SKIPPED:{REASON}
- 총 iteration: 0회
- E2E 리포트: 없음 (SKIPPED:{REASON})
```

하위 실행 락 획득 자체가 불가능한 경우:
```
E2E Test Loop — BLOCKED
- 종료 상태: BLOCKED:LOCK_UNAVAILABLE
- 실행 수준: {요청 수준 smoke|full}
- 총 iteration: {N}회
- E2E 리포트: 없음 (BLOCKED:LOCK_UNAVAILABLE)
```

## 상태 코드

| 코드 | 의미 |
|------|------|
| `DONE` | 루프 정상 종료 |
| `SKIPPED:{사유}` | 환경 미충족으로 루프 미진행 (`NO_PROFILE`, `DISABLED`, `NO_SERVER_URL`, `NO_SERVER`, 하위 스킬 SKIP 전파) |
| `BLOCKED:MAX_ITERATIONS` | 상한 도달, 이슈 잔존 |
| `BLOCKED:NO_PROGRESS` | 같은 실패를 연속 2회 동일 에러로 반복 |
| `BLOCKED:LOCK_UNAVAILABLE` | 하위 e2e-test가 락을 획득하지 못해 서버 기동 전 종료 — 루프 즉시 종료, 리포트 없음 |
| `PASS` / `WARN` / `FAIL` | 하위 `e2e-test` 판정 (그대로 전파) |

## 주의사항

- `e2e-test` 스킬이 서버 기동/종료를 책임지므로, 이 루프에서는 서버 상태를 직접 건드리지 않는다.
- `e2e-test`가 반환한 session/PID cleanup 경고를 각 iteration의 raw 기록에 보존한다. 루프가 알 수 없는 PID를 대신 종료하지 않는다.
- **실행 락도 직접 다루지 않는다.** 하위 `e2e-test` 가 회차마다 획득/해제하므로, 수정 단계 동안에는 락이 풀려 다른 에이전트가 순번을 가져갈 수 있다. 루프 전체를 잠그면 수정하는 내내 다른 에이전트가 굶으므로 의도된 동작이다.
- 수정 에이전트가 서버를 재시작하지 않도록 프롬프트에 명시한다.
- `{buildCommand}` 가 비어있으면 빌드 체크는 SKIP.

## References

| 파일 | 로드 시점 |
|------|----------|
| `assets/render_e2e_report.py` | Step 4 (md 렌더링 스크립트 — 읽지 않고 실행만 한다) |
