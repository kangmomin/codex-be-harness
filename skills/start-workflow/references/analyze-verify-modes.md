> `--analyze`와 `--verify`의 전용 절차다. Build Phase와 섞지 않는다.
> 상태 파일은 상위 스킬의 실행별 `{RUN_DIR}` 안에 생성한다.

# Analyze / Verify

두 모드 모두 profile과 프로젝트 오버라이드를 먼저 읽고, 지정된 범위를 검증된 `{CWD}` 기준으로
해결한다. 경로가 없으면 `sourceDirs`를 제안하고 사용자의 범위 결정을 받는다.

## Analyze (`--analyze`, Phase A1~A4)

코드를 수정하지 않고 아키텍처·품질·의존성·패턴·기술 부채를 분석한다.

### Phase A1: 범위와 초점

플래그 뒤 경로가 있으면 범위로 사용한다. 없으면 전체/디렉터리/파일 중 범위를 확인한다. 초점은
복수 선택할 수 있다.

1. 아키텍처: 레이어, 모듈 결합, 인터페이스
2. 코드 품질: 복잡도, 중복, dead code, smell
3. 의존성: 외부 패키지, 내부 그래프, 순환
4. 패턴과 기술 부채: 일관성, anti-pattern, TODO/FIXME
5. 전체(기본)

사용자 요청에 관심사가 있으면 별도 context로 보존한다.

### Phase A2: 상태

`{STATE_FILE}`에 `Mode: analyze`, `Scope`, `Focus`, `Context`, 현재/남은 Phase를 기록하고
`코드 분석을 시작합니다.`라고 알린다.

### Phase A3: 분석

[agents/code-analyzer.md](agents/code-analyzer.md)를 읽고 해당 역할을 독립적인 읽기 전용 서브에이전트에
전달한다. 프롬프트에는 `{CWD}`, `{STATE_FILE}`, scope/focus/context, Phase A3/A4를 포함한다.
범위가 작거나 위임이 불가능하면 같은 역할 계약으로 직접 분석하되 축소 여부를 보고한다.

반환 결과는 구체적인 `file:line`, 측정값, 확인한 명령을 포함해야 한다. 범위 밖 일반론은 제외한다.

### Phase A4: 보고

다음 머리글을 유지한다.

```markdown
## Code Analysis Report

### 분석 개요
- **모드**: Analyze
- **범위**: {scope}
- **초점**: {focus}

{code-analyzer 결과}

### 추가 조치
```

발견 사항 수정은 보고와 분리한다. 전체/선택/건너뛰기 중 사용자의 명시적 선택을 받은 뒤에만 수정하고,
수정 후 커밋 여부도 별도로 확인한다. 상태의 Remaining Phases를 `없음`으로 마감한다. 기본은 상태를
보관하고 사용자가 정리를 요청한 경우에만 검증된 `{RUN_DIR}`를 정리한다.

## Verify (`--verify`, Phase V1~V5)

보안·성능·잠재 버그·안정성을 검증하고 `PASS/WARN/FAIL`을 판정한다. 검증 자체는 읽기 전용이다.

### Phase V1: 범위와 초점

플래그 뒤 경로를 사용하고 없으면 범위를 확인한다. 초점은 복수 선택할 수 있다.

1. 보안: injection, 인증/인가, 데이터 노출
2. 성능: N+1, 리소스/메모리, 네트워크
3. 잠재 버그: nil, 동시성, 에러 처리, 경계 로직
4. 안정성: 자원 정리, 복원력, 테스트 커버리지
5. 전체(기본)

### Phase V2: 상태와 정적 분석

`{STATE_FILE}`에 `Mode: verify`, `Scope`, `Focus`, 현재/남은 Phase를 기록한다. 비어 있지 않은 명령을
다음 순서로 실행하고 결과를 append한다.

1. `{lintCommand}`
2. `{buildCommand}`
3. `{typeCheckCommand}`
4. 초점이 전체/안정성이면 `{testCommand}`와 coverage 결과

빈 명령은 `SKIPPED:PROFILE_EMPTY`다. 이 Phase는 코드 파일을 수정하지 않는다.

### Phase V3: 코드 검증

[agents/code-verifier.md](agents/code-verifier.md)를 읽고 읽기 전용 검증 역할에 scope/focus, 정적 분석
결과, `{CWD}`, `{STATE_FILE}`, Phase V3/V4/V5를 전달한다. 이론적 가능성이 아니라 실제 도달 경로와
`file:line` 근거가 있는 이슈만 받는다.

### Phase V4: 컨벤션 검사

초점이 `전체`일 때만 형제 `../../convention-check/SKILL.md`를 읽고 그 검사 절차를 현재 컨텍스트에서
수행한다. 결과는 `위반: N건`으로 기록한다. 그 외에는 `SKIPPED:FOCUS_NOT_FULL`이다.

### Phase V5: 종합 보고

다음 머리글과 표를 유지한다.

```markdown
## Code Verification Report

### 검증 개요
- **모드**: Verify
- **범위**: {scope}
- **초점**: {focus}

### 정적 분석 결과
| 도구 | 판정 | 비고 |
|------|------|------|
| lint | PASS/FAIL/SKIPPED | {요약} |
| build | PASS/FAIL/SKIPPED | {요약} |
| typecheck | PASS/FAIL/SKIPPED | {요약} |
| test/coverage | PASS/FAIL/SKIPPED ({%}) | {요약} |

### 코드 검증 결과
{code-verifier 결과}

### 컨벤션 검사 결과
{결과 또는 미실행}

### 종합 판정
| 항목 | 판정 |
|------|------|
| 정적 분석 | PASS/FAIL |
| 보안 | PASS/WARN/FAIL |
| 성능 | PASS/WARN/FAIL |
| 잠재 버그 | PASS/WARN/FAIL |
| 안정성 | PASS/WARN/FAIL |
| 컨벤션 | PASS/WARN/FAIL 또는 SKIPPED |
| **종합** | **PASS/WARN/FAIL** |

### 즉시 수정 권고 (Critical + High)
{이슈 목록}
```

종합은 가장 나쁜 카테고리 판정을 따른다. 발견 사항 수정은 Critical+High 전체/선택/건너뛰기 중
사용자의 승인을 받은 후에만 수행하고 커밋 여부도 확인한다. 상태를 마감하고 실행 중 시작한 세션이
있다면 정리한다.
