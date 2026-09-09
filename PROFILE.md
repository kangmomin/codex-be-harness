# be-harness Project Profile

모든 be-harness 스킬은 프로젝트 루트의 **`.codex/be-harness.local.md`** 를 읽어 빌드/테스트/소스 경로 등을 결정한다.
프로젝트 루트에 없고 linked worktree라면 메인 워크트리의 profile을 상속하며, 어디에도 없으면 값을 추측하지 않고
`init` 실행을 안내한 뒤 종료한다(아래 "profile 해석"). Go/Node 자동 탐지와 프리셋은 `init`이 profile 초안을 만들 때만 사용한다.

> profile 은 **값(settings)** 을 담는다. 스킬/에이전트 **동작**을 프로젝트별로 조정하려면 별도의 **Project Overrides** 레이어를 쓴다 → `OVERRIDES.md` 참조.

## 파일 위치

```
<repo-root>/.codex/be-harness.local.md
```

## profile 해석

신규 실행과 단독 스킬은 아래 순서로 `{PROFILE_PATH}`를 확정한다. Verify 재개는 이 조회보다 먼저 run-lifecycle의 snapshot 검증·명령 복원을 수행하며, 보존한 명령을 live profile로 덮지 않는다.

1. `{PROJECT_ROOT}` = `git rev-parse --show-toplevel`(git 저장소가 아니면 cwd). `{PROJECT_ROOT}/.codex/be-harness.local.md`가
   있으면 그것이 `{PROFILE_PATH}`다.
2. 없고 linked worktree라면(`git rev-parse --git-dir`과 `--git-common-dir`이 다르고 common-dir의 basename이 `.git`)
   `{MAIN_WORKTREE}` = common-dir의 부모 디렉토리로 두고 `{MAIN_WORKTREE}/.codex/be-harness.local.md`를 상속한다.
   보고에 `[Assumption] 메인 워크트리 profile 상속: {경로}`를 남긴다.
3. 둘 다 없으면 `PROFILE_MISSING`이다. 값을 추측하지 않고 `init` 실행을 안내한 뒤 mutation 없이 종료한다.
4. 확정한 `{PROFILE_PATH}`를 모든 형제 절차와 서브에이전트 envelope에 전달한다. 형제 절차는 전달받은 경로가 있으면 다시
   해석하지 않는다. Build 워크플로우(`start-workflow`) 안에서 호출될 때는 호출자가 넘긴 `## Profile Snapshot`(frontmatter 값 + resolved 경로)을 profile 값으로 쓰고 frontmatter를 다시 읽지 않는다 — `{PROFILE_PATH}`는 식별·보고용이다. 본문(Project Notes)은 스냅샷 대상이 아니며 읽기 전용으로 참조할 수 있다. Verify의 명령 4종은 run-lifecycle이 보존한 verify-commands.json이 정본이며 재개 때 live profile로 재해석하지 않는다.

## 포맷

YAML frontmatter + 선택적 마크다운 본문.

```markdown
---
preset: go            # go | node | custom
language: ko          # ko | en (유저 대화 언어)

# 빌드/검증 명령 (preset 기본값을 override 하고 싶을 때만 작성)
buildCommand: "go build ./..."
testCommand:  "go test ./..."
lintCommand:  "go vet ./..."
typeCheckCommand: ""       # 해당 없으면 빈 문자열
makeTestCommand: ""        # Makefile 기반 테스트 러너가 있으면 지정

# 서버/E2E
runServerCommand: ""       # 로컬 서버 기동 커맨드 (백그라운드 실행용). 없으면 생략.
serverUrl: "http://localhost:8080"
e2eEnabled: true           # false면 e2e-test, e2e-test-loop 스킵
apiDocsPath: ""            # OpenAPI/Swagger 스펙 파일 경로. 없으면 생략.
e2eLockDir: ""             # E2E 실행 락 디렉토리. 비우면 자동 해석
                           # (/tmp/harness-e2e-locks — work-log/cwd와 무관).
                           # 환경변수 HARNESS_E2E_LOCK_DIR 로도 지정 가능.

# 리포트 출력
reportDir: ""              # E2E 자기 점검·Workflow Report(md) 저장 디렉토리. 비우면 `.codex/harness-reports`
feedbackUpstreamRepo: ""  # Phase 12 보완점 upstream. 비우면 `SKIPPED:NO_FEEDBACK_UPSTREAM`

# 소스 레이아웃
sourceDirs: ["internal/", "cmd/", "pkg/"]
testDirs:   ["internal/", "pkg/"]

# Git
mainBranch: main
featureBranchPrefix: feat/
hotfixBranchPrefix:  hotfix/

# 커밋 컨벤션
commitPrefixes: [Add, Fix, Del, Refactor, Doc, Test, Chore, WIP]
commitCoAuthor: ""         # 비우면 Co-Authored-By 라인 생략

# 에이전트 토폴로지 슬롯 (선택. 생략 시 기본 배정 — 규칙: start-workflow references/agent-topology.md "슬롯 설정")
# topologyModels:
#   executor: { model: gpt-5.6-sol, effort: high }   # executor의 model·effort 교체
#   advisor:  { model: gpt-5.6-sol }                 # model만 지정하면 auto tiered 유지
#   advisor:  { model: gpt-5.6-sol, effort: xhigh }  # fixed advisor effort로 auto보다 우선

# 프로젝트 컨벤션 참조 (convention-check 및 default-conventions에서 사용)
projectConventions:
  - "AGENTS.md"            # 프로젝트 루트 기준 경로
---

# Project Notes

(선택) 프로젝트별 메모. 모든 스킬이 참고.
```

## 프리셋 기본값

### `preset: go`

```yaml
buildCommand: "go build ./..."
testCommand:  "go test ./..."
lintCommand:  "go vet ./..."
typeCheckCommand: ""
makeTestCommand: ""
runServerCommand: ""
serverUrl: "http://localhost:8080"
sourceDirs: ["internal/", "cmd/", "pkg/"]
testDirs:   ["internal/", "pkg/"]
```

### `preset: node`

```yaml
buildCommand: "npm run build"
testCommand:  "npm test"
lintCommand:  "npm run lint"
typeCheckCommand: "npm run typecheck"
makeTestCommand: ""
runServerCommand: "npm run dev"
serverUrl: "http://localhost:3000"
sourceDirs: ["src/"]
testDirs:   ["src/", "tests/", "__tests__/"]
```

### `preset: custom`

모든 필드를 직접 지정해야 한다. 누락 시 경고.

## 읽기 우선순위

profile이 존재할 때 값은 아래 순서로 결정한다:

1. `{PROFILE_PATH}`(위 "profile 해석"으로 확정한 `.codex/be-harness.local.md`)의 YAML 값
2. profile에 선언된 preset의 기본값

profile 자체가 없으면 값을 추측하지 않는다(프로젝트 루트와 메인 워크트리 모두 부재). `go.mod` 또는 `package.json` 탐지는 `init`의 preset 추천에만
사용하며, workflow는 사용자에게 `$codex-be-harness:init` 실행을 안내한다.

## 명령 실행 규칙

- 모든 스킬/에이전트는 하드코딩된 명령 대신 **profile의 `{buildCommand}`, `{testCommand}`** 등을 사용한다.
- profile에 해당 명령이 없거나 비어있으면 해당 단계를 `SKIPPED`로 표기하고 넘어간다 (실패로 보지 않는다).
- 예: `typeCheckCommand`가 비어있으면 타입 체크 단계를 스킵.

## profile 생성

`$codex-be-harness:init` 을 실행하여 대화형으로 생성한다. 기존 파일이 있으면 diff를 보여준 뒤 업데이트.
값 하나를 조회·수정할 때는 `$codex-be-harness:config {키}` / `$codex-be-harness:config {키}={값} …`을 쓴다(init 재실행 없이, 파일 생성은 하지 않음).

모델 추천 배정은 `$codex-be-harness:refresh-models`를 명시적으로 요청할 때만 갱신한다. 일반 실행·진단은 오프라인이다. 추천표는 확정 profile의 부모 아래 `be-harness/models.json`에 두며 profile 상속 시 같은 위치를 공유한다. `topologyModels`는 사용자 override로 보존되고 추천표보다 우선한다. orchestrator override는 legacy 읽기 호환용이며 경고 후 현재 세션을 유지한다. config의 슬롯 default는 override 삭제이며 저장된 추천(없으면 번들 표)으로 돌아간다. 명시 model-only 레코드는 번들 표의 effort를 사용한다.
