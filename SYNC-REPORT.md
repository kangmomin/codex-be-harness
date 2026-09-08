## 📋 Task Report: 기본 high + 선택 advisor (0.6.3)

### 1. Pre-Review (Plan)

- **Orchestrator Feedback**: executor 기본 high와 난이도·위험 신호별 advisor 자동 결정을 기존 Phase 4.2→4.4 경로에 맞춘다.
- **독립 리뷰어 Feedback (4.2 Luna / 4.3 Sol Max)**: max 신호의 독립 OR, 4.4 재평가의 기존 iteration 상한, Analyze/Verify와 legacy resume의 unused advisor 처리를 확인했다.
- **Refinement**: fixed override 우선, concrete spawn, raw 결과와 Assignment status 분리로 확정했다.

### 2. Implementation Details

- **Assumptions**: 없음.
- **Key Changes**: executor default high, advisor auto `N/A|xhigh|max`, legacy executor tiered 호환, state/resume 계약과 parser·경계 검사를 반영했다.

### 3. Final Convention Review

- **Layer Analysis**: 앱 레이어 변경은 없고 topology·lifecycle·profile parser 책임을 분리했다.
- **Simplicity Check**: 기존 점수·루프·상태 구조를 재사용하고 새 classifier나 runtime을 추가하지 않았다.

### 4. Status

- **Verification**: `HARNESS_DOCGEN_NO_SANDBOX=1 bash scripts/verify.sh`가 validate_port, Python 109개, Node 5개를 통과했고 plugin validator, 17개 전체 skill validator, shellcheck도 PASS했다. 옵션 없는 첫 Chromium sandbox 실패는 격리 환경 문제였으며, isolated read-back WARN A=1/C=0/E=0은 동작 실패가 아닌 test-source 재구성 한계다.
- **Cleanup**: 개인 설정과 설치 cache는 변경하지 않았고 RUN 상태·로그는 저장소 밖에 남겼으며, 승인된 프로젝트 override README를 포함했다.

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

## 📋 Task Report: AI 활용성 리뷰의 Astra 튜닝 (2026-09-08)

### 1. Pre-Review (Plan)

- **근거**: `work-log:정리된 문서/AI 활용성/20260907-AI 활용성 리뷰.md` §6~7 및 2026-09-08 본문을 확인한 [공식 GPT-6 Astra 가이드](https://developers.openai.com/api/docs/guides/latest-model).
- **Orchestrator Feedback**: 완료·승인·현재 기준과 인계 경계를 기존 execution-policy 및 실제 소비 경로에 연결한다. 검증은 요구의 증거를 기준으로 하고 불필요한 추가 반복을 줄인다.
- **독립 리뷰어 Feedback**: fresh-context 리뷰어 1명이 같은 Plan/효과의 승인 재사용, 기존 Spec 보존, 직접 Spec·일반 위임 연결, Read-back 격리, 역할별 AC/EC, 해시 출처를 검토했다.
- **Refinement**: 기존 Phase·상한·상태·topology를 유지하고 정책·소비 경로의 충돌만 수정했다. 난이도는 매핑 낮음, 정책 수정 중간, Codex 변환·호환성 기록 높음, 검증 중간이다.

### 2. Implementation Details

- **Assumptions**: Astra 튜닝은 현재 하네스의 행동 기준 조정으로 해석했으며 기존 모델 슬롯은 유지했다.

| 판정 | 반영 대상 | 이유 |
|---|---|---|
| 채택 | 작업 계약의 대상·기준·범위·완료 증거·승인·미결, 요구 기반 테스트, 역할별 AC/EC, 로그 마스킹·가설 검증 | 사용성 리뷰의 관찰된 마찰을 실행 기준으로 연결 |
| 변환 | 기존 execution-policy, request, native build-phases의 직접 Spec 및 Phase 4.4 승인 재사용 | Astra의 자율 완료·지침 민감도·적정 검증 권고를 기존 승인 계약 안에서 적용 |
| 변환 | bootstrap·일반 envelope, templates/run-lifecycle/analyze-verify | 정확한 식별자·최신 기준·완료 증거를 기존 상태 경로로 인계; Read-back 소스 격리와 writer 역할 보존 |
| 변환 | quality-loop/finalization | 마지막 수정·커밋 후 stale 이벤트별 실제 재검증과 Read-back 예외 명시; 과거 PASS 해시 치환 금지 |
| 제외 | Claude 정책 파일·도구·경로·모델의 일괄 복사, 새 승인/위임 단계, 전체 스키마·검증 엔진 확장 | 필요한 결정 기준을 기존 Codex 정책에 합치고 기능·호스트 경계를 유지 |

- **Provenance**: 전체 동기화 기준 `f9ce681427ccfbfd9194d3c3f204a445ae6f45dd`는 보존한다. 선택 반영한 11개 매핑의 source HEAD는 `80366fe4e83210368a9f3015fed73d1fbdafb878`의 AI 활용성 개선 커밋이며 source/target SHA-256을 함께 갱신했다. 변경 이력은 UPSTREAM-SYNC.json의 `selective_updates`에 있다. source start-workflow 계약은 기존 native entrypoint가 읽는 build-phases에 변환했다. execution-policy·agent-topology·build-phases는 로컬 전용으로 유지하며 별도 upstream 파일 매핑을 만들지 않았다.

### 3. Final Convention Review

- **Layer Analysis**: Presentation/Service/Repository 애플리케이션 코드 변경 없음. 공통 정책은 판단 기준, 스킬은 실행 경로, 기존 helper는 상태·검증 계약을 담당한다.
- **Simplicity Check**: 새 스킬·프로필 키·상태 스키마·모델 슬롯·위임 단계 없음. 기존 16개 실행 스킬의 정책 읽기 경로를 활용했다.
- **독립 행동 검토**: 별도 fresh-context 리뷰어가 6개 입력을 두 호스트 규칙에 적용했다. 동일 승인, 관리자 토큰만 있는 smoke, 설계/테스트 충돌, timeout 가설, 파일명 정정·새 worktree, 최종 tree 변경을 확인했다. 이는 읽기 전용 행동 검토이며 실제 서비스 workflow 실행은 아니다.
- **반영한 발견**: check-current는 모든 최신 non-pr 이벤트의 tree 일치를 요구한다. 영향 범위 재검증과 Read-back 1회 규칙의 모호함을 finalization의 실제 stale 재검증·격리 예외로 해소하고 리뷰어 재확인을 받았다.

### 4. Status

- **Verification**: validate_port PASS, plugin validator PASS, 17개 skill validator PASS, Python 93개 PASS, 실제 Chromium 문서 렌더링 5개 PASS, shellcheck PASS, git diff --check PASS. 전체 76개 target 해시 일치와 선택 반영한 11개 source 해시를 검사했다.
- **Test environment**: 기존 doc-gen 의존성을 사용했다. Python 검증은 임시 venv, 격리 컨테이너의 renderer에는 HARNESS_DOCGEN_NO_SANDBOX=1을 사용했다.
- **한계**: 실제 업무의 전체 workflow·서비스 API·원격 작업을 실행하지 않았다. 현재 검증 엔진은 전체 tree에 근거를 묶으므로 최종 문서/commit 변경도 stale 검증의 재실행을 요구할 수 있다.
- **Cleanup**: 검증 프로세스와 fixture 자원은 종료했고 임시 검토 자료를 정리했다. 후속 커밋·푸시 요청에 따라 0.6.1로 게시하며 적용 범위와 기존 모델 슬롯 유지 결정을 재사용한다.

## 📋 Task Report: 검증 신뢰성과 재개 개선 (0.6.2, 2026-09-08)

### 1. Pre-Review (Plan)

- **Orchestrator Feedback**: 개선 분석 R1~R8에 대한 변경·계속 요청을 근거로 원본 BE/FE/common과 Codex 포트의 관련 구현을 수정했다.
- **독립 리뷰어 Feedback**: fresh-context 리뷰어가 지문 비교의 단일화·실제 파일 집합·통합 결과의 종료/아카이브 연결·원래 바이트 해시의 리터럴 예외·Verify helper의 재개 검증을 요구했다. 외부 CLI 리뷰어는 호출하지 않았다.
- **Refinement**: 기존 지문을 자동 변환하지 않고 기록된 HEAD 의존성을 보존한다. 후보 탐색은 커버리지 판단과 분리한다. 실패와 불완전한 저장 상태는 보존한다.
- **Guide**: [공식 모델 가이드](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)를 2026-09-08 다시 확인했다. 필요한 수정·검증·명확한 완료 근거에 관한 행동 기준을 유지하며 모델 슬롯은 변경하지 않았다.

### 2. Implementation Details

- **Assumptions**: 없음. 앞서 제시한 R1~R8과 사용자의 변경 승인을 적용했다.
- **Provenance**: source HEAD `ae6900e4504a594bd6b9124043a59b7350ee33e8`에 커밋된 R1~R8 파일이 이번 동기화의 정본이다. target 구현 기준은 `21b15a5e30e98c2ecd5856c565262c8f43adb22e`다. UPSTREAM-SYNC.json의 21개 선택 source 해시와 전체 78개 target 해시를 기록했다. 이전 전체 동기화와 선택 반영 이력은 보존했다.

| 판정 | 내용과 적용 |
|---|---|
| 채택 | R1/R5 실제 파일 지문 v2·내용 동일 커밋 재사용, R3 integration 결과와 합산·아카이브, R6 검토한 줄의 리터럴 예외, R7 패키지/testDirs 후보, R8 Verify 명령 저장·재개 검증. 관련 순수 helper와 새 회귀 테스트를 원본에서 재사용했다. |
| 변환 | BE Phase 8.7 baseline 비교·test-summary·필수 integration, commit 검증 배리어의 재사용, Verify Pre-flight/재개 명령 출처를 Codex profile·역할·경로 계약에 연결했다. |
| 로컬 구현 | R2 단일 verify runner와 CI, AGENTS/README, 충돌하던 시나리오 기대값을 정리했다. Python/Node 실패를 실제로 주입하는 runner 테스트를 추가했다. |
| 원본에서 적용 | R4 FE fixture lock 정상화와 Node/npm 고정은 FE fixture가 있는 원본 저장소에 적용했다. Codex에는 기존 doc-gen 의존성과 새 verify CI를 사용한다. |

호환성 세부 사항은 [COMPATIBILITY.md](COMPATIBILITY.md)의 0.6.2 개선 표와 [결과 계약](skills/start-workflow/references/result-contract.md), [실행 재개 계약](skills/start-workflow/references/run-lifecycle.md)에 있다. 새 integration reader/writer는 같이 갱신하며, 구 지문과 명령 스냅샷 없는 구 Verify 실행을 자동으로 새 근거로 바꾸지 않는다.

### 3. Final Convention Review

- **Layer Analysis**: 애플리케이션 DB 변경은 없다. 스킬이 실행 흐름을 설명하고 helper가 지문·결과·스냅샷을 검증한다. 단일 writer·승인 범위·Read-back 격리·실패 이력과 루프 상한은 유지했다.
- **Simplicity Check**: 기존 helper와 형식에 필요한 필드·명령만 추가했다. 리터럴 예외는 정확한 줄에만 적용하고, 테스트 후보를 자동 커버리지로 승격하지 않는다.
- **독립 행동 검증**: A — 내용 동일 commit의 기존 unit PASS 재사용과 최종 결과 검증 성공. B — unit 최신 PASS 뒤에도 integration FAIL·회귀 1건 유지. C-valid — profile 변경 후 저장된 `recorded-command` 실행, exit 0과 결과 JSON 검증 성공. 원본 C fixture의 필수 메타데이터 누락은 BLOCKED 증거로 별도 보존했다. 최종 대조에서 TDD 생략 시의 이전 요약 문장도 합산 규칙에 맞췄다.

### 4. Status

- **Verification**: `bash scripts/verify.sh` exit 0 — 구조 검사(17 skills, 26 resources), Python 109개, 실제 Chromium doc-gen 5개 통과. plugin validator, 17개 skill validator, shellcheck 통과. 전체 검사 뒤 추가한 디렉터리↔파일 전환 경계는 두 저장소의 지문 회귀 검사 7개로 재검증했다. 원본의 전체 runner도 Python 212개·work-log Python 10개/Node 31개·doc-gen 5개·FE Jest 6개/Vitest 11개·loopback gRPC를 통과했다.
- **한계**: 실제 로컬 helper·Git·브라우저와 지정된 독립 행동을 검증했다. 원격 CI, 실제 서비스의 전체 Build→PR, Verify V3~V5, 모델별 시간·비용은 이번에 실행하지 않았다. ignored 파일·저장소 밖 입력은 내용 지문의 범위 밖이며 HEAD 의존성이 불명확한 검증은 include-head로 보수적으로 기록한다.
- **Integrity**: 전체 target 해시 78개·선택 source 해시 21개와 공유 helper 사본이 일치한다. 최종 구조 검사와 git diff --check가 통과했고, 두 저장소 HEAD·index는 시작 시점 그대로다.
- **Cleanup**: 검증 로그·독립 행동 결과를 보존하고 소유 프로세스가 없음을 확인한 뒤 임시 venv·fixture·패키지 캐시를 삭제했다. Git에서 제외된 기존 개발 의존성은 유지했다. 후속 commit-hard-push 요청에 따라 0.6.2 게시 내용을 확정했다. 독립 게시 검토에서 커밋 분할·리터럴 분류·원본 출처를 확인했으며 설치 갱신은 이번 요청 범위에 포함하지 않는다.
