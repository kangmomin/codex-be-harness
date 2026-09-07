# 최종 결정 이후 검증과 반영

Phase 12 결정은 받는 즉시 `## Final Decisions`에 기록하고 재개 시 다시 묻지 않는다. 최초 보고서는 결정용 초안이다.

1. 승인한 코드·Spec·테스트 수정은 Terra executor가 수행한다. Sol High는 상태·구현 노트만 갱신한다. Baseline 원본은 바꾸지 않는다.
2. 영향 범위의 Phase 7~9 빌드·단위/E2E·컨벤션 검증 및 동작 변경의 Read-back을 다시 수행한다. [result-contract.md](result-contract.md)의 RESULTS_FILE에 새 iteration과 실제 tested_tree를 기록한다. 미해결 실패는 해당 Phase의 BLOCKED/FAIL로 유지한다.
3. 검증된 소유 변경만 동봉 commit 절차로 논리 커밋한다. `PUBLISH_POLICY`가 local이면 로컬 commit만, push이면 commit-hard-push, pr이면 commit-pr의 미완료 단계/기존 PR 갱신, none이면 Build commit/원격 반영 없이 보고만 한다. 브랜치/VERSION/PR을 중복 생성하지 않는다.
4. 모든 commit/amend/rebase 후 현재 HEAD로 Assumption Gate를 다시 수행한다. 테스트 때와 HEAD가 달라지면 새 tested_tree로 필요한 검증을 재실행한다. 과거 PASS의 해시를 수동으로 교체하지 않는다. 승인된 push/PR이 남아 있으면 이를 완료하고 원격 HEAD/PR URL을 확인한다.
5. WORK_REPORT의 검증 표는 JSON의 마지막 결과에서 작성한다. 최종 수정·검증·반영·보류를 반영한다. 필수 작업이 모두 완료된 경우에만 마지막 Phase를 DONE, Remaining Phases를 없음으로 마감하고 RESULTS_FILE의 terminal_state/tested_tree를 검증한다.
6. 미해결 BLOCKED/FAIL을 일괄 DONE/SKIPPED로 바꾸지 않는다. 명시적으로 범위에서 제외한 항목은 사유를 기록하되 과거 실패 이벤트를 보존한다. 필수 작업이 남으면 live 결과와 상태를 보관하고 영구 아카이브를 만들지 않는다. 완료 시 `workflow_archive.py --results`로 1회 배타 생성한다. 실패 시 원문 경로/오류를 보고하고 cat/cp/replace 폴백을 하지 않는다.
