> `start-workflow`의 세션 기반 에이전트 토폴로지 단일 원천이다. Build, Analyze, Verify 모두 이 문서를
> 먼저 읽는다. Phase 순서·상태 코드·반복 상한·출력 머리글·승인 Gate는 다른 참조 문서의 계약을 따른다.

# Session agent topology

## 역할과 모델

<!-- topology:defaults-begin -->
| 슬롯 | 역할 라벨 | 기본 model | 기본 effort |
|------|-----------|-----------|-------------|
| `orchestrator` | Orchestrator | `session` | `inherit` |
| `executor` | Worker | `gpt-5.6-terra` | `high` |
| `readonly` | Readonly | `gpt-5.6-luna` | `xhigh` |
| `advisor` | Advisor | `gpt-6-astra` | `tiered` |
<!-- topology:defaults-end -->

| 슬롯 | 권한 |
|------|------|
| `orchestrator` | 사용자 승인 처리, Phase 상태·배리어·파일 소유권, 명령 실행·commit 조정, 최종 판정·보고 |
| `executor` | 작업 트리 편집, 테스트/빌드 수정, API 문서, 승인된 push/PR, 승인된 Phase 12 remediation |
| `readonly` | 탐색, 엣지 케이스, 리뷰, 품질 스캔, scope/read-back, Analyze/Verify 읽기 전용 작업 |
| `advisor` | Phase 4.3 fresh-context Plan 검증 전용 |

역할명은 모델과 독립적이다. Orchestrator는 사용자가 연 현재 세션이며 별도로 spawn하지 않는다.
Worker는 기존 `executor`, 탐색·리뷰를 맡는 Readonly는 기존 `readonly` 슬롯을 사용한다.
Advisor는 독립적인 Plan 검증 역할이다. 슬롯 이름과 Phase 권한 경계는 유지한다.

위 표는 번들 초기 배정의 단일 원천이다. 일반 workflow에서는 온라인 모델 조사·비교·갱신을 하지 않는다.
`$codex-be-harness:refresh-models`를 사용자가 요청할 때만 최신 추천을 조사해 프로젝트 추천표를 갱신한다.
기본 모델은 영구 고정 정책이 아니며, 현재 실행에서는 확정 배정을 유지한다.

모든 하위 역할 spawn은 `fork_turns:none`을 사용한다. 각 슬롯의 확정 model/effort를 다른 값으로 조용히
대체하지 않고 역할 프롬프트에 명시한다. `session@inherit`는 현재 세션의 역할 표기이며 spawn 인자가 아니다.

### 슬롯 설정 (`topologyModels`)

슬롯은 `orchestrator` · `executor` · `readonly` · `advisor`이며 위 표와 1:1로 대응한다.
profile의 선택 block 키 `topologyModels`는 슬롯별 배정을 교체한다.

```yaml
topologyModels:
  executor: { model: {model}, effort: high }   # executor의 model·effort 교체
  advisor:  { model: {model}, effort: xhigh }  # advisor effort만 조정
```

각 레코드는 `{ model, effort? }`다. `model`은 OpenAI 모델 id이며 `^[A-Za-z0-9._-]+$`를 따라야 하고
provider 필드는 없다. `effort`는 `minimal|low|medium|high|xhigh|max|ultra|tiered` 중 하나이고,
`tiered`는 `executor`와 `advisor`만 사용할 수 있다. 생략한 슬롯은 저장된 추천(없으면 번들 표)을 쓰고, 명시 레코드에서 effort를 생략하면
번들 표의 effort를 쓴다. 낮은 우선순위 레코드의 effort를 상속하지 않는다. executor의 명시적 호환 `tiered`는 난이도 1~8에서 `high`, 9~10에서 `max`다.

compact 표기는 `{슬롯}={model}[@{effort}]`를 쉼표로 나열하고, `{슬롯}=default`로 해당 슬롯을
기본값으로 되돌린다. 마지막 `@` 뒤를 effort로 해석한다. 빈 항목·중복 슬롯·알 수 없는 슬롯·model
패턴 불일치·effort enum 밖·executor/advisor 외 슬롯의 `tiered` 중 하나라도 있으면 입력 전체가 무효다.

start-workflow Pre-flight는 신규 실행에서 한 번만 다음 오프라인 helper로 resolve한다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/refresh-models/assets/models.py" resolve --cwd "{CWD}"
```

플래그가 있으면 원문을 shell에 안전하게 전달한 `--topology-models "{값}"`를 추가한다.
반환된 `models`, `sources`, `diagnostics`, `models_path`, `sha256`를 사용한다.
슬롯 레코드 우선순위는 `실행 플래그 --topology-models > profile topologyModels > 저장된 추천표 > 번들 기본값`이다.
추천표 경로는 확정 `{PROFILE_PATH}`의 부모 디렉토리 아래 `be-harness/models.json`이다. profile이 메인
worktree에서 상속되면 추천표도 그 위치를 읽고 갱신한다. 플러그인 설치 캐시·전역 설정은 쓰지 않는다.
profile의 무효 슬롯은 경고하고 저장된 추천(없으면 번들 표)을 쓴다. profile은 바꾸지 않는다.
플래그가 무효면 helper는 오류를 반환한다. 대화형은 재입력을 1회 받고 여전히 무효면 플래그 없이
resolve하며 경고한다. 비대화형도 플래그를 무시하고 경고한다. 무효 배치를 부분 적용하지 않는다.
플래그의 `{슬롯}=default`는 profile을 건너뛰고 저장된 추천(없으면 번들 표)을 선택한다.
config의 `{슬롯}=default`는 profile 슬롯 삭제로 같은 추천으로 돌아간다.
기존 orchestrator override는 읽기 호환만 유지하며 `SESSION_ORCHESTRATOR` 경고와 함께 무시한다.
`orchestrator=session@inherit`로 현재 세션을 사용하며 모델·effort 변경 또는 별도 bootstrap을 하지 않는다.
손상된 추천표는 `INVALID_MODELS`로 중단하고 기존 파일을 보존한다. 자동 초기화나 온라인 복구는 하지 않는다.

확정 문자열 `{TOPOLOGY_MODELS}`는
`orchestrator={model}@{effort},executor={model}@{effort},readonly={model}@{effort},advisor={model}@{effort}`
형식과 4슬롯 고정 순서를 쓴다. executor의 명시적 `tiered`는 Phase 2 난이도 확정 시 `high|max`로 치환한다.
advisor의 `tiered`(기본 및 model-only 포함)는 Phase 4.2 완료 뒤 첫 4.3 직전에 `N/A|xhigh|max`로 치환한다.
Analyze/Verify 신규 실행은 executor와 advisor를 쓰지 않으므로 `executor=N/A,advisor=N/A`로 기록한다.
spawn 인자로는 확정된 concrete model/effort만 전달한다. `tiered`·`N/A`·`-`는 절대 전달하지 않으며
미확정 또는 unused 슬롯의 availability 검사와 spawn도 금지한다.

provider 전환 미지원(Codex spawn 제약): `model`은 OpenAI 모델 id만 받으며 spawn 단위 provider 전환은 지원하지 않는다.

설정된 슬롯의 model/effort가 거부되면 진단에 `model_unavailable({슬롯}:{사유})`를 남기고 해당 Phase의
기존 `CODEX-UNAVAILABLE` / `SKIPPED:AGENT_DIED` / `BLOCKED:AGENT_DIED` 계약을 적용한다. 기본값으로
되돌리거나 다른 model/effort로 재시도하지 않는다. 영구 변경은
`$codex-be-harness:config topologyModels=…`, 실행 한정 변경은 `--topology-models`를 사용하며 실행 한정
변경은 profile에 기록하지 않는다.

### Worker effort 선택

난이도 1~8은 Worker High, 9~10은 Worker Max다. 난이도 산정의 리스크에는 보안, 데이터 이관,
복잡한 API/계약 변경을 반영한다. 이 기준 외의 모호한 승격 규칙은 만들지 않는다.
executor 슬롯은 기본 `high`다. 추천표 또는 profile/플래그가 `tiered`를 지정했을 때만 이 규칙으로
확정한다. profile이나 플래그가 `high`·`max` 등 고정 effort를 지정하면 난이도와 무관하게 그 값이다.

### Advisor effort 선택

advisor 슬롯의 fixed effort(`minimal|low|medium|high|xhigh|max|ultra`)는 항상 실행하며 자동 선택보다 우선한다.
model만 지정하거나 effort가 `tiered`면 자동이다. Phase 4.2의 Plan 반영 뒤 `D=max(A,B)`를 다시 계산한다.
어느 축의 근거라도 `UNKNOWN`이면 `D=max(D,7)`이다. 다음 신호 중 하나라도 있으면 `max`다: `D>=9`, 동시성 제어,
데이터 정합성 또는 이관, 설계 대상 파일 8개 이상, Presentation/Service/Repository 3개 레이어 전체 변경, 공유 구조 변경.
그 외 D 4~8은 `xhigh`, D 1~3이며 UNKNOWN·max 신호가 없으면 `N/A`와
`SKIPPED:ADVISOR_NOT_REQUIRED`다. advisor에는 현재 리뷰 관점과 Spec/Plan의 가장 중요한 결정 질문 1개만 전달한다.

Phase 4.4 직전에 최종 Plan·사용자 정정·승인 범위를 포함한 A/B·UNKNOWN·max 신호를 항상 다시 평가한다. required minimum이
`N/A→xhigh|max` 또는 `xhigh→max`로 상승한 경우에만 기존 `{PLAN_MAX}`의 다음 iteration 하나를 소비해 fresh advisor를
실행한다. 남은 slot이 없으면 `BLOCKED:MAX_ITERATIONS`; 이미 실행한 effort가 required minimum 이상이면 재실행·downshift하지 않는다.
fixed advisor는 자동 승격 대상이 아니다.

## Session entry (bootstrap 대체)

현재 사용자 대면 세션이 Orchestrator를 직접 맡는다. orchestrator를 spawn하거나 요청·승인을 별도
에이전트에 relay하지 않는다. Pre-flight에서 검증한 RUN 경로를 계속 사용하며 create를 다시 실행하지 않는다.
새 요청/명시적 재개는 run-lifecycle.md를 먼저 따르고 같은 task의 사용자 응답은 현재 실행 경로를 유지한다.
Advisor의 verdict나 다른 subagent 결과는 사용자 승인을 대체할 수 없다.

사용자 입력이 필요하면 `USER_INPUT_REQUIRED: {질문}` 계약으로 직접 질문하고 **같은 orchestrator task**에서
응답을 반영한다. 이 continuation은 새 bootstrap을 만들지 않으며 Phase 4.4 승인도 현재 세션에서 처리한다.
Pre-flight가 Phase 5 전에 실패하면 상태 파일을 만들지 않는다. 원인과 중단 사실을 보고하고
코드·git·원격 효과 없이 종료한다. orchestrator spawn 자체가 없으므로 bootstrap 모델 가용성 검사도 없다.

재개 시 하위 슬롯과 concrete advisor 결정은 기존 `TOPOLOGY_MODELS`를 재사용하고 추천표를 다시 읽지 않는다.
legacy 상태에 concrete orchestrator 모델이 있으면 과거 기록을 보존하되 역할은 현재 세션이 맡는다고 보고한다.
새로 수행하는 Phase의 orchestrator 표기는 `session@inherit`로 남긴다. 호스트가 실제 모델·effort를 제공하면
진단에 별도로 기록할 수 있지만 추측하거나 세션 설정을 변경하지 않는다.

## Writer와 상태 경계

Orchestrator만 `{STATE_FILE}`의 `Current Phase`, `Phase Assignments`, `Remaining Phases`, `Phase Results`를
작성한다. Worker, Readonly, Advisor는 `{STATE_FILE}`과 Phase Results를 쓰지 않고 구조화된 결과만 반환한다. Worker가 E2E 서버를
시작하면 PID/세션 핸들과 정리 결과를 반환하고 Orchestrator가 상태에 기록한다.

Orchestrator는 `{RUN_DIR}`와 report 같은 운영 메타데이터를 쓸 수 있지만 source, test, API 문서 등 작업
트리 내용은 직접 편집하지 않는다. 작업 트리의 단일 writer는 해당 시점에 배정된 Worker다.
Phase 8.5의 단일 writer, Phase 6 barrier, Phase 8.8의 isolation은 이 경계보다 우선하는 예외가 아니다.

## Phase routing

| 범위 | 담당 | 실행 규칙 |
|------|------|-----------|
| Build 1~5, 6/8 barrier·commit, 7/8 명령·판정, 10 Assumption Gate, 12 상태·사용자 결정·보고 | Orchestrator | 승인과 상태를 소유하며 worktree를 직접 편집하지 않음 |
| 1 edge-case 보강, 4.2, 8.2, 8.3, 8.4, 8.8, 11 | Readonly | 읽기 전용; 8.8에는 Spec/Plan/state/Test Map을 전달하지 않음 |
| 4.3 | Advisor | auto면 N/A·xhigh·max 중 하나, fixed면 명시 effort; 실행 시 매 iteration 새 fresh context로 spawn, 최대 `{PLAN_MAX}`회(standard 5 / light 2) |
| 6.1 Red, 6.2 Green, 7 build-fix, 8.5, 8.6, 8.7, 9, 10 승인된 push/PR, 12 승인된 remediation | Worker | Orchestrator가 명령/승인/상태를 조정하고 Worker가 수정 또는 외부 효과를 수행 |
| Analyze A1/A2/A4, Verify V1/V2/V5 | Orchestrator | 읽기/명령/보고 소유 |
| Analyze A3, Verify V3/V4 | Readonly | 읽기 전용 구조화 결과 반환 |

Advisor의 결과를 Plan에 반영하거나 기각하는 판단은 Orchestrator만 한다. Phase 12에서 Worker remediation이
diff를 바꾸면 Orchestrator는 Phase 10 Assumption Gate와 Phase 4.4에서 승인된 외부 효과 범위를 다시 확인한 뒤에만
push/PR을 재개한다.

## Unavailable과 agent died

모델 capability 미가용(`model_unavailable(...)`)과 실행 중 사망을 구분한다. 진단에는
`model_unavailable(...)`만 기록하고, 타 모델로 대체하거나 모델/effort를 낮춰 재시도하지 않는다.

- Phase 4.3의 concrete advisor를 시작할 수 없거나 실행 중 두 번 사망하면 타 모델 대체 없이 기존
  `CODEX-UNAVAILABLE` 결과로 4.4에 진행할 수 있다. 시작 불가는 `model_unavailable(...)`, 실행 중
  사망은 `agent_died(...)`와 필요한 `agent_retry(...)`를 진단에 남긴다.
- Readonly 작업이 실행 중 두 번 실패하면, Phase 8.8은 `SKIPPED:AGENT_DIED`로 하고 Orchestrator가
  대체하지 않는다. 그 밖의 읽기 전용 작업은 Orchestrator의 축소 읽기 검토로 `DONE`과
  `degraded_fallback(...)`을 함께 기록할 수 있다.
- Worker writer/external-effect 작업이 실행 중 두 번 실패하면 `BLOCKED:AGENT_DIED`다. Orchestrator는
  source/test/API 문서 편집이나 push/PR을 대신 수행하지 않는다.
- 실행 불가인 다른 Phase는 그 Phase의 기존 `CODEX-UNAVAILABLE`/`SKIPPED:*`/`BLOCKED:*` 계약을
  적용한다. `model_unavailable(...)`를 Phase 상태로 쓰지 않는다.
- 설정된 슬롯의 model/effort가 거부되면(실증 형태: 에이전트 턴 실패 `400 invalid_request_error` — 지원되지 않는 모델) 진단에 `model_unavailable({슬롯}:{사유})`를 남기고 위 Phase별 계약을 그대로 적용한다. 기본값으로 되돌리거나 다른 model/effort로 재시도하지 않는다.

기존 예산 보존 규칙(`SKIPPED:BUDGET_PRESERVED`)과 재시도 진단(`agent_retry(...)`)은 유지한다.

## 실행 소유권과 결과 배리어

모든 writer dispatch/재시도 전에 [writer-safety.md](writer-safety.md)를 적용한다. timeout·오류·interrupt 접수는 종료가 아니다. 실제 종료 증거 없는 재시도는 `BLOCKED:WRITER_UNKNOWN`이다.
Orchestrator만 RUN 경로·OWNED_FILES·RESULTS_FILE·receipt·상태/노트를 갱신한다. Worker/Readonly/Advisor는 자기 결과 객체를 반환한다. nested spawn/직접 commit 제한은 유지한다.
범위는 [scope-contract.md](scope-contract.md)의 START_SHA~작업 트리 JSON에서 수집하며 envelope에 실제 명시 파일 목록을 넣는다. Read-back에는 Spec/Plan/상태 경로 없이 소스 목록만 보낸다.
writer 종료 후 실제 scope와 결과를 확인하고 다음 Phase를 진행한다. 호스트에서 checkout별 실제 cwd를 강제하지 못하면 parallel-slices도 순차 writer로 실행한다.
