> `start-workflow`의 고정 에이전트 토폴로지 단일 원천이다. Build, Analyze, Verify 모두 이 문서를
> 먼저 읽는다. Phase 순서·상태 코드·반복 상한·출력 머리글·승인 Gate는 다른 참조 문서의 계약을 따른다.

# Fixed agent topology

## 역할과 모델

| 역할 | 고정 모델 | effort | 권한 |
|------|-----------|--------|------|
| Orchestrator | `gpt-5.6-sol` | `high` | 사용자 승인 relay, Phase 상태·배리어·파일 소유권, 명령 실행·commit 조정, 최종 판정·보고 |
| Executor | `gpt-5.6-terra` | `high` 또는 `max` | 작업 트리 편집, 테스트/빌드 수정, API 문서, 승인된 push/PR, 승인된 Phase 12 remediation |
| Read-only subagent | `gpt-5.6-luna` | `xhigh` | 탐색, 엣지 케이스, 리뷰, 품질 스캔, scope/read-back, Analyze/Verify 읽기 전용 작업 |
| Plan advisor | `gpt-5.6-sol` | `max` | Phase 4.3 fresh-context Plan 검증 전용 |

모든 고정 spawn은 `fork_turns:none`을 사용한다. 고정 모델명을 다른 모델로 조용히 대체하지 않고,
모든 역할 프롬프트에는 이 문서의 배정 모델과 effort를 명시한다.

### Executor effort 선택

난이도 1~8은 Terra High, 9~10은 Terra Max다. 난이도 산정의 리스크에는 보안, 데이터 이관,
복잡한 API/계약 변경을 반영한다. 이 기준 외의 모호한 승격 규칙은 만들지 않는다.

## Bootstrap

entry agent는 workflow 요청을 한 번만 다음 Sol High orchestrator에 relay한다.

```text
spawn_agent(model="gpt-5.6-sol", reasoning_effort="high", fork_turns="none")
topology_bootstrapped=true
topology_hop_limit=1
payload={원본 사용자 요청, CWD, 프로젝트/스킬 지침, flags, resolved profile}
```

`topology_bootstrapped=true` marker를 받은 Sol High는 다시 orchestrator를 spawn하지 않는다. hop limit은
1을 넘기지 않는다. entry agent는 사용자 질문과 Phase 4.4 승인 요청/응답을 원문 그대로 relay한다.
advisor의 verdict나 다른 subagent 결과는 사용자 승인을 대체할 수 없다.

Sol High가 사용자 입력을 더 받아야 하면 `USER_INPUT_REQUIRED: {질문}` 구조로 entry agent에 반환한다.
entry agent는 질문을 사용자에게 원문 그대로 relay하고, 응답도 원문 그대로 **같은 orchestrator task**에
follow-up한다. 이 continuation은 새 bootstrap을 만들지 않으며, Phase 4.4 승인도 같은 계약을 따른다.

bootstrap이 Phase 5 전에 실패하면 상태 파일을 만들지 않는다. 사용자에게 실패 원인과 중단 사실을
보고하고, 코드·git·원격 효과 없이 종료한다.

## Writer와 상태 경계

Sol High만 `{STATE_FILE}`의 `Current Phase`, `Phase Assignments`, `Remaining Phases`, `Phase Results`를
작성한다. Executor, Luna, Advisor는 `{STATE_FILE}`과 Phase Results를 쓰지 않고 구조화된 결과만 반환한다. Executor가 E2E 서버를
시작하면 PID/세션 핸들과 정리 결과를 반환하고 Sol High가 상태에 기록한다.

Sol High는 `{RUN_DIR}`와 report 같은 운영 메타데이터를 쓸 수 있지만 source, test, API 문서 등 작업
트리 내용은 직접 편집하지 않는다. 작업 트리의 단일 writer는 해당 시점에 배정된 Terra executor다.
Phase 8.5의 단일 writer, Phase 6 barrier, Phase 8.8의 isolation은 이 경계보다 우선하는 예외가 아니다.

## Phase routing

| 범위 | 담당 | 실행 규칙 |
|------|------|-----------|
| Build 1~5, 6/8 barrier·commit, 7/8 명령·판정, 10 Assumption Gate, 12 상태·사용자 결정·보고 | Sol High | 승인과 상태를 소유하며 worktree를 직접 편집하지 않음 |
| 1 edge-case 보강, 4.2, 8.2, 8.3, 8.4, 8.8, 11 | Luna xHigh | 읽기 전용; 8.8에는 Spec/Plan/state/Test Map을 전달하지 않음 |
| 4.3 | Sol Max | 매 iteration 새 fresh context로 spawn, 최대 `{PLAN_MAX}`회(standard 5 / light 2) |
| 6.1 Red, 6.2 Green, 7 build-fix, 8.5, 8.6, 8.7, 9, 10 승인된 push/PR, 12 승인된 remediation | Terra High/Max | Sol이 명령/승인/상태를 조정하고 Executor가 수정 또는 외부 효과를 수행 |
| Analyze A1/A2/A4, Verify V1/V2/V5 | Sol High | 읽기/명령/보고 소유 |
| Analyze A3, Verify V3/V4 | Luna xHigh | 읽기 전용 구조화 결과 반환 |

Sol Max advisor의 결과를 Plan에 반영하거나 기각하는 판단은 Sol High만 한다. Phase 12에서 Terra remediation이
diff를 바꾸면 Sol High는 Phase 10 Assumption Gate와 Phase 4.4에서 승인된 외부 효과 범위를 다시 확인한 뒤에만
push/PR을 재개한다.

## Unavailable과 agent died

모델 capability 미가용(`model_unavailable(...)`)과 실행 중 사망을 구분한다. 진단에는
`model_unavailable(...)`만 기록하고, 타 모델로 대체하거나 모델/effort를 낮춰 재시도하지 않는다.

- Phase 4.3 advisor를 시작할 수 없거나 실행 중 두 번 사망하면 타 모델 대체 없이 기존
  `CODEX-UNAVAILABLE` 결과로 4.4에 진행할 수 있다. 시작 불가는 `model_unavailable(...)`, 실행 중
  사망은 `agent_died(...)`와 필요한 `agent_retry(...)`를 진단에 남긴다.
- Luna read-only 작업이 실행 중 두 번 실패하면, Phase 8.8은 `SKIPPED:AGENT_DIED`로 하고 Sol High가
  대체하지 않는다. 그 밖의 읽기 전용 작업은 Sol High의 축소 읽기 검토로 `DONE`과
  `degraded_fallback(...)`을 함께 기록할 수 있다.
- Terra writer/external-effect 작업이 실행 중 두 번 실패하면 `BLOCKED:AGENT_DIED`다. Sol High는
  source/test/API 문서 편집이나 push/PR을 대신 수행하지 않는다.
- 실행 불가인 다른 Phase는 그 Phase의 기존 `CODEX-UNAVAILABLE`/`SKIPPED:*`/`BLOCKED:*` 계약을
  적용한다. `model_unavailable(...)`를 Phase 상태로 쓰지 않는다.

기존 예산 보존 규칙(`SKIPPED:BUDGET_PRESERVED`)과 재시도 진단(`agent_retry(...)`)은 유지한다.
