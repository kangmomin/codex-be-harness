> Build 모드의 Phase 1~12 순서, 게이트, 상한을 정의한다. 단독 실행하지 않는다.
> 플레이스홀더와 상태 어휘는 상위 `SKILL.md`가 canonical이다.

# Build Mode — Phase 1~12

## Planning-only boundary

Phase 1~4.4 동안 허용되는 것은 읽기 전용 탐색, 사용자 질문, Technical Spec과 Plan 작성뿐이다.
프로젝트 파일·git refs·원격 상태를 변경하지 않는다. Spec/Plan 초안은 대화에 유지하고, 실행별 상태
파일은 승인 후 Phase 5에서 만든다. 승인 전 임시 디렉터리를 만든 경우에도 코드나 git은 변경하지 않는다.

## Phase 1: 작업 범위와 Technical Spec

상세 Spec이 이미 제공되어 작업 유형, 대상 API/기능, 핵심 요구사항이 모두 명확하면 그것을 Technical
Spec으로 정리한다. 아니면 형제 `../../request/SKILL.md`를 읽고 **spec-only** 절차로 질문한다. standalone
request의 즉시 실행 규칙은 사용하지 않는다.

어느 경로든 기존 코드를 읽어 참조 구현을 찾고 다음을 포함한다.

- 작업 유형: 생성/수정/검토/디버깅
- 정상 흐름 `AC-nn`, 엣지 케이스 `EC-nn`, 디버깅 재현 `RC-nn`
- Request/Response, 비즈니스 규칙, DB/외부 의존, 호환성
- 각 엣지 케이스의 참조 구현 `file:line` 또는 `-`

엣지 케이스 보강이 필요하면 [agents/edge-case-analyzer.md](agents/edge-case-analyzer.md)를 읽고 API당 한
읽기 전용 역할에 `incremental` 모드로 전달한다. 질문은 역할이 사용자에게 직접 보내지 않고
오케스트레이터에게 반환한다.

Spec 전문을 사용자에게 보여주고 확인받는다. 불명확한 요구는 대안을 제시하고 결정받으며 임의로
확정하지 않는다.

## Phase 2: 난이도

코드 복잡도 A와 영향 범위 리스크 B를 각각 1~10으로 산정하고 `max(A,B)`를 종합 난이도로 사용한다.

| 요소 | 1~3 | 4~6 | 7~10 |
|------|-----|-----|------|
| 파일/레이어 | 1~3개·단일 | 4~7개·2개 레이어 | 8개+·전 레이어 |
| DB | 없음 | 컬럼 추가 | 신규 테이블/데이터 이관 |
| 연동/로직 | 단순 CRUD | 기존 연동·분기 3개 이하 | 신규 연동·상태 머신 |
| 호환성 | breaking 없음 | 선택 필드 | 필수 필드/응답 구조 변경 |
| 공유 영향 | 없음 | 유틸·공통 함수 | 미들웨어·DI·외부 서비스 |
| 롤백 | 즉시 | migration rollback | 데이터 복구 필요 |

출력: `난이도: 코드 [A]/10 + 리스크 [B]/10 — [근거]`

## Phase 3: 실행 전략

기본은 `sequential`이다. 다음 5개를 모두 충족할 때만 2~3개 `parallel-slices`를 허용한다.

1. 각 슬라이스가 독립 endpoint/feature의 수직 슬라이스다.
2. 파일 소유권이 겹치지 않고 공유 DTO, middleware, DI wiring 변경이 없다.
3. 기존 테이블 변경이나 공통 계약 변경이 없다.
4. 슬라이스별로 빌드와 테스트가 가능하다.
5. 순서 의존이 없다.

FE와 BE 변경이 모두 필요하면 더 진행하지 않는다. 상태/보고에 다음을 포함하고 종료한다.

```text
상태: BLOCKED:FULLSTACK_HANDOFF_REQUIRED
FE 근거: 요청 조항, 후보 파일, 필요한 변경
BE 근거: 요청 조항, 후보 파일, 필요한 변경
영향 파일: 발견한 경로 목록
후속: fullstack 오케스트레이터로 handoff / BE-only로 범위 축소 / 종료
```

BE-only를 사용자가 선택하면 FE 조항과 파일을 Spec에서 제거하고 Phase 2부터 다시 산정한다. 이 첫
릴리스는 fullstack 실행을 자체 수행하지 않는다.

출력: `실행 전략: [sequential/parallel-slices] — [근거]`

## Phase 4: Plan과 리뷰

### Phase 4.1: Plan 작성

Spec 아래에 파일 단위 구현 순서, 각 변경, 최종 구조, 의존 관계, 위험, 테스트/검증을 추가해 하나의
Spec+Plan 산출물로 만든다. 중복 로직이 예상되면 최종 단순 구조를 여기서 확정한다.

`parallel-slices`면 `## Slices`에 제목·파일 범위·설명을 최대 3개로 적는다. 파일 범위가 겹치면
`sequential`로 되돌린다.

### Phase 4.2: 다관점 보강 1회

최대 3개 독립 리뷰어를 두 배치로 실행한다. 모두 읽기 전용이고 Spec+Plan 전문을 받는다.

- Batch 1: 유지보수성, 성능, 엣지 케이스
- Batch 2: 데이터 정합성, 보안, 기존 코드 영향

반환 형식은 `Verdict: APPROVE|CONCERN|REJECT`, `Issues`, `Suggestions`다. REJECT는 Plan에 반영하고,
CONCERN은 근거가 타당한 항목만 반영한다. 결과를 Plan v1으로 고정한다.

### Phase 4.3: 독립 Plan 검증 루프

fresh-context architect 리뷰어로 최대 5회 검증한다. 매회 Spec, Plan vN, 전략, 난이도 근거를 전달하고,
2회차부터 이전 diff와 기각 피드백/사유도 전달한다. 검토 관점은 Spec 추적성, 레이어 책임, 파일 소유권,
테스트 누락, 더 단순한 경로다.

매회 verdict, 반영, 기각 사유, Plan 변경 요약을 `Plan Verification Log` 초안에 누적한다.

| 조건 | 결과 |
|------|------|
| `APPROVE` | `PROCEED` 후 4.4 |
| 사용자 명시 중단 | `USER-INTERRUPTED`; 잔존 이슈 기록 후 4.4 가능 |
| 독립 리뷰 실행 불가 | `CODEX-UNAVAILABLE`; 사유 기록 후 4.4 가능 |
| 5회 미승인 | `BLOCKED:MAX_ITERATIONS`; 현재 Plan 진행/5회 추가/종료 결정 |

동일 이슈가 3회 반복되면 사용자 판단을 받는다. 반영·기각·변경이 모두 0건인 iteration은 즉시
중단해 무한 반복을 막는다.

### Phase 4.4: 명시적 실행 승인

Plan 모드 전환 명령에 의존하지 않는다. 아래 승인 블록을 사용자에게 보여주고 명시적 승인을 받는다.

```markdown
## 실행 승인 요청
- 확정 Spec/Plan: [요약과 잔존 이슈]
- 예상 변경 파일: [목록]
- 브랜치: [생성할 이름 / --hard로 현재 브랜치 유지]
- 로컬 변경: 코드·테스트·문서 편집, 논리 단위 커밋
- 외부 변경: [일반 모드] push + draft PR / [--hard] 현재 브랜치 push, PR 없음
- 자동 구간: Phase 6~11; Assumption Gate에 걸리면 push/PR 보류

이 Plan과 부작용으로 실행을 시작해도 될까요?
```

승인 거부/수정 요청은 Phase 1~4 안에서 처리한다. **승인 전에는 Phase 5의 브랜치·파일·커밋 동작을
하나도 수행하지 않는다.** 승인 후 `Plan Verification Summary`(iterations, convergence, 잔존 이슈)를
확정한다.

## Phase 5: 브랜치, 상태, baseline

승인 직후 시작한다.

- 일반 모드: 현재 브랜치가 `feat/**`/`hotfix/**`가 아니면 profile prefix로 feature 브랜치를 만든다.
  보호 브랜치에 직접 커밋하지 않는다.
- `--hard`: 브랜치를 만들지 않고 현재 브랜치를 사용한다.
- [templates.md](templates.md)의 상태/Implementation Notes 템플릿을 `{RUN_DIR}`에 생성한다.
- [tdd.md](tdd.md)의 적용 판정과 baseline 수집을 수행한다.

baseline 수집 실패는 자율 구간 전 마지막 결정 지점이다. 회귀 판정 저하를 감수하고 진행, 중단,
`--no-tdd` 전환 중 결정받는다.

## Phase 6: TDD 구현

[tdd.md](tdd.md)와 [agent-prompts.md](agent-prompts.md)를 읽는다.

### Phase 6.1: Red

TDD가 활성일 때만 `AC-nn`/`EC-nn`/`RC-nn` 근거의 실패 테스트와 최소 스텁을 작성한다. 형제
`../../unit-test/SKILL.md`의 Red 절차를 읽어 적용한다.

- sequential: 테스트 작성자 1명, 커밋은 오케스트레이터 소유
- parallel-slices: 각 작성자는 자기 테스트/스텁만 편집하고 실행·상태 기록·커밋하지 않는다.
  모두 끝난 뒤 오케스트레이터가 전역 Red 검증과 단일 커밋을 수행한다.

| 결과 | 상태/진행 |
|------|-----------|
| 모든 ID가 `red_assertion`/`already_satisfied`/`deferred_e2e` | `DONE` → 6.2 |
| 일부 `cannot_compile` | `DONE`; 해당 ID 제외 후 6.2 |
| 전체 `cannot_compile` | `BLOCKED:NO_VALID_RED`; TDD 생략 후 6.2 |
| baseline 밖 기존 테스트 실패 | `BLOCKED:REGRESSION_AT_RED`; 기록 후 6.2 |

Red 커밋은 `Test: {요약} — 실패 테스트 선작성 (Red)`다. pre-commit이 실패 테스트를 거부하면 Red
커밋을 생략하고 Green과 합친다.

### Phase 6.2: Green

- sequential: implementer 역할이 Plan 순서대로 구현하고 논리 단위로 커밋한다.
- parallel-slices: 파일 범위를 겹치지 않게 병렬 편집하고 각 작성자는 커밋·빌드를 하지 않는다.
  오케스트레이터가 결과를 대조한 뒤 한 번 커밋한다.

TDD 활성 시 테스트 파일 수정은 금지한다. 테스트가 잘못됐다고 판단하면 `[TestConflict]`만 보고하고
[tdd.md](tdd.md)의 오케스트레이터 판정을 따른다.

## Phase 7: 빌드 강제 검증

`buildCommand`가 없으면 `SKIPPED:PROFILE_EMPTY`다. 있으면 구현 직후 실행한다. 실패할 때마다
build-fix 역할이 원인 범위만 수정하고 커밋한 후 다시 실행한다. 총 3회 실패하면
`BLOCKED:BUILD_FAIL`로 중단하고 오류를 보고한다.

## Phase 8: 품질 루프

[quality-loop.md](quality-loop.md)가 canonical이다. 최대 3회 동안 읽기 전용 병렬 스캔 → 단일 작성자
통합 수정 → E2E/통합 테스트 순으로 수행한다. 종료 조건은 `modified == false`와 테스트 `PASS`다.
TDD가 생략됐으면 수정 0건만으로 종료할 수 있다. 3회 뒤에도 green이 아니면
`BLOCKED:TEST_NOT_GREEN`을 기록하되 Phase 8.8 이후를 계속한다.

루프 밖에서 격리된 Phase 8.8 Read-back을 정확히 한 번 실행한다. `FAIL`이어도 수정하지 않고 Phase
12 결정으로 이연한다.

## Phase 9: API 문서

작업 유형이 API 생성/수정/삭제이고 `apiDocsPath`가 실제 파일일 때만 문서 파일을 외과적으로
동기화한다. 외부 플랫폼으로 push하지 않는다. 아니면 구체적인 `SKIPPED:{사유}`를 기록한다.

## Phase 10: Assumption Gate와 PR/push

base diff의 추가 라인과 미push 커밋 본문에서 `[Assumption]`을 검색한다. 하나라도 있으면 push/PR을
금지하고 `BLOCKED:ASSUMPTION_UNRESOLVED`와 위치 목록을 기록한 뒤 Phase 11~12로 간다. 사용자가
결정하고 태그가 제거된 후 Phase 10만 재실행한다.

- 일반 모드: 형제 `../../commit-pr/SKILL.md`를 읽고 논리 커밋, base/branch 결정, VERSION patch bump,
  기존 PR 처리, 일반 push, draft PR을 수행한다. PR URL은 필수 결과다.
- `--hard`: 형제 `../../commit-hard-push/SKILL.md`의 Assumption Gate와 일반 push 절차를 읽고 현재
  브랜치에 push한다. PR은 만들지 않는다.

Phase 4.4에서 승인되지 않은 원격 효과가 새로 필요하면 여기서 멈춰 추가 승인을 받는다.

## Phase 11: 성찰

`--reflect`일 때만 [agents/workflow-reflection.md](agents/workflow-reflection.md) 역할로 커밋 로그와 Phase
결과를 분석한다. 아니면 `SKIPPED:REFLECT_NOT_REQUESTED`다. 보완점은 plugin 원본이 아니라
`.codex/be-harness/**` 후보로만 제안한다.

## Phase 12: 최종 보고

[templates.md](templates.md)의 순서를 바꾸지 않는다.

1. Implementation Notes HTML과 Workflow Report 생성
2. TDD 미해결 항목 결정
3. Read-back Diff 결정
4. Phase 11이 DONE이면 보완점의 로컬 저장 여부 결정
5. 상태 마감과 산출물 경로 보고

`feedbackUpstreamRepo`가 없으므로 첫 릴리스는 feedback PR을 만들지 않고
`SKIPPED:NO_FEEDBACK_UPSTREAM`을 기록한다. 값이 있더라도 Phase 4.4 승인 범위를 벗어난 외부 제출은
별도 승인을 받는다. 실행 중 띄운 서버가 남아 있지 않은지 확인하고 PID/세션 핸들을 정리한다.
