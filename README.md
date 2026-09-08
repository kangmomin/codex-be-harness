# codex-be-harness

기존 `be-harness`의 Spec → Plan → TDD → 품질 루프 → PR workflow를 Codex-native skill로 제공한다.

작업 계약에 대상·현재 기준·완료 증거·승인 범위를 기록하고 다음 에이전트까지 전달한다. 동일 승인 재사용, 근거가 있는 추가 검증, 역할별 권한 검증은 기존 [공통 실행 원칙](skills/start-workflow/references/execution-policy.md)을 통해 적용한다. Astra용 변환과 유지하는 호환성 경계는 [선택적 동기화 기준](COMPATIBILITY.md#선택적-동기화-기준)에 기록한다.

## 호환 범위

- Build mode: Phase 1~12
- Analyze mode: Phase A1~A4
- Verify mode: Phase V1~V5
- profile, project override, TDD Test Map, 회귀 baseline, Assumption Gate
- bounded simplify/quality/E2E loop와 기존 상태·보고 형식

Fullstack으로 판정되면 BE로 조용히 진행하지 않고 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 종료한다. Minmos overlay와 원격 feedback 제출은 0.2.0 범위에도 포함하지 않는다. 세부 차이는 [COMPATIBILITY.md](./COMPATIBILITY.md)를 참고한다.

`start-workflow`는 승인된 고정 topology를 사용한다. Sol High는 승인·상태·판정을 조정하고, Terra
High/Max는 source/test/API 문서 등 업무 변경 파일의 유일한 writer 및 승인된 push/PR 실행자이며, Luna xHigh는 읽기 전용 검토를 맡는다.
기본 Terra executor effort는 `high`다. Phase 4.3 advisor는 auto(`tiered`)에서 낮고 명확한 D 1~3 작업을
`SKIPPED:ADVISOR_NOT_REQUIRED`로 넘기고, D 4~8은 xhigh, D≥9 또는 동시성·데이터 정합성/이관·8+ 파일 설계·3 레이어·공유 구조 변경은 max로 새 context에서 Plan만 검증한다. fixed advisor effort는 이 선택보다 우선한다. 모든 고정 spawn은 `fork_turns:none`이다.

일반 Codex task에 이 원칙을 한 번 적용하려면 유효한 전역 AGENTS 파일에 작업 영향·불확실성에 비례해 탐색과 검증을 넓히고, 필수 검증 통과 뒤 새 실패·미검증 가설·수정 영향이 없으면 반복을 멈춘다는 지침을 수동으로 둘 수 있다. 이 저장소의 `AGENTS.md`는 repository 범위 지침이며 전역 파일과 다르다. base와 plan effort 예시는 각각 `model_reasoning_effort = "high"`, `plan_mode_reasoning_effort = "high"`다. 이는 개인 `~/.codex` 설정이나 현재 실행 effort를 자동 변경하지 않는 1회 안내이며 새 task부터 적용된다.

## 0.6.3 변경

현재 버전: `codex-be-harness@0.6.3`.

- executor 기본 effort를 high로 두고, advisor auto를 `N/A|xhigh|max`으로 Phase 4.2 뒤 resolve한다. fixed override와 legacy executor tiered 호환을 유지하며 symbolic effort는 spawn하지 않는다.
- Build 상태에는 concrete advisor 결정을, Analyze/Verify 신규 상태에는 `executor=N/A,advisor=N/A`를 기록한다. 비례 탐색·검증 종료 원칙과 선택적 전역 AGENTS 안내를 추가했다.

## 0.6.2 변경

이전 버전: `codex-be-harness@0.6.2`.

- 실제 파일 내용 지문 v2로 변경 누락을 막고 내용이 같은 커밋의 검증 근거를 재사용한다. 통합 테스트는 단위 테스트와 별도로 기록·합산한다.
- 검토한 추론 태그 리터럴의 좁은 제외, Go 테스트 후보 탐색, Verify 명령 보존을 적용했다.
- `bash scripts/verify.sh`와 CI를 실제 Python·문서 렌더링 테스트에 연결했다. 호환성 경계와 검증 결과는 [COMPATIBILITY.md](COMPATIBILITY.md)와 [SYNC-REPORT.md](SYNC-REPORT.md)에 있다.

## 0.6.1 변경

이전 버전: `codex-be-harness@0.6.1`.

- AI 활용성 리뷰를 반영해 작업 계약·승인 재사용·인계·완료 기준을 보완했다.
- Astra 행동 지침에 맞춰 요구사항 기반 테스트, 역할별 권한 검증, 로그 마스킹과 가설 검증을 적용했다.
- 기존 모델 슬롯·필수 검증 경계를 유지하며, 상세 반영과 검증 결과는 [SYNC-REPORT.md](SYNC-REPORT.md)에 기록했다.

## 0.6.0 변경

이전 버전: `codex-be-harness@0.6.0`.

- upstream 작업 트리의 `be-harness@1.5.4`와 기존 공통 의존 스킬(`common@0.14.2`) 동기화. 원본 HEAD와 파일별 SHA-256은 [UPSTREAM-SYNC.json](UPSTREAM-SYNC.json)에 기록한다.
- 실행별 경로/명시적 `--resume`, schema 4, 결과 JSON·검증 tree·리뷰 범위·writer 종료 계약을 연결했다. 구 schema 2/3 실행은 새 실행으로 시작해야 한다.
- E2E는 v2 socket-resource lease, 수정 빌드 검증, 중단 이력 보존, JSON 기반 리포트를 사용한다. Python 3.9+/POSIX가 필요하며 동일 자원의 v1 실행과 혼용하지 않는다.
- config는 원자적 preview/apply와 상속 profile을 지원한다. Codex topologyModels·모델/effort·단일 writer 경계를 유지한다.
- commit은 사용자 index 보존과 현재 HEAD Gate를 적용한다. doc-gen은 고정 Node/Chromium 의존성으로 실제 Mermaid·오프라인 HTML을 검증한다.
- [공통 실행 원칙](skills/start-workflow/references/execution-policy.md): 문맥 기반 자율 완료, 기존 승인 재사용, 지침 충돌 설명, 변경에 맞는 검증을 실행 스킬에 적용한다. 모델 배정과 필수 Gate는 기존 계약을 따른다.

upstream 동기화는 [선택적 동기화 기준](COMPATIBILITY.md#선택적-동기화-기준)을 따른다. 공식 모델 가이드를 확인하고 기능 계약·필요한 수정만 채택하며, 호스트 종속 동작은 Codex에 맞게 변환한다. 채택·변환·제외·보류 근거는 `SYNC-REPORT.md`, 원본과 적용 결과의 해시는 `UPSTREAM-SYNC.json`에 남긴다.

## 0.5.1 변경

이전 버전: `codex-be-harness@0.5.1`.

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
- 결정적 단계 스크립트 4개를 당시 upstream `2d7a01c`와 바이트 동일하게 도입했다. 이후 변경된 파일의 현재 해시와 출처는 `UPSTREAM-SYNC.json`에 기록한다.
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
python3 -m pip install PyYAML==6.0.3
npm ci --prefix skills/doc-gen/assets
bash scripts/verify.sh
python3 /home/dev/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

이 저장소는 로컬 marketplace를 자동으로 변경하거나 플러그인을 전역 설치하지 않는다.
