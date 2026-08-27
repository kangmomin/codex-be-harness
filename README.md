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

## 0.5.1 변경

현재 버전: `codex-be-harness@0.5.1`.

- `e2e-lock.sh`: 락 디렉토리 `mkdir`의 비-EEXIST 실패(권한·파일시스템)를 대기 없이 즉시 `ERROR` exit 1로 끝낸다 → e2e-test `BLOCKED:LOCK_UNAVAILABLE`(upstream be-harness 1.5.1 미러)
- `render_e2e_report.py`: upstream 1.5.1 사본으로 갱신 — dead option `--level full-command` 제거(SHA-256 고정값 갱신)
- `config`: `topologyModels` 블록에 기존 무효 슬롯이 남는 수정은 `BLOCKED:INVALID_PROFILE`(덮어쓰기·`{슬롯}=default` 삭제만 진행)

## 0.5.0 변경

관찰 가능한 동작 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)의 "0.5.0 deviations"에 있다.

- 토폴로지 역할 슬롯 설정: profile `topologyModels`(block)로 `orchestrator` · `executor` · `readonly` · `advisor` 슬롯의 model/effort를 교체한다(`$codex-be-harness:config topologyModels=executor=gpt-5.6-sol@high,…`). 역할 라벨(Sol High / Terra High·Max / Luna xHigh / Sol Max)과 권한 경계는 불변.
- `--topology-models {슬롯}={model}[@{effort}],…`: 실행 한정 교체(profile 미기록). resolve 순서는 플래그 > profile > 기본값, 무효 슬롯은 기본값 + 경고.
- 폴백 없음: 설정 model/effort 거부는 `model_unavailable({슬롯}:{사유})` + 기존 Phase 계약. provider 전환은 Codex spawn 제약으로 미지원.
- 상태 파일 스키마 3: `## Flags` `TOPOLOGY_MODELS`, Snapshot `topologyModels`. 0.4.0(`SCHEMA: 2`) 상태 파일은 재개 시 기본값으로 1회 보완(원자 교체).
- `doctor`가 `topologyModels` 슬롯을 정적 검증한다(`INVALID_SLOT`).

## 0.4.0 변경

관찰 가능한 동작 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)의 "0.4.0 deviations"에 있다.

- 검증 티어(`light`/`standard`)와 `--tier standard`: 코드 복잡도·영향 리스크에 따라 저위험 작업의 검증 범위를 축소하고 승격 조건 충족 시 `standard`로 전환한다.
- 결정적 단계 스크립트 4개: `risk_facts.py`, `test_failures.py`, `workflow_archive.py`, `render_e2e_report.py`는 upstream `2d7a01c`와 바이트 동일하며 SHA-256을 고정 검증한다.
- 상태 파일 스키마 2: Flags·Profile Snapshot·Verification Tier·Final Decisions·Artifacts를 고정하고 스키마 불일치 재개를 fail-closed 처리한다.
- Phase 12는 슬림 Workflow Report 1회 작성과 md 아카이브 1회 생성으로 단일화하고 HTML 노트를 폐지한다.
- E2E는 md 자기 점검 리포트와 `--smoke`를 지원하며 `BLOCKED:LOCK_UNAVAILABLE`이면 Phase 10 Gate를 보류한다.

## 0.3.0 변경

관찰 가능한 동작 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)의 "0.3.0 deviations"에 있다.

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
| `start-workflow` | Build/Analyze/Verify 전체 workflow — 검증 티어(light/standard, `--tier standard`), md 아카이브, 토폴로지 슬롯(`--topology-models`) |
| `request` | 단계적 질문과 코드 분석으로 Technical Spec 생성 |
| `unit-test` | Spec 추적 ID 기반 단위 테스트 및 Red 단계 |
| `simplify-loop` | 네 관점 검토와 단일 writer 기반 bounded 단순화 |
| `convention-check` | profile과 프로젝트 문서 기반 컨벤션 검사 |
| `e2e-test` / `e2e-test-loop` | E2E 실행(`--smoke`) 및 최대 5회(smoke 3회) 수정 루프, md 자기 점검 리포트 |
| `commit*` / `resolve-assumption` | 논리 커밋, push/PR, Assumption Gate |
| `init` / `doctor` | `.codex/be-harness.local.md` 생성 및 진단 (`topologyModels` 슬롯 검증) |
| `config` | profile 값 조회·키 단위 수정 (init 재실행 없이, `topologyModels` 슬롯 포함) |

Codex CLI 또는 IDE에서 `$`로 설치된 skill을 선택한다. 예:

```text
$codex-be-harness:start-workflow 주문 취소 API를 추가해줘
$codex-be-harness:start-workflow --tier standard 주문 취소 API를 추가해줘
$codex-be-harness:start-workflow --topology-models executor=gpt-5.6-sol@high 주문 취소 API를 추가해줘
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
