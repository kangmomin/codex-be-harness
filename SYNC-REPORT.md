## 📋 Task Report: Codex BE Harness 동기화

### 1. Pre-Review (Plan)

- **Orchestrator Feedback**: 현재 harness-plugins 작업 트리의 BE 및 기존 공통 의존 스킬을 Codex-native 저장소에 이식한다. 원본 저장소는 수정하지 않는다.
- **독립 리뷰어 Feedback**: 스킬 외 작업의 fresh-context 리뷰어 1명이 lifecycle/schema, JSON 소비자, writer 종료, profile 상속 경계를 검토했다. 외부 CLI 리뷰어는 호출하지 않았다.
- **Refinement**: schema 4·공통 Run 헤더, 구 실행 차단, 실패 보존, 실제 writer 종료 확인, commit 이후 검증 배리어를 반영했다. 설정 슬롯 초기화와 무효 슬롯 교체/삭제 오류도 회귀 테스트로 고쳤다.

### 2. Implementation Details

- **Assumptions**: “지금의 harness plugin”은 미커밋 변경을 포함한 현재 작업 트리이며, 대상은 기존 codex-be-harness의 BE·공통 6개 의존 스킬 범위로 해석했다.
- **Key Changes**: codex-be-harness 0.6.0. upstream be-harness 1.5.4/common 0.14.2의 실행 경로·명시적 재개·검증 JSON·변경 범위·writer·E2E v2·TDD·Git·doc-gen 변경을 동기화했다.
- **Preserved behavior**: .codex profile/override 경로, linked worktree 상속, topologyModels 모델/effort, 고정 역할, 단일 writer, 기존 원격 승인 범위.
- **Provenance**: source HEAD f9ce681427ccfbfd9194d3c3f204a445ae6f45dd와 미커밋 입력. UPSTREAM-SYNC.json에 76개 대응 파일의 source/target SHA-256을 기록했다. 그중 23개는 바이트 동일하며 실행 자산 18개를 구조 검사에서 고정 검증한다. 복사 시점과 마지막 원본 해시가 일치했다.
- **Compatibility**: 구 schema 2/3 및 run.json이 없는 실행은 새 실행으로 시작한다. E2E v1/v2 실행은 같은 자원에서 혼용하지 않는다. 세부 계약은 COMPATIBILITY.md에 있다.

### 3. Final Convention Review

- **Layer Analysis**: 애플리케이션 Presentation/Service/Repository 변경은 없다. 스킬 지침은 실행 흐름을, 자산은 경로·상태·파일·검증 처리를 담당하도록 연결했다. 공유 상태는 orchestrator, 업무 파일 수정은 executor 소유다.
- **Simplicity Check**: 기존 17개 스킬 범위를 유지했다. 순수 helper는 원본을 재사용하고 Codex host adapter에 필요한 차이만 적용했다. 기존 source 변경·설치 캐시·marketplace는 보존했다.

### 4. Status

- **Verification**: Python unittest 93개 PASS; 실제 Chromium 기반 doc-gen 5개 PASS(오프라인 SVG, 본문/twin 정합성, 잘못된 Mermaid, 충돌/부분 생성 정리). plugin validator PASS, 17개 skill validator PASS, validate_port PASS, shellcheck PASS, git diff --check PASS.
- **Test environment**: doc-gen 고정 의존성을 npm ci로 설치했다. 격리 컨테이너의 Chromium 테스트에서 HARNESS_DOCGEN_NO_SANDBOX=1을 명시했다. node_modules는 개발 의존성으로 유지하며 Git에서 제외한다.
- **Verification limits**: 실제 외부 모델로 전체 업무 workflow를 실행하거나 실제 서비스 API·push·PR를 수행하지 않았다.
- **Cleanup**: 테스트가 만든 Git/worktree/lease/브라우저 임시 자원은 종료·정리했다. 작업용 /tmp 스크립트·검토 파일·로그를 정리했다. 변경은 대상 저장소 main의 미커밋 상태이며 commit/push/재설치는 수행하지 않았다.

## 📋 Task Report: OpenAI 가이드 기반 실행 지침 보강

### 1. Pre-Review (Plan)

- **Orchestrator Feedback**: 앞서 요청한 자율 완료 원칙을 실행 스킬에 연결하고, 이후 upstream 동기화에서 핵심 계약만 채택하도록 기준을 정리한다.
- **독립 리뷰어 Feedback**: fresh-context 리뷰어 1명이 승인 재사용 범위, standalone 문구 충돌, bootstrap 지시 전달, Read-back 격리, 필수 검증 경계를 검토했다. 구현 후에도 이번 작업 시작 직전 사본과 비교했다.
- **Refinement**: 기존 승인은 같은 Spec·Plan·대상·효과에만 재사용한다. 새 upstream 입력의 source 해시 갱신과 로컬 지침 수정의 target 해시 갱신을 구분했다.

### 2. Implementation Details

- **Source**: [OpenAI 모델 가이드 — GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra), 2026-09-07 본문 확인. prompting 권고와 사용자의 자율 실행 요청을 적용했다.
- **Assumptions**: 이번 요청은 행동 지침과 선택적 동기화 기준의 개선으로 해석했다. 모델 슬롯 교체·API 호스트 기능 구현은 포함하지 않았다.
- **Key Changes**: [공통 실행 원칙](skills/start-workflow/references/execution-policy.md)을 16개 실행 스킬에서 읽는다. bootstrap·일반 envelope에 최신 지시·승인 근거·미결 결정을 전달한다. 필수 Gate, 모델·effort, 상태·루프·출력 형식을 유지한다.

| 판정 | 적용 내용·파일 | 근거 |
|---|---|---|
| 채택 | execution-policy, AGENTS: 의도 기반 완료·승인 재사용·중단 근거 설명·간결한 보고·비례적 검증 | 사용자 요청과 공식 prompting 권고 |
| 변환 | request/commit-push/resolve-assumption/doc-gen: 확정된 유형·브랜치·커밋·문서 인자 재확인 제거; OVERRIDES: 사용자 우선순위와 유지보수 범위 명시 | 이미 승인된 작업을 파일 지침 때문에 다시 중단하는 충돌 해소 |
| 변환 | agent-topology/agent-prompts: 최신 지시와 승인 전달, 지정 역할 내 완료; COMPATIBILITY/README: 선택적 동기화 기준 연결 | fresh-context 전달과 기존 writer·격리 계약에 맞춤 |
| 제외 | 가이드 원문 전체 복사, 무제한 위임·검증, 모델 일괄 교체, API async/configuration update 구현 | 필요한 행동 기준만 적용; 기존 제품·호스트·모델 역할 범위 유지 |

- **Provenance**: 이번 보강은 새 upstream 입력을 복사하지 않았다. 기존 76개 매핑의 source 정보는 보존하고 변경된 18개 매핑의 target SHA-256만 갱신했다. 로컬 전용 execution-policy와 topology에 upstream 출처를 추가하지 않았다.
- **Future sync**: [선택적 동기화 기준](COMPATIBILITY.md#선택적-동기화-기준)에 따라 공식 가이드를 다시 확인하고 변경별 채택·변환·제외·보류 근거를 기록한다.

### 3. Final Convention Review

- **Layer Analysis**: 애플리케이션 Presentation/Service/Repository와 실행 자산 변경 없음. 공통 정책·진입점·위임 입력·동기화 기록의 책임을 분리했다.
- **Simplicity Check**: 공통 지침은 한 파일, 각 스킬은 짧은 링크로 연결했다. 새 스킬·설정 키·상태 코드·자동 동기화 도구·문구를 복제하는 테스트를 추가하지 않았다.
- **독립 리뷰 결과**: 승인 범위 확대, Phase 4.4·Assumption Gate·Read-back 격리 회귀를 발견하지 못했다. 정책 읽기 명시와 향후 source 해시 갱신 설명을 보완했다.

### 4. Status

- **Verification**: validate_port PASS, plugin validator PASS, 17개 skill validator PASS, Python unittest 93개 PASS, 실제 Chromium doc-gen 5개 PASS, shellcheck PASS, git diff --check PASS. 16개 실행 스킬의 공통 정책 경로와 76개 target 해시를 확인했다.
- **Test environment**: 기존 설치된 doc-gen 의존성을 사용했다. 격리 컨테이너의 Chromium 테스트에만 HARNESS_DOCGEN_NO_SANDBOX=1을 지정했다.
- **Verification limits**: [행동 시나리오](tests/scenario-contracts.md#공통-실행-원칙-검토-시나리오)는 지침 대조용이다. 실제 모델로 전체 workflow를 실행하거나 원격 push·PR를 수행한 결과는 아니다.
- **Cleanup**: 검증 프로세스는 종료됐으며 임시 검토 자료를 정리했다. 작업 시작 전의 미커밋 변경을 보존했다. commit/push·원본 저장소·설치 캐시·marketplace 변경은 수행하지 않았다.
