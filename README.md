# codex-be-harness

기존 `be-harness`의 Spec → Plan → TDD → 품질 루프 → PR workflow를 Codex-native skill로 제공한다.

## 호환 범위

- Build mode: Phase 1~12
- Analyze mode: Phase A1~A4
- Verify mode: Phase V1~V5
- profile, project override, TDD Test Map, 회귀 baseline, Assumption Gate
- bounded simplify/quality/E2E loop와 기존 상태·보고 형식

Fullstack으로 판정되면 BE로 조용히 진행하지 않고 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 종료한다. Minmos overlay와 원격 feedback 제출은 0.2.0 범위에도 포함하지 않는다. 세부 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)를 참고한다.

`start-workflow`는 승인된 고정 topology를 사용한다. Sol High는 승인·상태·판정을 조정하고, Terra
High/Max는 source/test/API 문서 등 업무 변경 파일의 유일한 writer 및 승인된 push/PR 실행자이며, Luna xHigh는 읽기 전용 검토를 맡는다.
Phase 4.3은 매번 새 Sol Max advisor context로 Plan만 검증한다. 모든 고정 spawn은 `fork_turns:none`이다.

## 0.3.0 변경

현재 버전: `codex-be-harness@0.3.0`. 관찰 가능한 동작 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)의 "0.3.0 deviations"에 있다.

- `config` 스킬: profile 값 조회와 `{키}={값}` 배치 수정(init 재실행 없이, 파일 생성 없음). linked worktree에서는 상속된 메인 워크트리 profile에 반영하고 `[Assumption]`으로 보고한다.
- 키 parity 가드: `tests/validate_port.py`가 `PROFILE.md` frontmatter 키 집합과 config 키 마커를 양방향 대조한다.

## 0.2.0 변경

관찰 가능한 동작 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)의 "0.2.0 deviations"에 있다.

- profile 해석: linked worktree는 메인 워크트리의 `.codex/be-harness.local.md`를 상속한다.
- 질문 배칭: `request`는 spec-only에서 남은 질문을 한 턴에 묶고 기본값을 붙인다. `init`은 전체 필드 표를 한 번에 확인한다.
- Phase 1 중복 작업 스캔(`BLOCKED:DUPLICATE_IN_PROGRESS`), Phase 12 Workflow Report md 저장, 서브에이전트 대기 규약.
- `e2e-test` `mode: workflow`(인증 부재 시 `SKIPPED:NO_AUTH`), 기준 브랜치는 profile `mainBranch`.

## 주요 skill

| skill | 설명 |
|---|---|
| `start-workflow` | Build/Analyze/Verify 전체 workflow |
| `request` | 단계적 질문과 코드 분석으로 Technical Spec 생성 |
| `unit-test` | Spec 추적 ID 기반 단위 테스트 및 Red 단계 |
| `simplify-loop` | 네 관점 검토와 단일 writer 기반 bounded 단순화 |
| `convention-check` | profile과 프로젝트 문서 기반 컨벤션 검사 |
| `e2e-test` / `e2e-test-loop` | E2E 실행 및 최대 5회 수정 루프 |
| `commit*` / `resolve-assumption` | 논리 커밋, push/PR, Assumption Gate |
| `init` / `doctor` | `.codex/be-harness.local.md` 생성 및 진단 |
| `config` | profile 값 조회·키 단위 수정 (init 재실행 없이) |

Codex CLI 또는 IDE에서 `$`로 설치된 skill을 선택한다. 예:

```text
$codex-be-harness:start-workflow 주문 취소 API를 추가해줘
$codex-be-harness:start-workflow --verify internal/order
$codex-be-harness:init
$codex-be-harness:config reportDir=.codex/reports
```

## 개발 검증

```bash
python3 tests/validate_port.py
python3 /home/dev/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

이 저장소는 로컬 marketplace를 자동으로 변경하거나 플러그인을 전역 설치하지 않는다.
