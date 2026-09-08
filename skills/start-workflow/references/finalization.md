# 최종 결정 이후 검증과 반영

Phase 12 결정은 받는 즉시 `## Final Decisions`에 기록하고 재개 시 다시 묻지 않는다. 최초 보고서는 결정용 초안이다.

1. 승인한 코드·Spec·테스트 수정은 Terra executor가 수행한다. Sol High는 상태·구현 노트만 갱신한다. Baseline 원본은 바꾸지 않는다.
2. 영향 범위의 Phase 7~9 빌드·단위/E2E·컨벤션 검증 및 동작 변경의 Read-back을 다시 수행한다. [result-contract.md](result-contract.md)의 RESULTS_FILE에 새 iteration과 실제 tested_tree를 기록한다. 미해결 실패는 해당 Phase의 BLOCKED/FAIL로 유지한다.
3. 검증된 소유 변경만 동봉 commit 절차로 논리 커밋한다. `PUBLISH_POLICY`가 local이면 로컬 commit만, push이면 commit-hard-push, pr이면 commit-pr의 미완료 단계/기존 PR 갱신, none이면 Build commit/원격 반영 없이 보고만 한다. 브랜치/VERSION/PR을 중복 생성하지 않는다.
4. 모든 commit/amend/rebase 후 현재 HEAD로 Assumption Gate를 다시 수행한다. 테스트 때와 HEAD가 달라지면 새 tested_tree로 필요한 검증을 재실행한다. 과거 PASS의 해시를 수동으로 교체하지 않는다. 승인된 push/PR이 남아 있으면 이를 완료하고 원격 HEAD/PR URL을 확인한다.
5. WORK_REPORT의 검증 표는 JSON의 마지막 결과에서 작성한다. 최종 수정·검증·반영·보류를 반영한다. 필수 작업이 모두 완료된 경우에만 마지막 Phase를 DONE, Remaining Phases를 없음으로 마감하고 RESULTS_FILE의 terminal_state/tested_tree를 검증한다.
6. 미해결 BLOCKED/FAIL을 일괄 DONE/SKIPPED로 바꾸지 않는다. 명시적으로 범위에서 제외한 항목은 사유를 기록하되 과거 실패 이벤트를 보존한다. 필수 작업이 남으면 live 결과와 상태를 보관하고 영구 아카이브를 만들지 않는다. 완료 시 `workflow_archive.py --results`로 1회 배타 생성한다. 실패 시 원문 경로/오류를 보고하고 cat/cp/replace 폴백을 하지 않는다.

## 최종 트리와 검증 재사용

현재 `workflow_results.py check-current`는 `--require` 목록뿐 아니라 **모든 최신 non-pr 이벤트**의 tested_tree를 대조한다. 문서·VERSION·commit도 HEAD 또는 content_sha256을 바꾸므로, 영향 범위 검증만 마쳤어도 과거 이벤트가 stale이면 마감할 수 없다. 마지막 로컬 수정·커밋을 끝낸 트리에서 stale인 종류/케이스의 검증을 실제 재실행해 새 iteration으로 기록한다. 원래 SKIP 조건이 적용되는 항목만 현재 근거로 다시 판정하며, 미해결 실패를 SKIP으로 바꾸거나 과거 해시만 교체하지 않는다.
Read-back의 “루프 밖 1회”는 최초 품질 검증 횟수다. 최종 수정·HEAD 변경으로 기존 결과가 stale인 경우에는 이 마감 절차에서 격리를 유지해 재검증한다. 검증할 트리가 더 바뀌지 않도록 문서·버전·로컬 커밋을 먼저 마무리하고, 현재 트리의 필수 근거가 모두 갖춰진 뒤에는 새 근거 없는 추가 리뷰를 돌리지 않는다. 재검증 불가 시 미완료와 남은 stale 항목을 보고한다.
