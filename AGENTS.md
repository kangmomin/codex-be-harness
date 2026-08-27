# Codex BE Harness Repository Instructions

이 저장소는 `harness-plugins/be-harness`의 Codex-native 포트다.

## 작업 원칙

- 사용자와의 대화 및 보고는 한국어로 작성한다.
- BE workflow의 Phase 순서, 상태 코드, 루프 상한, 출력 머리글을 호환성 계약으로 취급한다.
- 원본과 달라지는 동작은 숨기지 말고 `COMPATIBILITY.md`에 근거와 함께 기록한다.
- Claude 전용 도구명, 경로, 모델명, slash command를 runtime 파일에 추가하지 않는다.
- 모델명은 고정하지 않고 parent 모델과 reasoning effort를 기본 상속한다. 단, 사용자 승인된
  `start-workflow` topology는 `skills/start-workflow/references/agent-topology.md`의 기본값 표(Sol High /
  Terra High·Max / Luna xHigh / Sol Max)를 기본으로 하고 profile `topologyModels` 슬롯 설정(또는 `--topology-models`)으로만 교체한다.
- 프로젝트별 값은 `.codex/be-harness.local.md`, 동작 override는 `.codex/be-harness/**`에서 읽는다.
- push, PR, 원격 피드백 제출은 해당 작업에 대한 사용자 승인이 있을 때만 수행한다.
- 관련 없는 리팩터링이나 포맷 변경을 섞지 않는다.

## 검증

변경 후 다음을 실행한다.

```bash
python3 tests/validate_port.py
python3 /home/dev/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
for skill in skills/*; do
  python3 /home/dev/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill"
done
```

`shellcheck`가 설치되어 있으면 `skills/e2e-test/assets/e2e-lock.sh`도 검사한다.

`tests/validate_port.py`는 `skills/*/assets/*.py` 문법 검사(내장 `compile()` — 바이트코드 파일 없음)와 upstream `2d7a01c` 기준 SHA-256 고정 검사를 포함한다(별도 `py_compile` 명령은 없다).
