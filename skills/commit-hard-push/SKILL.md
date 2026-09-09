---
name: commit-hard-push
description: "보호 브랜치 제한 없이 /commit 진행 후 현재 브랜치에 그대로 push한다. main 등 보호 브랜치에 직접 push해야 할 때, '그냥 현재 브랜치에 올려줘' 요청 시 사용."
---

실행 전에 [공통 실행 원칙](../start-workflow/references/execution-policy.md)을 읽는다.

> **Project Overrides**: 실행 전 `.codex/be-harness/common.md`와 `.codex/be-harness/skills/commit-hard-push.md`를 읽기.
> 존재하면 추가 규칙/예외로 흡수하고 충돌 시 오버라이드가 우선한다. 상세 규약: 플러그인 루트 `OVERRIDES.md`.

# Commit & Hard Push

`$codex-be-harness:commit-push`와 달리 **브랜치 판정·생성·네이밍 검증을 모두 생략**하고, 어떤 브랜치에서든 현재 브랜치에 그대로 push한다.


## Workflow commit → 검증 → 원격 반영 배리어

start-workflow 내부에서는 VERSION/논리 commit/amend/rebase 준비까지 수행한 뒤 **push 전에** 현재 HEAD·소유 변경 목록·완료 단계를 Orchestrator에 반환한다. Orchestrator가 check-current로 검증 입력을 대조한다. 내용 동일 v2·HEAD 비의존 이벤트는 재사용하고, stale인 빌드/테스트만 실행해 RESULTS_FILE에 새 iteration을 기록한다. 현재 HEAD로 check-current와 Assumption Gate를 통과시킨다.
Orchestrator는 검증한 HEAD와 승인된 PUBLISH_POLICY를 전달해 같은 작업의 미완료 push/PR 단계만 재개한다. Worker는 HEAD가 같음을 즉시 확인하고 원격 반영한다. 이 재개에서는 VERSION/commit을 중복 수행하지 않는다. HEAD가 또 바뀌면 다시 배리어로 돌아간다. standalone은 요청된 검증/승인 범위를 따른다.

## Step 1: 커밋

`$codex-be-harness:commit` 절차를 수행해 변경사항을 논리 단위별로 커밋한다.

## Step 2: Assumption Gate

`$codex-be-harness:commit-push`의 Step 3(Assumption Gate) 절차를 수행한다. `[Assumption]` 태그가 모두 해소되기 전에는 push하지 않는다.
코드 base와 미push 메시지 기준을 구분한다. 보호 브랜치 직접 push는 fetch한 해당 원격 브랜치를 코드 기준으로 쓸 수 있다. feature upstream을 PR base로 임의 대체하지 않는다. 명시 upstream/base 미존재나 Git 오류는 BLOCKED다. 커밋 이후 검사한 HEAD를 기록하고 push 직전 동일성을 확인한다.

## Step 3: Push

```bash
git push -u origin {현재 브랜치}
```

실패 시: 에러 원문과 원인 분석을 보고하고 중단한다 (커밋은 로컬에 보존됨).

## Codex 실행 계약

`{PLUGIN_ROOT}`는 현재 설치된 이 플러그인의 절대 루트다. 형제 스킬은 해당 `SKILL.md`를 읽고 절차를 수행한다.
profile은 `../../PROFILE.md`의 `{PROFILE_PATH}` 해석을 따르고 workflow에서는 전달받은 `## Profile Snapshot`을 사용한다.
사용자가 요청한 commit/push/PR 범위와 기존 승인을 재사용한다. 원격 작업은 그 효과가 승인된 경우에만 수행한다.
