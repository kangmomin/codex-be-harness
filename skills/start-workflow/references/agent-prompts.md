> Phase 4.2~11의 위임 공통 계약이다. 단독 실행하지 않는다.
> `{CWD}`, `{RUN_DIR}`, `{STATE_FILE}`, `{IMPL_NOTES}`는 상위 스킬이 해결한 절대 경로다.

# Subagent prompts and recovery

## 공통 envelope

모든 서브에이전트 프롬프트에 아래 정보를 넣는다.

```text
프로젝트 루트: {CWD}
실행 디렉터리: {RUN_DIR}
상태 파일: {STATE_FILE} (Phase 8.8에는 전달 금지, 읽기 전용)
구현 노트: {IMPL_NOTES} (모든 역할 읽기 전용)
profile: {PROFILE_PATH} (식별·보고용 — 값은 아래 스냅샷만 쓰고 파일을 다시 읽지 않는다)
profile 스냅샷: {Pre-flight 확정값 — Phase 5부터는 {STATE_FILE}의 ## Profile Snapshot 전문과 동일, resolved_report_dir·resolved_e2e_lock_dir 포함}
현재 Phase: {PHASE}
남은 Phase: {REMAINING}
배정 model/effort: {TOPOLOGY_MODELS}의 해당 슬롯 확정값 (orchestrator / executor / readonly / advisor)
파일 소유권: {읽기 범위 / 수정 허용 범위}
반환 계약: {해당 Phase 출력 형식}
```

`{STATE_FILE}`과 `{IMPL_NOTES}`는 고정 경로로 추측하지 말고 받은 절대 경로만 사용한다. Sol High만
상태와 Phase Results를 작성하며 Executor/Luna/Advisor는 `{STATE_FILE}`과 `{IMPL_NOTES}`를 직접 쓰지 않고
구조화 결과만 반환한다. Terra executor의 작업 트리 편집 권한은 전달된 파일 소유권 범위에서 유지한다.
읽기 전용 역할이 파일을 수정했다면 그 변경은 결과로 채택하지 않고, 이슈 목록만 사용한다. 모든 고정 spawn은
`fork_turns:none`이며 역할/effort는 [agent-topology.md](agent-topology.md)의 슬롯 설정 규칙과 `{TOPOLOGY_MODELS}`를 따른다.

탐색·수집 질문이 3개 이상이면 3~10개를 한 Luna xHigh 읽기 전용 역할에 묶는다. 한 질문마다 새 역할을 만들지
않는다. 반환은 질문별 `file:line`, 핵심 snippet 최대 5줄, 한 줄 결론으로 제한한다. `없음` 결론에는
검색한 pattern과 경로를 반드시 붙인다. 부재가 Plan을 바꾸는 결정적 근거라면 오케스트레이터가 직접
재확인하거나 해당 Phase의 고정 역할로 독립 재검증한다.

### Implementation Notes 블록

Sol High가 Executor의 구조화 결과를 받은 뒤 기록할 때만 사용한다.

```text
설계 결정·편차·트레이드오프·미결 질문을 반환 결과에 명시한다. Sol High가 필요 시 {IMPL_NOTES}의
해당 섹션에 append한다. 은 반드시 ## 편차에도 같은 항목으로 기록한다.
```

## 대기 규약

서브에이전트 결과는 단일 `wait_agent`로 기다린다. 역할별 1회 타임아웃은 Luna 리뷰/스캔 10분, Terra Red 10분,
Terra Green·8.5 수정·E2E 30분, Sol Max advisor 15분, Terra 문서/PR 10분이다.

- 타임아웃 1회 → 같은 길이로 1회 재대기한다. 2회째 타임아웃은 실행 중 사망으로 간주하고 아래 재시도 예산(최대 2회)에
  편입한다.
- 재대기 전에 `send_message`로 재촉하지 않는다. 대기 중 `git status`·작업 트리 파일을 폴링해 진행 여부를 추측하지
  않는다 — 결과는 반환 계약으로만 판정한다.
- 반환 형식에 필수 섹션이 빠졌으면 `followup_task` 1회로 누락 섹션만 요청한다(재시도로 세지 않는다). 그래도 누락이면
  사망으로 처리한다.

## 사망/불완전 결과 처리

오류, 응답 없음, 필수 반환 형식 누락을 실패로 감지한다. Phase마다 최대 두 번 재시도한다. 두 번 모두
동일 역할·동일 모델·동일 effort·`fork_turns:none`로 하고 두 번째에는 `간결 모드: 산출물 계약은 유지하고 핵심만 수행`을 추가한다.
model capability 미가용은 실행 중 사망이 아니며 `model_unavailable(...)`을 진단 열에만 기록한다.
Sol Max Phase 4.3이 실행 중 두 번 사망하면 타 모델 대체 없이 `agent_died(...)`와 필요한
`agent_retry(...)`를 진단에 남기고 기존 `CODEX-UNAVAILABLE` 결과로 Phase 4.4에 진행한다.

| 두 번 실패한 역할 | 처리 |
|-------------------|------|
| Phase 8.8 격리 Read-back | `SKIPPED:AGENT_DIED`; 오케스트레이터 대체 금지 |
| Luna 읽기 전용 스캔·리뷰·성찰 | Sol High 축소 읽기 검토; `DONE` + `degraded_fallback(...)` |
| Terra 구현·수정·문서·E2E·승인된 push/PR | `BLOCKED:AGENT_DIED`; Sol High가 작업 트리/원격 효과를 대체하지 않음 |

재시도 성공은 `agent_retry({원인})`를 진단 셀에 기록한다. 한 실행에서 세션/예산 한계 사망이 2회
누적되면 Phase 8.4와 8.8 검증 독립성을 우선 보존하고 비검증 위임은
`SKIPPED:BUDGET_PRESERVED`할 수 있다. 모든 축소/재시도는 최종 보고의 `축소 실행 내역`에 남긴다.

## Phase 4 review prompts

Phase 4.2 Plan 리뷰어는 Luna xHigh이고 Spec과 Plan을 읽기만 한다. 각 관점마다 다음 형식으로 반환한다.

```text
Verdict: APPROVE | CONCERN | REJECT
Issues:
- {Spec ID 또는 Plan 항목} — {문제와 근거 file:line}
Suggestions:
- {최소 수정 제안}
```

Phase 4.3 fresh-context architect는 Sol Max이며 iteration마다 새 `fork_turns:none` context로 만든다.
이전 결론을 답으로 주입하지 않는다. Spec-Plan 추적성, 레이어 책임, 파일 소유권, 검증 누락, 단순화 여지를 독립적으로 평가하도록 한다.

## Phase 6.2 Green

역할 계약은 Terra High/Max [agents/workflow-implementer.md](agents/workflow-implementer.md)를 함께 전달한다.

```text
{STATE_FILE}의 확정 Spec과 Plan 순서대로 구현한다. 기존 프로젝트 스타일을 따르고 Spec 밖 동작은
변경하지 않는다. 변경 파일, 커밋 수, Plan diff, [Assumption], [TestConflict]를 반환한다.
```

TDD 활성 시 추가한다.

```text
테스트 파일을 수정하지 않는다. 테스트가 Spec과 충돌한다고 판단하면 코드와 테스트 모두 유지하고
[TestConflict]만 보고한다. Test Map의 모든 Green과 baseline 대비 신규 실패 0건이 통과 조건이다.
```

Executor는 커밋·상태 기록을 하지 않는다. `parallel-slices`에서는 각 역할에 정확한 파일 범위를
전달하고 커밋·빌드를 금지한다. Sol High가 모든 범위 밖 변경 여부를 검사한 뒤 단일 커밋을 조정한다.

## Phase 7 build-fix

```text
{buildCommand}의 아래 오류를 원인 범위 안에서만 수정한다.
오류: {BUILD_OUTPUT}
수정 후 같은 명령으로 확인하고 수정 파일과 원인을 반환한다. 무관한 정리는 하지 않는다.
```

Executor는 구조화 결과를 반환하고 Sol High가 성공한 수정만 `Fix: 빌드 에러 수정 (Phase 7)`로 커밋을 조정한다.

## Phase 9 API docs

```text
Terra executor가 {apiDocsPath}의 포맷을 내용으로 판정한다. 이번 Spec에서 추가·변경된 endpoint와 field만 파일에
반영한다. 외부 서비스에는 전송하지 않는다. 문서 diff와 반영 목록을 반환한다.
```

## Phase 8.6 E2E

Sol High가 `../../e2e-test-loop/SKILL.md`의 계약과 절대 asset 경로, `{PROFILE_PATH}`(식별용)와 `## Profile Snapshot` 전문(resolved 경로 포함)을 같은 Terra executor에 전달한다. Terra는 e2e-test-loop 호출에 그 스냅샷을 `mode: workflow` 입력으로 그대로 넘기고, 어느 단계에서도 profile 파일을 다시 읽지 않는다.
호출에는 `mode: workflow`를 명시해 인증 토큰 확보 실패가 사용자 질문 대신 `SKIPPED:NO_AUTH`로 끝나게 한다.
Terra는 중첩 agent spawn이나 직접 commit 없이 E2E와 실패 수정을 수행하고, PID/세션 핸들·정리 결과·
수정 파일·검증 결과를 구조화해 반환한다. Sol High만 `{STATE_FILE}` 기록과 commit 조정을 한다.

## Phase 10 PR

Sol High가 먼저 Assumption Gate를 통과시킨다. Terra executor가 일반 모드는 `../../commit-pr/SKILL.md`, hard
모드는 `../../commit-hard-push/SKILL.md`를 읽고 승인된 해당 절차를 수행한다. Phase 4.4에 고지한 원격 효과만
허용한다. 일반 모드 반환에는 브랜치, base, PR URL, draft/ready 상태가 있어야 한다.

## Phase 11 reflection

Luna xHigh 역할에 [agents/workflow-reflection.md](agents/workflow-reflection.md)를 전달한다. 상태 파일과 base
대비 커밋/diff를 읽어 계획 정확도, 품질 루프 효과, 난이도 정합성, 누락, 비용 집중 Phase를 분석한다.
개선안은 `.codex/be-harness/**` 로컬 오버라이드 후보로만 반환하고 직접 쓰지 않는다.

## 역할 문서

- Analyze: [agents/code-analyzer.md](agents/code-analyzer.md)
- Verify: [agents/code-verifier.md](agents/code-verifier.md)
- 요청 보강: [agents/edge-case-analyzer.md](agents/edge-case-analyzer.md)
- Scope 검증: [agents/scope-reviewer.md](agents/scope-reviewer.md)
- 구현: [agents/workflow-implementer.md](agents/workflow-implementer.md)
- PR: [agents/workflow-pr.md](agents/workflow-pr.md)
- 성찰: [agents/workflow-reflection.md](agents/workflow-reflection.md)
