# Codex BE Harness Repository Instructions

이 저장소는 `harness-plugins/be-harness`의 Codex-native 포트다.

## 작업 원칙

- 사용자와의 대화 및 보고는 한국어로 작성한다.
- BE workflow의 Phase 순서, 상태 코드, 루프 상한, 출력 머리글을 호환성 계약으로 취급한다.
- 원본과 달라지는 동작은 숨기지 말고 `COMPATIBILITY.md`에 근거와 함께 기록한다.
- Claude 전용 도구명, 경로, 모델명, slash command를 runtime 파일에 추가하지 않는다.
- 일반 위임은 parent 모델과 reasoning effort를 기본 상속한다. `start-workflow`의 orchestrator는
  현재 사용자 세션을 유지한다. 하위 역할은 `skills/start-workflow/references/agent-topology.md`의
  저장 배정과 profile `topologyModels`/`--topology-models`를 따른다. 최신 모델 조사는 사용자가
  `refresh-models`를 요청할 때만 수행하며 일반 workflow에서는 실행하지 않는다.
- 프로젝트별 값은 `.codex/be-harness.local.md`, 동작 override는 `.codex/be-harness/**`에서 읽는다.
- push, PR, 원격 피드백 제출은 해당 작업에 대한 사용자 승인이 있을 때만 수행한다.
- 관련 없는 리팩터링이나 포맷 변경을 섞지 않는다.

## 자율 실행과 동기화

- 사용자 지시와 이전 대화에서 의도·범위를 파악하고, 실행 요청은 필요한 작업과 검증을 끝까지 수행한다. 이미 승인된 범위의 가역적 작업은 재확인 없이 진행한다.
- 공통 행동 기준은 [공통 실행 원칙](skills/start-workflow/references/execution-policy.md)을 따른다. 지침에 따른 중단은 실제 근거를 밝히고, 구체적으로 승인되지 않은 파괴적·원격 효과는 기존 승인 범위를 확인한다.
- upstream 동기화 전 [선택적 동기화 기준](COMPATIBILITY.md#선택적-동기화-기준)을 읽고 공식 모델 가이드를 다시 확인한다. 기능 계약과 필요한 수정만 채택하고, 호스트 전용 실행 방법은 Codex에 맞게 변환한다.

## 검증

변경 후 다음을 실행한다.

```bash
bash scripts/verify.sh
python3 /home/dev/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
for skill in skills/*; do
  python3 /home/dev/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done
```

`shellcheck`가 설치되어 있으면 `skills/e2e-test/assets/e2e-lock.sh`도 검사한다.

`scripts/verify.sh`는 구조 검사(`tests/validate_port.py`), Python unittest, Node doc-gen 테스트를 순서대로 실행하며 하나라도 실패하면 실패한다. 구조 검사는 Python 자산 문법(compile, 바이트코드 없음)과 UPSTREAM-SYNC.json의 현재 자산 SHA-256도 확인한다. 테스트 의존성은 `.github/workflows/verify.yml`의 설치 단계를 따른다. Chromium sandbox 미지원 격리 컨테이너의 renderer 테스트에서만 HARNESS_DOCGEN_NO_SANDBOX=1을 명시할 수 있다.
