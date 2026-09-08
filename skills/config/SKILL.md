---
name: config
description: "be-harness project profile(.codex/be-harness.local.md)의 설정 값을 조회하고 키 단위로 수정한다. '프로필 설정 확인해줘', '설정 값 바꿔줘', '{키} 값 뭐야', '{키}를 {값}으로 바꿔줘' 요청 시, init 재실행 없이 값 하나만 보거나 고칠 때 사용. 파일 생성·환경 진단은 하지 않는다 (init·doctor 담당)."
---

실행 전에 [공통 실행 원칙](../start-workflow/references/execution-policy.md)을 읽는다.

# be-harness Config

실행 전 `.codex/be-harness/common.md`, `.codex/be-harness/skills/config.md`와 `../../PROFILE.md`를 읽는다.
`{PLUGIN_ROOT}`는 실제 설치된 플러그인 루트, `{CWD}`는 프로젝트 경로다. 호출은 전체 조회, 단일 키 조회 또는 `{키}={값}` 배치 수정이다.

## 키

스키마는 아래 키로 닫혀 있다. 알 수 없는 키/중복/타입 오류는 전체 배치를 거부한다.

<!-- config:keys-begin — tests/validate_port.py parity 대상 -->
| 타입 | 키 | 값 규칙 |
|------|----|--------|
| enum | `preset` (go \| node \| custom) · `language` (ko \| en) | trim 후 exact — 빈 값 무효 |
| bool | `e2eEnabled` | true \| false exact |
| string | `buildCommand` `testCommand` `lintCommand` `typeCheckCommand` `makeTestCommand` `runServerCommand` `serverUrl` `apiDocsPath` `e2eLockDir` `reportDir` `feedbackUpstreamRepo` `mainBranch` `featureBranchPrefix` `hotfixBranchPrefix` `commitCoAuthor` | 자유 문자열 — 빈 문자열 유효 |
| array | `sourceDirs` `testDirs` `commitPrefixes` `projectConventions` | 쉼표 구분 (원소 안의 쉼표 비지원) — 빈 배열 유효 |
| block | `topologyModels` | 슬롯 레코드 블록 — compact {슬롯}={model}[@{effort}] 쉼표 나열 또는 {슬롯}=default, 빈 값은 전 슬롯 default; 규칙은 아래 "topologyModels 슬롯" 절 |
<!-- config:keys-end -->

## 조회와 경로

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/config/assets/profile.py" resolve --domain be --cwd "{CWD}"
```

helper의 profile_path가 `{PROFILE_PATH}`다. 프로젝트 루트의 `.codex/be-harness.local.md`를 우선하며 linked worktree에 없으면 메인 worktree 것을 상속한다. 양쪽에 없으면 `BLOCKED:NO_PROFILE`; init 안내 후 파일을 만들지 않는다. preset은 자동 추정하지 않는다.
`values`, `sources`, `commands`, `diagnostics`로 `키 | 값 | 출처 | 비고`를 보고한다. 단일 조회도 같은 출력에서 해당 키만 표시한다. 명시적 빈 값은 부재와 다르며 BE 명령의 빈 값은 SKIP이다.

## 배치 수정

1. 요청을 타입이 있는 JSON으로 변환한다. 명령 문자열을 shell 코드로 보간하지 않는다. 배열은 JSON 문자열 배열이며 원소 안 쉼표도 보존한다. 결정되지 않은 값만 짧게 확인한다.
2. `profile.py edit --domain be --cwd "{CWD}"`에 JSON을 stdin 또는 실행 소유 `--changes` 파일로 전달해 preview한다. heredoc은 따옴표 delimiter를 사용하고 본문과 충돌하지 않게 한다.
3. PREVIEW에서 의도한 키만 바뀌었는지 확인하고 **같은 JSON**에 `--apply --expected-sha256 "{sha256_before}"`를 추가한다. preview는 추가 사용자 승인 단계가 아니다.
4. 파일 잠금·해시 재검사 후 frontmatter를 한 번의 원자 교체로 반영한다. 본문·EOL·대상 밖 줄·주석은 보존한다. STALE_PROFILE은 새 preview로 해결하며 수동 전체 덮어쓰기로 우회하지 않는다. changed:false면 파일을 쓰지 않는다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/config/assets/profile.py" edit --domain be --cwd "{CWD}" <<'PROFILE_JSON'
{"language":"en","sourceDirs":["src/","path,with,commas/"]}
PROFILE_JSON
```

슬롯은 `orchestrator` · `executor` · `readonly` · `advisor`다. `tiered`는 `executor`와 `advisor`만 허용한다.
`topologyModels`의 슬롯 레코드는 model(필수)과 effort(선택)뿐이다. provider 전환은 미지원이며 모델/effort 허용값은 `../start-workflow/references/agent-topology.md`를 따른다.
compact 입력을 JSON 슬롯 객체로 바꾼다. `{"topologyModels":{"executor":{"model":"example-model","effort":"high"},"advisor":null}}`처럼 슬롯 단위로 교체하며 null은 해당 슬롯 삭제, 빈 객체는 모든 슬롯 기본값 복귀다. 다른 슬롯/기존 레코드의 필드를 상속하지 않는다.
기존 무효 슬롯이 수정/삭제 없이 남으면 `BLOCKED:INVALID_PROFILE`이다. 주석 소실·비지원 layout·symlink 쓰기는 `BLOCKED:UNSUPPORTED_LAYOUT`이다.

## 보고

`키 | 이전 | 이후 | 상태`와 실제 `{PROFILE_PATH}`를 보고한다. 상속이면 `[Assumption] 메인 워크트리 profile 상속: {경로}`를 명시한다. 수정도 이 상속 경로에 반영한다.
상태는 DONE/PREVIEW 또는 BLOCKED:NO_PROFILE/INVALID_VALUE/INVALID_PROFILE/UNSUPPORTED_LAYOUT, 동시 변경은 STALE_PROFILE이다. 실패 시 원래 파일을 보존한다.
`$codex-be-harness:doctor`로 확인한다. 진행 중·재개되는 워크플로우는 `## Profile Snapshot`을 유지하며 새 값은 다음 실행부터 적용한다. 오버라이드·상태·인증 설정은 수정하지 않는다.
