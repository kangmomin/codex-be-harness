---
name: refresh-models
description: "사용자가 요청할 때 최신 공식 모델 가이드와 현재 호스트의 지원 모델을 확인해 be-harness 역할별 추천 배정을 갱신한다. '모델 배정 최신화', '최신 모델 기준으로 갱신해줘' 요청에 사용한다. 일반 workflow 실행에서는 호출하지 않는다."
---

# be-harness Refresh Models

[공통 실행 원칙](../start-workflow/references/execution-policy.md)을 읽는다.
사용자의 모델 최신화 요청에만 실행한다. 날짜 경과·workflow 시작·모델 실행 실패는 자동 호출 조건이 아니다.
`{PLUGIN_ROOT}`는 실제 플러그인 루트, `{CWD}`는 대상 프로젝트다.
프로젝트의 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/refresh-models.md`가 있으면 읽는다.

## 범위와 선택 기준

[agent-topology.md](../start-workflow/references/agent-topology.md)의 슬롯·기본 표·effort 정책을 따른다.
Orchestrator는 현재 세션을 유지한다. 갱신 대상은 Worker(`executor`), 탐색·리뷰(`readonly`), Advisor(`advisor`)다.
Worker는 구현 품질과 실행 시간, Readonly는 범위가 정해진 탐색·리뷰의 정확성과 효율,
Advisor는 복잡한 설계·반례 검토 능력을 기준으로 선택한다. 새 출시만으로 모든 슬롯을 교체하지 않는다.
기본 갱신은 모델 배정을 재평가하고 기존 추천 effort 정책을 보존한다. effort까지 변경할 명확한 근거가 있으면
지원 범위와 변경 이유를 보고한다. 자동 advisor 호출 조건·Phase·루프·권한은 바꾸지 않는다.

추천표는 helper가 반환한 `models_path` 한 곳에 저장한다. profile을 상속하는 worktree에서는 추천표도 같은
위치를 공유하며 실제 경로와 상속 여부를 보고한다. 사용자 `topologyModels`, 실행 플래그, 세션/전역 설정,
플러그인 설치 캐시와 진행 중인 workflow의 snapshot은 수정하지 않는다.

## 최신 근거 확인

1. 아래 오프라인 resolve로 현재 추천과 사용자 override, 출처를 읽는다. profile이 없으면 `init`을 안내한다.
2. 공식 문서 검색·조회 도구가 있으면 우선 사용한다. 없으면 공식 도메인만 웹 검색하고 해당 본문을 연다.
   [최신 모델 가이드](https://developers.openai.com/api/docs/guides/latest-model)와
   [하위 에이전트 가이드](https://learn.chatgpt.com/docs/agent-configuration/subagents)를 기준으로 필요한 모델만 확인한다.
   출처는 `developers.openai.com`, `platform.openai.com`, `learn.chatgpt.com`의 HTTPS URL로 기록한다.
3. 현재 호스트의 모델 목록과 지원 effort(제공된 도구 스키마·모델 capability 정보)를 확인한다.
   문서에 등장한다는 이유로 실행 가능하다고 간주하지 않는다. `tiered`는 executor의 high/max,
   advisor의 xhigh/max 지원을 모두 확인한다. provider 전환·모델 탐색용 spawn·외부 CLI는 수행하지 않는다.
4. 모델별 지원 정보나 최신 공식 근거를 확보하지 못하면 부족한 근거와 기존 유지 사실을 보고한다.
   확인하지 못한 지원 목록을 추측해서 채우거나 기존 파일을 부분 갱신하지 않는다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/refresh-models/assets/models.py" resolve --cwd "{CWD}"
```

## 후보와 반영

실행 소유 임시 디렉토리에 UTF-8 후보 JSON을 쓴다. 스키마는 다음과 같다(실제 값으로 채운다).

```json
{
  "schema_version": 1,
  "checked_at": "YYYY-MM-DD",
  "sources": ["https://developers.openai.com/api/docs/guides/latest-model"],
  "models": {
    "executor": {"model": "WORKER_MODEL_ID", "effort": "high"},
    "readonly": {"model": "READONLY_MODEL_ID", "effort": "xhigh"},
    "advisor": {"model": "ADVISOR_MODEL_ID", "effort": "tiered"}
  },
  "rationale": {
    "executor": "출처에 근거한 선정 이유",
    "readonly": "출처에 근거한 선정 이유",
    "advisor": "출처에 근거한 선정 이유"
  },
  "host_models": {"실제 모델 ID": ["실제로 확인한 지원 effort"]}
}
```

`checked_at`는 실제 확인 날짜이며 `host_models`에는 세 슬롯에서 사용하는 모델과 실제 확인한 지원 effort를
담는다. 이는 호스트가 노출한 정보의 기록이며 실제 dispatch 성공이나 성능 평가를 수행한 증거는 아니다.
모델 ID를 문자열 조합으로 만들어내지 않는다. 명시 override가 있는 슬롯도 추천은 갱신할 수 있지만
실효 값은 override가 우선한다. 추천만 바뀌고 실제 배정은 유지되는 경우를 구별해 보고한다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/refresh-models/assets/models.py" edit --cwd "{CWD}" --candidate "{CANDIDATE_FILE}"
```

PREVIEW의 `before`, `after`, `preview`로 역할별 이전/추천/실효 값과 변경 근거를 검토한 뒤 같은 후보를 반영한다.
최신화 요청은 추천표 갱신을 포함하므로 preview 뒤 추가 승인을 요구하지 않는다. 사용자가 비교만 요청했으면
preview에서 끝낸다. 파일 생성·교체는 helper만 사용한다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/refresh-models/assets/models.py" edit --cwd "{CWD}" --candidate "{CANDIDATE_FILE}" --apply --expected-sha256 "{sha256_before}"
```

helper는 후보 스키마·근거 URL·지원 effort를 검증하고 원자적으로 생성/교체한다. 최초 생성의 expected hash는
`missing`이며, 동일 후보는 `changed:false`로 파일을 쓰지 않는다. `STALE_MODELS`면 현재 값을 다시 읽고
새 preview로 해결한다. 손상된 파일·비지원 스키마·symlink는 원본을 보존하고 원인을 보고한다.
적용 후 resolve로 출처·실효 값을 확인하고 실행 소유 임시 파일을 정리한다. 빌드·E2E·모델 벤치마크는 실행하지 않는다.

## 보고

`역할 | 이전 추천 | 새 추천 | 실효 배정 | 근거`와 실제 저장 경로·확인 날짜를 보고한다.
명시 override 보존 여부, 다음 신규 workflow부터 적용됨을 알린다. 추천은 공식 가이드와 호스트 정보에
근거한 판단이며 직접 성능 비교 결과로 표현하지 않는다. 실패 시 변경 여부와 부족한 근거를 명확히 쓴다.
