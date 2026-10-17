# 외부 응답 픽스처 출처

수집일: **2026-10-17**. 인증 없이 아래 공식 **문서 페이지**만 열람했다.
실제 채용 API 엔드포인트는 호출하지 않았고 인증키를 사용하거나 저장하지 않았다.
고용24 상세 페이지는 웹 열람 도구 오류 후 Python 표준 라이브러리로 같은 문서 HTML을 확인했다.

- [S1: 사람인 채용 공고 API 가이드](https://oapi.saramin.co.kr/guide/job-search): JSON 응답 예시, 출력 필드표, JSON/XML 오류 예시 및 오류 코드표.
- [W3: 고용24 채용정보 목록 명세](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiSvcInfo.do?fullApiSvcId=000000000000000000000000000000): `wantedRoot` XML 출력 필드표. 사용예제는 요청 URL이며, 값이 채워진 XML 응답 예시는 확인하지 못했다.
- [W4: 고용24 채용정보 상세 명세](https://www.work24.go.kr/cm/e/a/0110/selectOpenApiSvcInfo.do?fullApiSvcId=000000000000000000000000000000%5E000000000000000000000000000001%5E000000000000000000000000000003): `wantedDtl` XML 출력 필드표. 값이 채워진 XML 응답 예시와 오류 응답 형식은 확인하지 못했다.

아래 모든 파일의 수집일은 2026-10-17이다. **합성** 응답은 실제 응답과 다를 수 있다.
게이트 1에서 승인된 실제 응답을 확보하면 개인정보·키를 제거한 응답으로 교체해야 한다.
현재 합성 픽스처를 공급자와의 실연동 검증 증거로 사용하면 안 된다.

| 파일 | 출처 | 공식/합성 | 변경·구성 내역 |
| --- | --- | --- | --- |
| `saramin/list_ok.json` | S1 JSON 응답 예시 구조 및 필드표 | 합성: 공식 예시 기반 | 원래 2건인 예시를 가상 공고 3건으로 재작성. 이름·제목·ID·URL·시각·급여를 가상 값으로 교체하고 경력 신입/경력/무관을 구성. `jobs.total="5"`, `start=0`, `count=3`. 선택 필드는 생략. |
| `saramin/list_page2.json` | S1 JSON 응답 예시 구조 및 필드표 | 합성: 공식 예시 기반 | 같은 5건 쿼리의 마지막 페이지. 중복 없는 가상 공고 2건, `start=1`, `count=2`, `total="5"`. |
| `saramin/list_empty.json` | S1 JSON 응답 예시 구조 및 필드표 | 합성 | `job=[]`, `total="0"`, `count=0`, `start=0`으로 빈 검색 결과 구성. |
| `saramin/list_missing_fields.json` | S1 JSON 응답 예시 구조 및 필드표 | 합성 | 별도 가상 공고 1건에서 `position.experience-level`, `position.required-education-level`, `expiration-timestamp`, `salary`, `keyword` 제거. 누락 상태의 안전한 처리용이며 공급자의 생략 보장은 아님. |
| `saramin/error_quota.json` | S1 JSON 오류 예시 구조 및 오류 코드표 | 합성 | 공식 코드 `4` 사용. `message`는 코드표 설명으로 합성했으며 실제 메시지 미확인. JSON 예시처럼 최상위 `code/message` 사용(`result` 래퍼 없음). |
| `saramin/error_auth.json` | S1 XML 인증 오류 예시 및 JSON 오류 예시 구조 | 합성 | XML 예시의 `code=2`와 메시지(끝 공백 포함)를 JSON 최상위 `code/message` 구조로 옮김. 유효하지 않은 키의 실제 JSON 응답은 미확인. |
| `saramin/error_missing_key.json` | S1 Sample Output JSON 오류 예시 | 공식 예시 그대로 | `code=1` 키 미입력 예시의 JSON 값과 구조를 그대로 보존. 들여쓰기만 정리. |
| `work24/list_ok.xml` | W3 XML 출력 필드표 | 합성 | `wantedRoot` 아래 `total=5`, `startPage=1`, `display=3`과 가상 공고 3건 구성. ID·회사·직무·급여·학력·경력·날짜·URL 등을 합성. 사업자번호는 0으로 채움. |
| `work24/list_page2.xml` | W3 XML 출력 필드표 | 합성 | 같은 쿼리의 마지막 페이지 `startPage=2`, `total=5`, 가상 공고 2건. `display=3`은 동일한 요청 페이지 크기로 유지. |
| `work24/list_empty.xml` | W3 XML 출력 필드표 | 합성 | `total=0`, `startPage=1`, `display=3`, `wanted` 요소 없음. |
| `work24/list_missing_fields.xml` | W3 XML 출력 필드표 | 합성 | 별도 가상 공고 1건에서 `minEdubg`, `maxEdubg`, `career`, `closeDt`, `sal`, `minSal`, `maxSal` 제거. 명세의 실제 생략 보장이 아닌 방어 처리용. |
| `work24/detail_ok.xml` | W4 XML 출력 필드표 | 합성 | 목록 첫 공고의 가상 상세. `corpInfo.totPsncnt=120`, `wantedInfo.jobCont`와 경력·학력·고용·급여 코드 구성. 대표자명은 홍길동, 전화·팩스는 02-0000-0000. 첨부·연락처 등 일부 필드는 생략. |
| `work24/detail_missing_fields.xml` | W4 XML 출력 필드표 | 합성 | `detail_ok.xml`에서 `corpInfo.totPsncnt`, `wantedInfo.jobCont`, `empchargeInfo` 제거. |
| `work24/error.xml` | W3/W4 검토: 오류 응답 명세 없음 | 합성: **형식 미확인, 추정** | 테스트 전용 `<error><message>` 구성으로 실제 오류 코드·래퍼를 단정하지 않음. 이 XML 구조를 운영 어댑터의 확정 계약으로 삼지 말고 게이트 1에서 실제 오류 응답 확인 후 교체. |

## 페이지·자료형과 개인정보 처리

- 사람인 `start`는 0 기반 페이지 번호다. 첫 페이지 3건과 마지막 페이지 2건의 합이 `total=5`이며 `count`는 반환 공고 수다. `total`·ID·시각은 공식 JSON 예시의 문자열 자료형, `active`·경력 코드/최소/최대는 숫자 자료형을 따른다. 예시의 선택 필드와 일부 직무·업종 필드는 필수 범위 밖이라 생략했다.
- 고용24는 문서의 `returnType=XML` 계약을 따르는 UTF-8 XML이다. 목록은 1 기반 페이지, `display=3` 요청 크기, 총 5건이다. 목록 날짜 `26-10-17`/`26-10-31`, 상세 날짜 `2026-10-31`, 급여 숫자의 단위와 원문 링크 경로·쿼리는 테스트용 합성값이며 실제 형식 확인이 필요하다.
- 목록·상세 연결은 `wantedAuthNo=K000002610170001`이다. 누락 목록은 별도 ID를 사용한다. 사람인·고용24의 URL은 원문 사이트 도메인으로 구성했으며 실재 공고 존재를 보장하지 않는다. 어떤 링크도 열어 수집하지 않았다.
- 연락처 원문은 복사하지 않았다. 가상 인명은 홍길동, 연락처는 02-0000-0000, 이메일을 추가할 때는 recruit@example.com을 사용한다. 인증키 필드·값은 포함하지 않는다.
- `test_fixture_hygiene.py`는 전체 트리를 읽어 JSON/XML 파싱과 키·이메일·전화번호 위생을 검사한다. XML은 defusedxml로 파싱하며 엔티티 선언을 거부한다. `tmp_path` 위반 자료는 테스트 실행 중 생성하고 커밋하지 않는다.
