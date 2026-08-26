# Compatibility Contract

## 기준

- upstream: `kangmomin/harness-plugins`
- commit: `e87949b127159759950a2247a5067d30e41292a1`
- source plugin: `be-harness@1.1.0`
- target plugin: `codex-be-harness@0.2.0`

호환성은 문장 일치가 아니라 관찰 가능한 workflow 동작을 기준으로 한다. Phase 순서, 승인·차단 게이트, 상태 코드, 루프 상한, 보고서 머리글을 invariant로 본다.

## Source inventory mapping

### Skills

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `be-harness/skills/start-workflow/**` | `skills/start-workflow/**` | Codex planning gate와 subagent prompt로 변환 | Build Phase 1~12, Analyze A1~A4, Verify V1~V5 유지 |
| `be-harness/skills/request/**` | `skills/request/**` | 구조화 입력 fallback, 내부 `spec-only` 경계 | Spec·엣지 케이스·추적 ID 형식 유지 |
| `be-harness/skills/unit-test/**` | `skills/unit-test/**` | Codex 파일/명령 실행 표현 | Red 분류와 테스트 상한 유지 |
| `be-harness/skills/simplify-loop/**` | `skills/simplify-loop/**` | Workflow JS를 prompt/state machine으로 교체 | 최대 10회, 네 관점, DA→arbiter→writer와 종료 코드 유지 |
| `be-harness/skills/convention-check/**` | `skills/convention-check/**` | AGENTS/profile 경로 변환 | 검사 관점과 PASS/WARN/FAIL 유지 |
| `be-harness/skills/default-conventions/**` | `skills/default-conventions/**` | provider-neutral 호출 | 레이어·에러·트랜잭션 기본 규칙 유지 |
| `be-harness/skills/e2e-test/**` | `skills/e2e-test/**` | skill-relative asset, PTY/PID 정리, bounded polling | lock·server·시나리오·판정 계약 유지 |
| `be-harness/skills/e2e-test-loop/**` | `skills/e2e-test-loop/**` | Codex subagent 수정 loop | 최대 5회와 no-progress 차단 유지 |
| `be-harness/skills/init/**` | `skills/init/**` | `.codex` profile/override 생성 | preset과 non-destructive update 유지 |
| `be-harness/skills/doctor/**` | `skills/doctor/**` | Codex 경로·tool 진단 | 필수/선택 진단 분류 유지 |

### Agents

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `be-harness/agents/code-analyzer.md` | `skills/start-workflow/references/agents/code-analyzer.md` | read-only subagent prompt | Analyze 관점과 보고 형식 유지 |
| `be-harness/agents/code-verifier.md` | `skills/start-workflow/references/agents/code-verifier.md` | read-only subagent prompt | Verify 기준과 판정 유지 |
| `be-harness/agents/edge-case-analyzer.md` | `skills/request/references/edge-case-analyzer.md` | request 내부 분석 prompt | 다관점 edge-case 질문/출력 유지 |
| `be-harness/agents/scope-reviewer.md` | `skills/start-workflow/references/agents/scope-reviewer.md` | read-only subagent prompt | Spec-only scope 검증 유지 |
| `be-harness/agents/workflow-implementer.md` | `skills/start-workflow/references/agents/workflow-implementer.md` | writer subagent prompt | Plan/TDD 제약과 결과 보고 유지 |
| `be-harness/agents/workflow-pr.md` | `skills/start-workflow/references/agents/workflow-pr.md` | commit/PR skill orchestration prompt | Assumption Gate와 PR 결과 유지 |
| `be-harness/agents/workflow-reflection.md` | `skills/start-workflow/references/agents/workflow-reflection.md` | read-only reflection prompt | 회고 항목과 override 제안 유지 |

### References and assets

| source | target | adaptation | invariant / gap |
|---|---|---|---|
| `start-workflow/references/agent-prompts.md` | same relative target | Codex spawn/death semantics | Phase assignment 유지 |
| `start-workflow/references/analyze-verify-modes.md` | same relative target | sibling procedures와 subagent prompt 사용 | A/V phase 유지 |
| `start-workflow/references/quality-loop.md` | same relative target | bounded Codex subagents | Phase 8.1~8.7 유지 |
| `start-workflow/references/tdd.md` | same relative target | unit-test 절차를 sibling에서 로드 | Red barrier/Test Map 유지 |
| `start-workflow/references/templates.md` | same relative target | `.codex`와 feedback gap 반영 | 상태·최종 보고 머리글 유지 |
| `simplify-loop/references/workflow-script.md` | same relative target | 실행 JS가 아닌 상태 머신 명세 | 기존 상태 필드와 종료 판정 유지 |
| `e2e-test/assets/e2e-lock.sh` | same relative target | work-log fallback 제거 | acquire/heartbeat/release/timeout 유지 |
| `e2e-test-loop/assets/api-test-cases-prompt.md` | same relative target | provider-neutral prompt | 테스트 케이스 생성 목적 유지 |

### Inlined common dependencies

| source | target | purpose |
|---|---|---|
| `common/skills/commit/**` | `skills/commit/**` | 논리 단위 커밋 canonical |
| `common/skills/commit-push/**` | `skills/commit-push/**` | 브랜치/base/Assumption/push canonical |
| `common/skills/commit-pr/**` | `skills/commit-pr/**` | VERSION과 PR canonical |
| `common/skills/commit-hard-push/**` | `skills/commit-hard-push/**` | `--hard` 경로 |
| `common/skills/resolve-assumption/**` | `skills/resolve-assumption/**` | 개발 중 Assumption 해소 |
| `common/skills/doc-gen/**` | `skills/doc-gen/**` | E2E·workflow 보고서 렌더링 |

## Runtime adaptations

- Phase 1~4는 planning-only다. Phase 4.4의 명시적 사용자 승인이 기존 Plan mode 종료의 의미적 대체다.
- workflow 상태는 run-scoped 임시 디렉토리에 저장하고 resolved path를 subagent에 전달한다.
- 일반 custom agent model은 고정하지 않고 parent 모델과 reasoning effort를 기본 상속한다. 다만
  `start-workflow`는 사용자 승인된 고정 topology(Sol High orchestrator, Terra High/Max executor,
  Luna xHigh read-only, Sol Max Phase 4.3 advisor)를 사용한다. 모든 고정 spawn은 `fork_turns:none`이며,
  모델 미가용/실행 중 사망은 구분해 기존 `CODEX-UNAVAILABLE`·`SKIPPED:AGENT_DIED`·
  `DONE + degraded_fallback`·`BLOCKED:AGENT_DIED` 계약을 적용하고 타 모델로 대체하지 않는다.
- project override agent 파일은 parent가 읽어 해당 subagent prompt에 추가한다.
- fullstack 판정은 Phase 3에서 `BLOCKED:FULLSTACK_HANDOFF_REQUIRED`로 종료한다. 자동 BE 축소를 금지한다.

## 0.2.0 deviations (observed-behavior changes vs upstream)

| 영역 | upstream 동작 | 0.2.0 동작 | 근거 |
|---|---|---|---|
| request 질문 | 한 턴에 질문 하나 | `spec-only`는 남은 질문 전부, `standalone`은 한 턴 최대 4개; 기본값 첨부, 무응답/`skip`은 기본값 + `[Assumption]` | 왕복 턴 수 절감 |
| profile 부재 | 즉시 종료 | 프로젝트 루트 → linked worktree의 메인 워크트리 상속 → 둘 다 없을 때만 종료 (`PROFILE.md` "profile 해석") | 워크트리 세션의 원격 DB 부팅·설정 재발명 차단 |
| Phase 1 | 없음 | 중복 작업 스캔, 강 신호는 `BLOCKED:DUPLICATE_IN_PROGRESS` | 동일 기능 병렬 착수 방지 |
| Phase 12 | HTML 노트 + 대화 보고 | 추가로 `*-workflow-report.md` 저장, remediation 후 재렌더링 | 보고서 유실 방지 |
| 서브에이전트 대기 | 명시 없음 | `agent-prompts.md` "대기 규약" (역할별 타임아웃, 재대기 1회, 폴링 금지) | 폴링·재촉 비용 제거 |
| e2e-test 호출 | standalone만 | `mode: workflow` 전달 시 인증 부재는 질문 없이 `SKIPPED:NO_AUTH` | 자율 구간 무질문 계약 |
| 기준 브랜치 | `main` 하드코딩 (e2e-test, simplify-loop) | profile `mainBranch` 우선 | `dev` 기반 레포의 과대 diff 방지 |
| Assumption Gate | diff·커밋 본문 | + `{IMPL_NOTES}` `## 편차` (Spec `[Assumption]` 이월분) | push 전 Spec 가정 해소 |

## Explicit gaps in 0.1.0

- Minmos overlay는 포함하지 않는다.
- fullstack workflow 자체는 포함하지 않는다.
- 원격 `submit-feedback`은 포함하지 않는다. 로컬 override를 저장하고 `SKIPPED:NO_FEEDBACK_UPSTREAM`을 반환한다.
- public ChatGPT 배포보다 로컬 Codex의 shell·Git workflow를 우선한다.
