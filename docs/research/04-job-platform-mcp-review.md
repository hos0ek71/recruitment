# 참고 저장소 검토: sjungwon03/job-platform-mcp

조사일: 2026-10-17 · 대상: https://github.com/sjungwon03/job-platform-mcp (Glama: https://glama.ai/mcp/servers/sjungwon03/job-platform-mcp)

## 결론

수집 파이프라인의 참고 설계로는 맞지 않는다. 평가 기준표와 약관 정리 방식 같은 아이디어만 참고한다.

## 근거

| 항목 | 확인한 사실 | 출처 |
| --- | --- | --- |
| 현재 방식 | Playwright로 화면에 보이는 Chrome을 띄워 원티드·사람인·잡코리아의 공개 검색 화면을 읽는다. 호출당 최대 20건, 다음 페이지·무한 스크롤·결과 저장·예약 수집은 하지 않는다 | COMPLIANCE.md, PR #13 |
| 우리 설계와의 관계 | 우리 MVP는 끝까지 수집, 결과 저장, 매일 자동 수집이 목표이고 스크래핑과 브라우저 자동화를 제외했다. COMPLIANCE.md도 "지속 모니터링, 예약 수집이 필요하면 이 프로젝트를 쓰지 말라"고 적는다 | 설계 문서 "MVP에서 하지 않을 것", COMPLIANCE.md |
| Glama 설명과 다른 이유 | Glama는 공식 API 방식이던 이전 버전을 설명한다. 2026-08-28 PR #13(커밋 33ab87f)에서 API 클라이언트를 모두 지우고 브라우저 방식으로 바꿨다 | 커밋 이력, PR #13 |
| 전환 이유 | "세 채용 MCP가 공식 API 승인과 사용자별 인증정보를 전제로 해 개인 구직자가 바로 사용할 수 없었다" | PR #13 본문 |
| 이전 API 코드의 수준 | 잡코리아 클라이언트는 승인 후 받은 호출 URL에 파라미터를 넘기는 얇은 래퍼이고, 응답이 JSON인지 XML인지도 정하지 않았다(실제 응답 미확인). 원티드는 V2 client ID/secret 방식 | 커밋 185b669의 packages/*/src/tools/jobs.ts |
| 라이선스 | LICENSE 파일이 없다(GitHub licenseInfo null). 코드나 문서를 복사하지 않고 아이디어만 참고한다 | GitHub API |
| 성숙도 | 2026-08-27~28 이틀 동안 커밋 20개, 별 0개. Glama에 "This server cannot be deployed" 표시 | GitHub API, Glama |

## 참고할 것

- `skills/job-match-search/references/matching-rubric.md`의 근거 4단계(확인, 추정, 미확인, 불일치)와 "공고 정보가 없다는 이유만으로 불충족으로 단정하지 않는다"는 규칙. 우리 적합도 평가(A-2)의 `match_reasons`, `missing`, `needs_check`와 잘 맞는다. 단 근무 조건(지역, 고용형태)은 우리 설계에서 코드 필터가 맡으므로 점수 항목에서 뺀다.
- COMPLIANCE.md처럼 플랫폼별 약관, 이용 조건, 중단 조건을 문서로 남기는 방식.

## 시사점

개인이 원티드·잡코리아 공식 API 승인을 받기 어렵다는 근거가 하나 더 생겼다(docs/mvp-design-review.md D0). 사람인 승인이 MVP의 핵심 경로다.
