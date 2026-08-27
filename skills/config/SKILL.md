---
name: config
description: "be-harness project profile(.codex/be-harness.local.md)의 설정 값을 조회하고 키 단위로 수정한다. '프로필 설정 확인해줘', '설정 값 바꿔줘', '{키} 값 뭐야', '{키}를 {값}으로 바꿔줘' 요청 시, init 재실행 없이 값 하나만 보거나 고칠 때 사용. 파일 생성·환경 진단은 하지 않는다 (init·doctor 담당)."
---

> **Project Overrides**: 실행 전 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/config.md`가 있으면 읽는다.
> 존재하면 추가 규칙/예외로 흡수하고 충돌 시 오버라이드가 우선한다. 상세 규약: 플러그인 루트 `OVERRIDES.md`.


# be-harness Config

profile의 설정 값을 **조회**하고 `{키}={값}` 배치로 **수정**한다. `init`을 다시 돌리지 않고 값 하나를 보거나 바꾸는 경로다.

호출: `$codex-be-harness:config` (전체 조회) · `$codex-be-harness:config {키}` (단일 조회) · `$codex-be-harness:config {키}={값} [{키}={값} …]` (배치 수정)

## 원칙

- 파일을 **생성하지 않는다** — 없으면 `$codex-be-harness:init` 안내. 명령 실행·자동 감지·환경 점검도 하지 않는다(`doctor` 담당). 단, `{PROFILE_PATH}` 확정에 필요한 `PROFILE.md`의 읽기 전용 Git 조회만 수행한다.
- **쓰는 파일은 `{PROFILE_PATH}` 하나뿐이다.** 읽는 파일은 `{PROFILE_PATH}`·플러그인 루트 `PROFILE.md`(이 스킬 파일 기준 `../../PROFILE.md`)·머리말의 Project Overrides 파일뿐이며 Overrides는 편집하지 않는다. `~/.codex/config.toml`(시크릿)·start-workflow 상태 파일은 읽지도 쓰지도 출력하지도 않는다.
- 플러그인 루트 `PROFILE.md`의 "profile 해석" 규칙으로 `{PROFILE_PATH}`를 확정한다. 프로젝트 루트 profile을 우선하고, linked worktree면 메인 워크트리 profile을 상속하며, 둘 다 없으면 `PROFILE_MISSING`이다. 상속 시 수정도 그 메인 워크트리 파일에 반영한다.
- 수정은 **frontmatter 안**에서 대상 키의 줄만 바꾼다. 본문(Project Notes)·구분선·키 순서·각 줄의 EOL은 바이트 그대로 보존한다.
- **중립 주석 줄·꼬리 주석은 어떤 규칙도 삭제·변형하지 않는다.** 삭제가 필요한 변경은 비지원으로 차단하고 직접 편집을 안내한다. 유일한 예외는 플레이스홀더 활성화(Step 4 ③)이며, 주석 처리된 `# {키}:` 줄의 선두 `# `만 벗긴다.
- `init`이 수용하는 값은 거부하지 않는다. 문서화된 한계 2건은 배열 원소 안의 쉼표와 따옴표 없는 값 앞뒤 공백이다(따옴표로 표현: `key=" v"`).
- 알 수 없는 키(점 표기 `sourceDirs.0`, `--플래그` 포함)는 쓰기 거부, 조회는 `⚠ 알 수 없는 키` 행으로 표시한다.
- 배치는 전건 검증 후 frontmatter 전체를 **한 번의** 치환으로 반영한다. 전부 `DONE` 아니면 전부 미반영이다.
- 동시 실행은 지원 범위 밖이며, 컨텍스트 검증형 치환이므로 lost update 없이 `FAIL`로 끝난다.
- 플레이스홀더(본문에서는 이 이름만 사용):
  - `{PROFILE_PATH}` = 플러그인 루트 `PROFILE.md`의 "profile 해석"으로 확정한 절대 경로
  - `{Q_MAX}` = 2 (실행당 질문 예산 — 재입력 질문 포함)

## 전제 조건

| 항목 | 미충족 시 |
|------|----------|
| `{PROFILE_PATH}` 존재 | `PROFILE_MISSING` = `BLOCKED:NO_PROFILE` — "1. `$codex-be-harness:init`으로 profile 생성(사용자) 2. 종료" |
| 플러그인 루트 `PROFILE.md`(스키마 canonical — 키별 허용값·빈 값 의미·프리셋 표) | Step 1에서 반드시 읽는다. 읽기 실패 → `FAIL`(플러그인 설치 이상) |

## 키

키 분류는 아래 마커 안이 canonical이며 `PROFILE.md` frontmatter의 키 집합과 양방향으로 일치한다(`tests/validate_port.py`가 검사). 허용값·빈 값의 의미·프리셋 기본값은 `PROFILE.md`를 따른다(구현 시 init 선택지와 동일).

<!-- config:keys-begin — tests/validate_port.py parity 대상 -->
| 타입 | 키 | 값 규칙 |
|------|----|--------|
| enum | `preset` (go \| node \| custom) · `language` (ko \| en) | trim 후 exact — 빈 값 무효 |
| bool | `e2eEnabled` | true \| false exact |
| string | `buildCommand` `testCommand` `lintCommand` `typeCheckCommand` `makeTestCommand` `runServerCommand` `serverUrl` `apiDocsPath` `e2eLockDir` `reportDir` `feedbackUpstreamRepo` `mainBranch` `featureBranchPrefix` `hotfixBranchPrefix` `commitCoAuthor` | 자유 문자열 — 빈 문자열 유효 |
| array | `sourceDirs` `testDirs` `commitPrefixes` `projectConventions` | 쉼표 구분 (원소 안의 쉼표 비지원) — 빈 배열 유효 |
| block | `topologyModels` | 슬롯 레코드 블록 — compact {슬롯}={model}[@{effort}] 쉼표 나열 또는 {슬롯}=default, 빈 값은 전 슬롯 default; 규칙은 아래 "topologyModels 슬롯" 절 |
<!-- config:keys-end -->

문서 기본값(파일에 없을 때 조회에 표시 — 출처 병기):

| 키 | 기본값 | 출처 |
|----|-------|------|
| language | ko | init |
| reportDir | .codex/harness-reports | PROFILE.md |
| e2eLockDir | 자동 해석 | PROFILE.md |
| e2eEnabled | true | init |
| projectConventions | ["AGENTS.md"] | init |
| feedbackUpstreamRepo | 빈 값 → `SKIPPED:NO_FEEDBACK_UPSTREAM` | PROFILE.md |
| topologyModels | default (agent-topology.md 기본값 표) | agent-topology.md |

그 외 키: `preset: go|node`면 PROFILE.md 프리셋 표 값(출처 `preset`), 아니면 `미설정`.

### topologyModels 슬롯

슬롯은 `orchestrator` · `executor` · `readonly` · `advisor`다. start-workflow `references/agent-topology.md`의
"슬롯 설정"이 canonical이다.

- 레코드 `{ model, effort? }`: model은 `^[A-Za-z0-9._-]+$`, effort는 `minimal|low|medium|high|xhigh|max|tiered`이며 `tiered`는 `executor`만 사용할 수 있다. effort 생략은 해당 슬롯의 기본 effort다.
- 입력(compact): `topologyModels={슬롯}={model}[@{effort}],…`로 지정하고 `{슬롯}=default`는 그 슬롯 자식 줄을 삭제해 기본값으로 복귀시킨다. 입력에서 생략한 기존 슬롯은 보존하며 `topologyModels=`는 전 슬롯 default다. 빈 항목·중복 슬롯·알 수 없는 슬롯·model 패턴 불일치·effort enum 밖·executor 외 tiered 중 하나라도 있으면 값 불일치로 전체를 무효 처리하고 Step 3.1의 `BLOCKED:INVALID_VALUE` 경로를 따른다.
- 저장 형태: 블록 매핑 `topologyModels:`과 연속 자식 `  {슬롯}: { model: "{model}", effort: "{effort}" }`를 쓴다. 자식은 1줄 flow 매핑이고 effort 생략 시 `  {슬롯}: { model: "{model}" }`다. 전 슬롯 default는 자식을 삭제하고 키 줄을 `{}`로 기록한다.
- 조회 셀: 자식 순서대로 compact 한 셀에 표시하고 effort 생략 슬롯은 `@` 없이 표시한다. 키 부재·`{}`는 `default`(출처 `기본값`)다. 자식이 비지원 형태이거나 알 수 없는 슬롯이면 `⚠ 비지원 레이아웃(수정 불가)`로 표시한다.

## Step 1: 로드·구조 판정

1. 플러그인 루트 `PROFILE.md`(이 스킬 파일 기준 `../../PROFILE.md`)를 읽는다(MUST — 키별 허용값·빈 값 의미·프리셋 표의 canonical).
2. 그 문서의 "profile 해석" 규칙으로 `{PROFILE_PATH}`를 확정하고 읽는다. `PROFILE_MISSING`이면 `BLOCKED:NO_PROFILE` + 선택지 "1. `$codex-be-harness:init`으로 profile 생성(사용자) 2. 종료". 상속 시 조회·수정 보고에 절대 경로와 `[Assumption] 메인 워크트리 profile 상속: {경로}`를 표시한다.
3. **EOL·구분선**: EOL은 각 줄의 LF 또는 CRLF(줄별, 혼합 허용). 1행이 `---`(뒤 공백·탭 허용) + EOL이고, 그 다음으로 `---`(뒤 공백·탭 허용) + EOL **또는 파일 끝**이 처음 나오는 줄이 닫는 구분선이다. 본문(닫는 구분선 뒤)은 불투명하며 본문의 `---`는 무시한다. 여는/닫는 구분선이 없거나 루트 키가 중복되면 `BLOCKED:INVALID_PROFILE`(전역 — 수정은 전부 차단. 조회: 닫는 구분선이 없으면 표 없이 종료, 루트 키 중복이면 그 키 행의 값 대신 `⚠ 중복 키(N회)` 표시. 선택지: "1. 직접 편집 후 재호출 2. `$codex-be-harness:init` 실행(사용자)").
4. **줄 분류**(frontmatter 안. 각 줄의 EOL은 분류와 무관하게 그 줄에 붙은 채 보존):

| 분류 | 형태 |
|------|------|
| 루트 줄 | 열-0 `키:` — 키는 `[A-Za-z0-9_-]+`(따옴표 키 `"preset":`·앵커·태그는 비지원) |
| 자식 줄 | 들여쓴 `- 항목` |
| 플레이스홀더 줄 | 분류표 키 K의 활성 루트 줄이 없을 때 **첫 번째** 열-0 `# K:` 줄(정확히 `# ` 한 칸 뒤 키·콜론). 구조 줄이며 중립 줄이 아니다. 잔여부는 활성 줄처럼 구분 공백 + 값 렉심 + 꼬리 주석으로 읽는다 |
| 중립 줄 | 그 외 주석만 있는 줄(들여쓰기 무관 — 두 번째 이후의 동명 플레이스홀더, 활성 키가 있는 키의 `# K:`, 분류표 밖 키의 주석 포함)·빈 줄 |

   - **꼬리 주석** = 따옴표(`"…"`·`'…'`) 밖에서 공백이 선행하는 `#`부터 줄 끝(`release#1`은 값, `release #x`는 값 + 주석, `Bot (team # owner)`는 `Bot (team` + 주석). flow `[…]` 안에서도 같으며 그런 줄은 flow가 닫히지 않아 비지원 레이아웃이 된다.
   - **값 렉심** = `키:` 뒤 구분 공백을 제외한 곳부터 꼬리 주석/후행 공백을 제외한 곳까지. 구분 공백·후행 공백·꼬리 주석은 바이트 보존한다.
   - 블록 범위 = 키 줄부터 **연속된** 자식 줄까지. 그 뒤의 중립 줄은 블록 밖이다. 키 줄과 첫 자식 사이의 중립 줄, 블록 범위 밖에 남는 들여쓴 자식형 줄은 비지원 레이아웃(대상일 때 `BLOCKED:UNSUPPORTED_LAYOUT`)이다.
5. **레이아웃 매트릭스** — 수정 대상 키에만 적용(대상이 아닌 키의 비지원 줄은 바이트 보존, 조회는 ⚠):

| 타입 | 지원 저장 형태 | 그 외 → `BLOCKED:UNSUPPORTED_LAYOUT` |
|------|--------------|------|
| enum·bool·string | 1줄 스칼라: bare / `"…"` / `'…'` / 빈 렉심·`~`·`null`(조회 ⚠, 수정은 렉심 교체 허용) | 블록 스칼라(`\|`·`>`), 여러 줄, 앵커·태그, 따옴표 키 |
| array | 1줄 flow `[…]`(따옴표·이스케이프 인지, 후행 쉼표 허용) / 블록 시퀀스 = `키:` + 연속 자식 `  - 항목` | 여러 줄 flow, 중첩 시퀀스, 자식 사이의 중립 줄 |
| block | 블록 매핑 = `키:` + 연속 자식 `  {슬롯}: { model: …, effort: … }`(자식은 1줄 flow 매핑, 값은 bare 또는 따옴표) / 빈 flow `{}` | 여러 줄 자식, 중첩, 자식 사이의 중립 줄, 알 수 없는 슬롯 키, flow 매핑이 아닌 자식 값 |

   플레이스홀더 줄의 잔여부에도 같은 매트릭스를 적용한다.

## Step 2: 인자 해석

`$ARGUMENTS` 원문을 스캐너로 항목 분리 → 디코딩 → 모드 판정한다.

| 입력 | 모드 |
|------|------|
| (없음) | 전체 조회 → (대화형) 수정 입력 질문 / (비대화형) 조회만 `DONE` |
| 항목 1개, `=` 없음 | 단일 조회 |
| 모든 항목이 `{키}={값}` | 배치 수정 |
| 조회와 할당 혼합 · 조회 항목 2개 이상 | 무효(Step 3.1) |

- **스캐너**(상태 = 밖 / `"…"` 안 / `'…'` 안): 밖에서 공백·탭·CR·LF는 **항상** 항목 구분(`key= v` → `key=`와 `v` = 혼합 → 무효). `"…"` 안은 `\"`·`\\`만 이스케이프(`'`는 문자), `'…'` 안은 모두 문자(`\` 포함). **입력 전체 무효**: 입력 끝에서 따옴표 미종결 · `\` 뒤에 문자 없음 · 탭·CR·LF 외 제어 문자 · 따옴표 안의 탭·CR·LF · 항목 전체 또는 값 전체를 감싸는 위치 이외의 따옴표(`a"b"c`, `key=x"y"`). 유니코드는 허용한다.
- **디코딩(순서 고정)**: ① 항목 전체가 짝 따옴표면 제거(큰따옴표였으면 `\"`→`"`, `\\`→`\` 해제) ② 첫 `=`로 키/값 분리(키 빈 문자열 무효, `=` 없으면 조회 항목) ③ 값 전체가 짝 따옴표면 제거 + 해제(①에서 해제했으면 재해제 없음) ④ 같은 키 중복 무효. 키는 대소문자 exact. 예: `"buildCommand=echo \"x\""` → `echo "x"` · `buildCommand='C:\'` → `C:\` · `commitPrefixes="[Add, Fix:, WIP]"`.
- **값 해석(타입별)**: enum·bool = trim 후 exact(`key=` 무효) / string = 그대로(`key=` → 빈 문자열) / array = 감싼 `[ ]` 선택 제거 → `,` 분리 → 원소 trim → 원소를 감싼 짝 따옴표 제거. 빈 원소(`a,,b`·후행 쉼표)는 무효이며 `key=`·`key=[]`는 빈 배열이다. 원소 따옴표는 값 전체가 따옴표로 감싸인 경우에만 쓴다(`sourceDirs=["a","b"]`는 스캐너 무효, `sourceDirs=a,b` 또는 `sourceDirs='["a","b"]'`) / block = 위 "topologyModels 슬롯" 절의 compact 규칙(`key=` → 전 슬롯 default).
- **기록 형태**: enum·bool bare / string 큰따옴표(내부 `"`·`\` 이스케이프, 빈 문자열은 `""`) / array flow `["a", "b"]`(원소는 string 기록 형태). 기존 블록 시퀀스는 블록을 유지하고 자식 `  - "항목"`도 같은 방식으로 이스케이프하며, 빈 배열은 flow `[]`로 기록한다 / block은 블록 매핑 자식 `  {슬롯}: { model: "…", effort: "…" }`, 전 슬롯 default는 `{}`.
- **인자 없음**: 조회 표 출력 → 비대화형은 `DONE`. 대화형 질문에는 구조화된 사용자 입력 기능이 제공되면 사용하고, 없으면 짧은 일반 질문으로 수집한다. Q1:
  > "1. 변경 없이 종료 2. 값 변경 — Other에 `{키}={값} …` 전체 입력"
  Other 텍스트 → Step 3. 선택 2(텍스트 없음) → Q2 "1. 취소 / Other에 입력" → 텍스트 없으면 `DONE`. 질문은 실행당 `{Q_MAX}`회까지다(Step 3 재입력 포함).

## Step 3: 검증 (판정 순서 고정)

**Step 3.1 입력 오류** — 스캐너 오류·혼합 모드·알 수 없는 키(할당 항목에만 — 조회 항목의 알 수 없는 키는 `⚠ 알 수 없는 키` 행 + `DONE`)·값 불일치 → 배치 전체 무효(파일 불변).
- 대화형: 항목별 사유 + 허용값을 고지하고 배치 전체 재입력을 묻는다(예산 내 1회): "1. 취소 / Other에 전체 재입력".
- 비대화형: 즉시 `BLOCKED:INVALID_VALUE` + 무효 항목 경고(profile 불변).

| 종료 조건 | 결과 |
|----------|------|
| 재입력이 유효 | Step 3.2로 진행 |
| 재입력도 무효(재입력은 1회뿐) | `BLOCKED:INVALID_VALUE` — "1. 올바른 값으로 재호출 2. `$codex-be-harness:init`" |
| 재입력 전에 `{Q_MAX}` 소진(Q1·Q2 사용 후) | `BLOCKED:INVALID_VALUE` — 같은 선택지 |
| 취소 | `DONE`(변경 없음) |

**Step 3.2 대상 키의 구조 오류** — 입력이 유효할 때만 판정한다. 재입력 없음, 예산 미소모.
- 비지원 레이아웃(활성 줄·플레이스홀더 잔여부) → `BLOCKED:UNSUPPORTED_LAYOUT`
- **주석 소실 변경** — 꼬리 주석이 달린 자식 줄을 배열 축소로 삭제해야 하는 경우 → `BLOCKED:UNSUPPORTED_LAYOUT`

하나라도 있으면 배치 전체 차단(파일 불변) + 해당 줄 인용 + 선택지 "1. 직접 편집 후 재호출 2. `$codex-be-harness:init` 실행(사용자)".

## Step 4: 렌더 + 1회 치환

먼저 **변경 없음 판정**: 대상 키의 새 값을 기록 형태로 렌더한 결과가 현재 줄 또는 블록과 바이트 동일하면 그 키는 변경 없음이며 어떤 줄도 건드리지 않는다. 모든 대상 키가 변경 없음이면 치환 없이 Step 5 "변경 없음". 나머지 키만 frontmatter 줄 배열의 사본에서 변환한다. 중립 줄·꼬리 주석은 어떤 규칙도 건드리지 않는다(③이 전환하는 플레이스홀더 줄은 중립 줄이 아니다).

| 규칙 | 조건 | 변환 |
|------|------|------|
| ① | 활성 키 + 1줄 스칼라/flow | 값 렉심만 기록 형태로 교체. 구분 공백·후행 공백·꼬리 주석·EOL 보존. 렉심이 비어 있었으면(`키:` 뒤 공백 전부 = 구분 공백) `키:` + 공백 1 + 새 렉심, 꼬리 주석이 있으면 이어서 (원래 구분 공백에서 1개 뺀 나머지, 없으면 공백 1) + 꼬리 주석, 없으면 아무것도 덧붙이지 않는다 |
| ② | 활성 키 + 블록 시퀀스 | 자식 줄을 정규 형태 `  - "항목"`으로 재구성한다(`PROFILE.md`의 `projectConventions`가 실제 예). 들여쓰기·구분 공백·꼬리 주석·EOL은 같은 위치(i번째→i번째)의 기존 자식에서 유지하고, 신규 항목은 마지막 자식 뒤에 추가한다(들여쓰기·구분 공백 = 마지막 기존 자식과 동일, 꼬리 주석 없음, EOL = 대상 키 줄). 주석 없는 줄만 삭제하며 주석이 있으면 Step 3.2에서 차단한다. 빈 배열은 자식을 삭제하고 키 줄에 `[]`를 기록한다 |
| ②′ | 활성 키 + 블록 매핑(block) | 슬롯별로 자식 줄을 재구성한다 — 기존 슬롯 자식은 같은 줄에서 값만 교체(들여쓰기·구분 공백·꼬리 주석·EOL 보존), `default` 슬롯의 자식 줄은 삭제(꼬리 주석이 있으면 Step 3.2 차단), 신규 슬롯은 마지막 자식 뒤에 추가(들여쓰기·EOL = 마지막 기존 자식, 없으면 공백 2·키 줄 EOL), 전 슬롯 default면 자식 삭제 + 키 줄 `{}` |
| ③ | 키 부재 + 플레이스홀더 줄 | 선두 `# `만 제거해 활성 키 줄로 전환한 뒤 ①(스칼라/flow)을 적용한다. 그 줄의 꼬리 주석·EOL을 보존하고 **뒤따르는 주석 줄(예시·설명)은 손대지 않는다**. block은 전환한 키 줄 **바로 다음**에 자식 줄을 삽입한다(EOL = 키 줄) — 뒤따르는 주석 예시 줄은 그대로 블록 뒤에 남는다. |
| ④ | 그 외 | 닫는 구분선 직전에 스칼라 `키: 값` 또는 배열 flow를 삽입한다(EOL = 닫는 구분선 줄의 것, 그 줄에 종결자가 없으면 여는 구분선 줄의 것). block은 키 줄 + 자식 줄 |

렌더 후 자체 검증: 루트 키 중복 0 · 대상 키 값이 기록 형태와 일치 · 변경 대상 줄 외 바이트 동일. 통과하고 변경 키가 1개 이상이면 frontmatter 전체(여는 구분선부터 닫는 구분선까지)를 **한 번의** 치환으로 반영한다. 치환 직전의 파일 내용이 Step 1에서 읽은 스냅샷과 다르거나 대상 구간이 비유일하면 `FAIL`, 파일 불변.

## Step 5: 보고

수정 결과 표(`키 | 이전 | 이후 | 상태` — 이전/이후 셀은 조회 셀 규칙 그대로, 부재 키는 `(없음)`)를 출력한다. 배치는 전부 `DONE` 또는 전부 `BLOCKED`/`FAIL`이다. 변경 0건(동일 값)이면 "변경 없음" `DONE`. 조회·수정 머리글의 `{PROFILE_PATH}`는 절대 경로로 출력하고, 상속 시 바로 아래에 `[Assumption] 메인 워크트리 profile 상속: {경로}` 1줄을 넣는다. 끝에 "`$codex-be-harness:doctor`로 확인" 1줄을 유지한다. 수정이 있었으면 항상 "진행 중·재개되는 워크플로우는 상태 파일 스냅샷 값을 유지하며 새 값은 다음 실행부터 적용" 1줄을 붙인다.

## 출력 형식

조회(전체/단일):

```markdown
## be-harness Config — {PROFILE_PATH}
| # | 키 | 값 | 출처 | 비고 |
|---|----|----|------|------|
| 1 | preset | go | profile | |
| 2 | typeCheckCommand | "" | profile | 비어 있으면 해당 단계 SKIP (PROFILE.md) |
| 3 | feedbackUpstreamRepo | (없음) → "" | 기본값 | 비어 있으면 SKIPPED:NO_FEEDBACK_UPSTREAM (PROFILE.md) |
| 4 | reportDir | (없음) → .codex/harness-reports | 기본값 | |
| — | ⚠ fooBar | x | 알 수 없는 키 | 어떤 스킬도 읽지 않음 |
변경: `$codex-be-harness:config {키}={값} …` · 파일 생성/전체 재설정: `$codex-be-harness:init`
```

- 출처: `profile`(파일 명시 — 빈 문자열도 profile; 비고 = PROFILE.md 해당 키 주석의 빈 값 의미) / `preset`(preset go|node의 PROFILE.md 프리셋 표 값) / `기본값`(문서 기본값 표) / `미설정`(그 외).
- 셀: 값 렉심만(꼬리 주석·구분 공백 제외), `|`는 `\|`, 블록 시퀀스는 flow 표기로 한 셀.
- 타입 판정: string 키는 `""` 유효, `~`/`null`/빈 렉심 → `⚠ 타입 불일치`; enum·bool 키는 허용값 밖(따옴표 포함) → `⚠ 타입 불일치`; array 키는 flow/블록 시퀀스 외 → `⚠ 타입 불일치`; 비지원 레이아웃 → `⚠ 비지원 레이아웃(수정 불가)`. 전부 읽기 전용 표시.

수정:

```markdown
## be-harness Config — 수정 결과 — {PROFILE_PATH}
| 키 | 이전 | 이후 | 상태 |
|----|------|------|------|
| buildCommand | "go build ./..." | "make build" | DONE |
| e2eEnabled | true | false | DONE |
`$codex-be-harness:doctor`로 확인.
진행 중·재개되는 워크플로우는 상태 파일 스냅샷 값을 유지하며 새 값은 다음 실행부터 적용
```

## 상태 코드

| 코드 | 의미 |
|------|------|
| `DONE` | 조회 완료 / 수정 반영 / 취소·변경 없음 |
| `BLOCKED:NO_PROFILE` | `PROFILE_MISSING` → `init` 안내 |
| `BLOCKED:INVALID_PROFILE` | 구분선 없음·루트 키 중복(전역) |
| `BLOCKED:UNSUPPORTED_LAYOUT` | 대상 키의 저장 형태 비지원 / 주석 소실 변경 |
| `BLOCKED:INVALID_VALUE` | 입력 오류 — 비대화형 즉시 / 대화형 재입력도 무효 또는 `{Q_MAX}` 소진 |
| `FAIL` | 치환 실패(스냅샷 변경·대상 구간 비유일) / 플러그인 루트 `PROFILE.md` 읽기 실패 |

## References

- `../../PROFILE.md` — Step 1에서 반드시 읽는다: 키별 허용값·빈 값 의미·프리셋 기본값·읽기 우선순위·`{PROFILE_PATH}` 해석.
