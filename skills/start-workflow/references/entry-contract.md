# Codex BE 진입 계약

모든 진입·재개에서 profile/init/Plan/RUN 생성·첫 dispatch보다 먼저 실행한다.
`{PLUGIN_ROOT}`는 실제 설치된 codex-be-harness 루트다. 실제 인자를 JSON 문자열 배열로 전달한다.

```bash
python3 -I -B "{PLUGIN_ROOT}/skills/start-workflow/assets/workflow_policy.py" route - <<'ROUTE_JSON'
{"entry":"be","arguments":["--verify"],"installed":{}}
ROUTE_JSON
```

- Build/Analyze/Verify를 지원한다. 동시 모드는 `BLOCKED:MODE_CONFLICT`; BE 외 도메인·overlay/외부 CLI 옵션은 `BLOCKED:UNSUPPORTED_ENTRY`다. 플래그를 버리고 Build로 진행하지 않는다.
- `--topology-models` 값은 토폴로지 문서대로 별도 검증한다. entry helper는 모델을 선택하거나 실행하지 않는다.
- exit 0 + READY일 때만 진행한다. 직접 native 호출은 dispatch=null이며 형제 플러그인을 찾거나 호출하지 않는다. exit 1/2는 차단이다.
- 기본 Build 정책은 pr, `--hard`는 push, Analyze/Verify는 none이다. 사용자가 로컬 실행으로 한정한 경우 `inherited_publish_policy:local`을 전달한다. READY의 hard/publish_policy/route_target을 보존한다.
- `--resume`은 명시된 상태의 MODE/HARD_MODE/PUBLISH_POLICY/ROUTE_TARGET을 `resume_mode`, boolean `resume_hard`, `resume_publish_policy`, `resume_route_target`으로 전달한다. 충돌하면 `BLOCKED:RUN_MISMATCH`이며 무시하지 않는다. READY 뒤에도 run-lifecycle의 절대 경로·저장소·미완료 검사를 통과해야 한다.
- `PUBLISH_POLICY:pr|push|local|none`과 `ROUTE_TARGET:be`를 상태에 기록한다. 재개·최종 수정의 정책 상한이며 저장된 local을 --hard 때문에 push로 확대하지 않는다. 이미 승인된 효과는 재승인을 요구하지 않는다.
- Phase 3에서 실제 FE+BE 범위를 발견하면 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 보고한다. 이 플러그인은 fullstack을 자체 실행하지 않는다.
