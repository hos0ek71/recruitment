1. **새 주력 소스로 확정할 경로는 없음**: 검색 API는 웹 색인의 일부이며, 공고 전체·민간 신입 IT 포함률을 보장하지 않는다. [N2·N4·K1·B2, 확인 2026-10-19]
2. **네이버 판정은 ‘부분’**: 공고 링크 발견은 가능하나 채용 전용 API는 없고, 기존 Open API 신규 신청은 종료됐으며 저장·가공·AI 입력 제약 때문에 공고 원장 수신기로는 불가다. [N1·N2·N3·N5, 확인 2026-10-19]
3. **Google 신규 이용 불가·Bing 기존 검색 API 종료**: 각각 2027-01-01 종료 예정·2025-08-11 종료로 새 기반에서 제외한다. [G1·M1, 확인 2026-10-19]
4. **새 RSS 후보는 인크루트**: 신입공채·IT 분류가 공식 안내에 있으나 현재 피드 응답·전체성·영구 저장 허락은 확인 못 함이며, 잡코리아 RSS는 공식 종료 공지가 있다. [R1·R2·R3, 확인 2026-10-19]
5. **sitemap·JobPosting은 이용 허가가 아님**: 포털 상세를 요청하지 않아 JSON-LD 현존은 확인 못 함이며, 기존 대학 RSS·메일·공유 URL 제안을 새 소스로 중복 계산하지 않는다. [S1·S2·S3·P1, 확인 2026-10-19]

# 비크롤링 채용 공고 수신 경로 조사

작성일·모든 외부 출처 확인일: **2026-10-19 (KST)**. 표의 출처 ID는 마지막 출처 목록의 공식 URL 및 확인일과 대응한다. ‘추정’은 제공 범위·필드로부터의 연구자 판단이며 실제 포함률 측정 결과가 아니다. ‘불가’는 현재 프로젝트의 영구 원본 보관·정규화·평가 경로로 사용할 수 없다는 운영 판정이며, 서비스 자체가 없다는 뜻으로 쓰지 않는다.

## 조사 범위와 이전 조사와의 차이

사람인 API, 고용24 공채속보, 공공기관 채용정보(15125273), 지방공기업(15159757), 잡코리아·원티드 API의 자격은 재조사하지 않았다. 대학 RSS 2곳과 메일·Google 알리미·북마클릿·공유 URL은 기존 문서에서 이미 다룬 경로로 인용만 한다. 이번 추가 근거는 검색 서비스의 **현행 이관·종료·저장 조건**, 인크루트 RSS 공식 안내, 잡코리아 RSS 종료 공지다. [P1, 확인 2026-10-19]

공식 개발자 문서·약관·도움말·robots.txt와 공식 도메인 제한 검색만 이용했다. 채용 포털 검색 결과·공고 상세·sitemap의 공고 목록·RSS 실제 항목은 요청하지 않았다. 계정 생성, 키 신청, API 실호출, 로그인, 메일 접근 및 외부 메시지 발송은 하지 않았다. 검색엔진이 반환한 공고 화면 요약은 증거에서 제외했다.

## 후보 경로 표

각 행의 사실·추정은 해당 행의 출처에 근거한다. 공통 확인일은 **2026-10-19**다. 표에서 ‘보조용’도 저장·재가공 허락까지 확보했다는 뜻이 아니며, 조건 확인 전 자동 수신기를 구현할 근거로 쓰지 않는다.

| 경로 | 제공자 | 개인 발급 | 채용 공고를 얼마나 덮나: 민간 신입 IT 추정과 근거 | 완전성 확인 수단 | 한도 | 약관상 저장·재가공 허용 | 분류 | 출처 URL·확인일 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 기존 검색 Open API: 웹·뉴스·블로그 등 | NAVER Developers | 신규 불가: 2026-07-30 24:00 접수 중단; 기존 신청자만 유예 | 추정: 색인된 공고·관련 기사·후기 일부. 채용 전용 필드 없음 | `total`은 검색 문서 총수; 공고 총수 아님 | 기존 25,000회/일; `display≤100`, `start≤1000`; 기존 제공 2027-06-30까지 | 독립·무가공 표시, 출처·링크 필요. 영구 DB·AI 입력 불가; 제한적 임시 보관만 | **불가**: 신규 수신 원장. 기존 키가 있으면 검색 표시 보조만 | [N1](https://developers.naver.com/products/terms/)·[N4](https://developers.naver.com/docs/serviceapi/search/web/web.md), 2026-10-19 |
| 이관된 웹문서 검색 | NAVER API HUB / NCP | NCP 콘솔 발급 절차 공개; 개인 계정 존재는 FAQ에 있으나 HUB 개인 발급 성공·추가 자격 확인 못 함 | 추정: 기존과 같은 웹문서 계층. 직무·신입·마감 구조 데이터 없음 | `total/start/display`; 상위 검색 창만 순회 가능 | 검색 통합 월 775,000회·키당 50 RPS, 한시 무료. 개별 명세에는 일 25,000도 남아 있어 불일치 | 2026-09-20 개정 공지에 저장·가공·AI·수익화 제한. 영구 원장으로 전용 불가 | **누락 측정·보조용**: 약관 범위의 독립 검색 표시. 원장 수신은 불가 | [N2](https://guide.ncloud-docs.com/docs/apihub-overview)·[N3](https://api.ncloud-docs.com/docs/naver-api-hub-search-webkr)·[N5](https://www.ncloud.com/support/notice/all/2243)·[N6](https://www.ncloud.com/support/faq/mbr), 2026-10-19 |
| 웹문서 검색 | Kakao / Daum | 일반 개발 앱 REST 키 방식, 웹문서 요구사항에 별도 권한 없음; 실제 개인 발급 확인 못 함 | 추정: Daum 색인 일부. 공고·비공고 혼재, 채용 전용 대상 없음 | `total_count`, `pageable_count`, `is_end`; 노출 가능 집합 종료만 확인 | 웹 30,000회/일, 검색 합산 50,000회/일; 전체 API 월 300만; `page≤50`, `size≤50` | 서비스 약관상 사전 승낙 없는 정보 복제·변경 등 제한; 영구 공고 DB·LLM 전달의 별도 허락 확인 못 함 | **누락 측정·보조용**: 검색 결과 확인. 저장형 자동 수신은 보류 | [K1](https://developers.kakao.com/docs/ko/daum-search/dev-guide)·[K2](https://developers.kakao.com/docs/ko/getting-started/quota)·[K3](https://developers.kakao.com/terms/ko/site-terms)·[K4](https://developers.kakao.com/docs/ko/daum-search/common), 2026-10-19 |
| Programmable Search JSON API | Google | 신규 고객 불가 | 추정: 기존 이용자도 설정한 검색엔진의 색인 결과 일부 | `searchInformation.totalResults` 추정치; 최대 100결과로 전체성 검증 불가 | 기존 고객만 무료 100쿼리/일; 추가 $5/1,000·최대 10,000/일; 2027-01-01 종료 | 신규 경로가 막혔으므로 저장 조건 추가 판정 안 함: 확인 못 함 | **불가** | [G1](https://developers.google.com/custom-search/v1/overview)·[G2](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list)·[G3](https://developers.google.com/custom-search/v1/reference/rest/v1/Search), 2026-10-19 |
| Bing Search APIs | Microsoft | 신규·기존 모두 이용 종료 | 현행 수신 범위 없음 | 해당 없음 | 2025-08-11 종료 | 종료 서비스이므로 해당 없음 | **불가** | [M1](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement), 2026-10-19 |
| Web Search API | Brave | 공개 플랜 선택→키 생성 절차. 사업자 전용 문구 확인 못 함; 개인 발급 성공은 미검증 | 추정: 독립 웹 색인 보완. 한국 신입 IT 포함률 확인 못 함 | `query.more_results_available`; 공고 총수·시장 분모 없음 | Search $5/1,000회, 월 $5 크레딧, 50 QPS; `count≤20`, `offset≤9` | 기본 약관은 일시 저장 외 DB화·파생물 제한. 별도 storage rights 플랜 필요; 현행 해당 플랜 가격·개인 적용 확인 못 함. 원문 웹페이지 권리 별도 | **누락 측정·보조용**: 검색 발견. 영구 수신은 저장권 계약 전 보류 | [B1](https://brave.com/search/api/)·[B2](https://api-dashboard.search.brave.com/documentation/services/web-search)·[B3](https://api-dashboard.search.brave.com/terms-of-service)·[B4](https://api-dashboard.search.brave.com/documentation/guides/authentication), 2026-10-19 |
| 신입공채·직종별 공식 RSS 안내 | 인크루트 | 공개 구독 안내; 키 신청 절차 없음 | 추정: 신입공채·인터넷/IT/통신/모바일/게임 분류 때문에 관련성 있음. 실제 피드 유효성·신입 IT 건수 확인 못 함 | 총수·과거 페이지·정정/삭제 계약 확인 못 함 | 공식 안내에서 호출·보관창·발송주기 확인 못 함. URL에 `today=y`가 있으나 의미는 미확인 | RSS 리더 구독 안내 있음. 개인약관 제19조④의 사전 동의 없는 복제 등 제한에 비춰 영구 저장·재가공 특약 확인 필요 | **누락 측정·보조용**: 공식 구독 후보. 주력은 미확보 | [R1](https://people.incruit.com/rss/rss.asp)·[R2](https://help.incruit.com/docs/terms.asp), 2026-10-19 |
| 채용 RSS | 잡코리아 | 종료 | 없음: 현행 재개 확인 못 함 | 해당 없음 | 2014-06-25 종료 공지 | 현행 RSS 저장 허락 확인 못 함 | **불가** | [R3](https://www.jobkorea.co.kr/help/notice/view?no=13169), 2026-10-19 |
| 공식 채용 전용 RSS/Atom | 사람인·잡알리오·나라일터·워크넷/고용24 | **확인 못 함** | 포함률·현재 제공 범위 모두 확인 못 함. 기존 API·맞춤알림을 RSS로 세지 않음 | 확인 못 함 | 확인 못 함 | 확인 못 함 | **불가: 현재 확보된 경로가 없음**; 부재 단정 아님 | [R4](https://www2.saramin.co.kr/zf_user/help/help-word/main)·[R5](https://www.jobalio.go.kr/)·[R6](https://www.gojobs.go.kr/)·[R7](https://m.work24.go.kr/ua/common/selectDictionaryList.do), 2026-10-19 검색 확인 |
| 기관 뉴스룸 RSS | 고용노동부 | 공개 리더 등록 안내 | 추정: 정책·일반 공지 보조. 민간 신입 IT 공고 피드로 볼 근거 없음 | 공고 total 없음 | 호출·보관창 확인 못 함 | 구독 안내 외 공고 원장 재가공 허락 확인 못 함 | **불가**: 민간 공고 소스. 정책 소식은 별도 용도 | [R8](https://www.moel.go.kr/site/rss/rssList.do), 2026-10-19 |
| 대학 공식 채용 RSS | 부산대 정보컴퓨터공학부·고려대 세종 경력개발센터 | 기존 조사에서 공개 구독 확인; 이번 재호출 안 함 | 기존 보조 경로. 대학에 도착한 공고·추천전형·행사, 시장 포함률 미측정 | 기존 조사 50항목 최신 창; 시장 total 없음 | 호출 한도·전체 이력 확인 못 함 | 영구 원문 저장·재가공 허락 확인 못 함 | **누락 측정·보조용**; 신규 발견에 합산 안 함 | [P1](../ideation/2026-10-18-job-data-sources/02-public-channels.md)·[부산대 RSS](https://cse.pusan.ac.kr/bbs/cse/2060/rssList.do?row=50)·[고려대 RSS](https://cwms.korea.ac.kr/bbs/cdc/526/rssList.do?row=50), 기존 확인 2026-10-18·문서 확인 2026-10-19 |
| sitemap→상세 JobPosting JSON-LD | 채용 포털 | 키가 없다는 것과 개인 이용 허가는 별개 | 존재·포괄률 확인 못 함. 구조 필드가 있어도 상세 요청 필요 | sitemap URL 수는 공고 총수 아님 | 허용 호출·갱신·총수 계약 확인 못 함 | 허가 아님. 사람인·인크루트 개인약관에 무단 복제 제한 | **불가**: 현재 프로젝트의 상세 자동 수집 금지와 충돌 | [S1](https://schema.org/JobPosting)·[S2](https://developers.google.com/search/docs/appearance/structured-data/job-posting)·[S3](https://www.rfc-editor.org/rfc/rfc9309.html)·[S4](https://www.saramin.co.kr/zf_user/help/terms-of-service)·R2, 2026-10-19 |

## 네이버: ‘채용 공고를 얻을 수 있는가’의 명확한 판정

**부분 가능**이다. 검색어에 일치하는 공고의 제목·링크·요약이 색인에 있으면 검색 결과에 포함될 수 있다는 **명세로부터의 추론**이다. 실제 채용 검색 API 호출로 확인한 결과가 아니다. 웹문서 응답에는 채용 상태·신입 구분·직무·마감일·고용형태가 없다. 따라서 공고 링크 발견과 확정 필터용 공고 원본 수신을 구분해야 한다. [N3·N4, 확인 2026-10-19]

- **대상:** 현행 HUB 목록은 뉴스·블로그·지역·지식iN·카페·백과사전·이미지·웹문서와 성인어 판별·오타변환이다. 채용 대상은 없다. 오래된 Open API 소개에는 쇼핑·책·전문자료가 남아 있지만 기존 개발자센터의 해당 데이터 제공은 2026-07-31 종료됐으므로 현행 신규 대상에 넣지 않는다. 쇼핑 인사이트는 상품 또는 채용 공고 목록 API가 아니다. [N1·N2·N7, 확인 2026-10-19]
- **개인 신규 신청:** 기존 개발자센터 발급 경로는 현재 닫혔다. HUB의 계정별 앱 등록 절차와 NCP 개인 계정 관련 FAQ는 공개돼 있으나, 이 조사는 신청하지 않았으며 ‘일반 개인에게 무조건 발급’까지 확인 못 함이다. [N1·N6·N7, 확인 2026-10-19]
- **저장·상업 조건:** 개인 비상업이어도 무제한 이용 허락이 아니다. 기존 API와 HUB 개정 조건은 독립적인 무가공 검색 표시·출처 링크를 요구하고, AI 입력·수익화·영구 축적을 제한한다. 예외는 연속성 목적의 임시 보관으로, 기기에는 24시간 또는 새 질의 중 짧은 기간, 서버 이력 조회에는 최대 21일이며 목적별 조건이 있다. 이 예외를 공고 장부의 영구 원본 저장 허락으로 확대하지 않는다. [N1·N5, 확인 2026-10-19]
- **결과 상한:** 명세는 시작 위치 최대 1,000과 응답 최대 100을 명시한다. `start=1000,display=100`의 경계 동작은 확인 못 했으므로 ‘정확히 1,000건 모두 보장’ 또는 ‘1,099건 보장’으로 해석하지 않는다. `total`이 크더라도 무제한 마지막 페이지까지 받는 계약은 없다. [N3·N4, 확인 2026-10-19]
- **한도 문서 불일치:** HUB 개요·등록 안내는 검색 합산 월 775,000을, 웹문서 개별 명세는 여전히 일 25,000을 안내한다. 월 관리 안내를 현행 운영 설명으로 인용하되 실계정 유효 한도와 일 제한 병존 여부는 **확인 못 함**으로 남긴다. [N2·N3·N7, 확인 2026-10-19]

**적용 결론:** 별도 검색 화면의 후보 발견에는 조건부 보조 가치가 있다. 응답을 DB에 영구 저장하고 정규화·AI 평가까지 하는 신규 수신 어댑터로는 사용하지 않는다. 검색으로 발견한 결과를 자동 저장하는 것을 ‘사용자가 준 링크’라고 이름만 바꿔 우회하지 않는다. [N1·N5에 따른 운영 판정, 확인 2026-10-19]

## RSS·Atom·뉴스룸의 실제 확인 수준

### 새로 찾은 인크루트 경로

공식 RSS 안내는 신입공채와 IT 직종 등 분류를 나열하고 RSS 버튼을 눌러 리더에 주소를 등록하라고 설명한다. 안내 HTML의 버튼 인자에서 신입공채 주소 `https://www.incruit.com/rss/job.asp?jobtycd=1&today=y`를 확인했다. 이 주소는 **안내에서 추출한 문자열이며 실제 피드를 호출하지 않았다**. IT 분류와 신입공채의 교집합 조건·공고 본문·반환 건수·최근 갱신·현재 HTTP 응답은 확인 못 함이다. [R1, 확인 2026-10-19]

개인약관 제19조④에는 사전 동의 없는 서비스 정보 복제·변경 등에 대한 제한이 있다. RSS 구독 안내는 리더 수신의 근거지만, 자체 DB 장기 보관·정규화·LLM 평가 허락까지 확인한 것은 아니다. **후속 확인 순서 제안:** 운영자에게 해당 RSS의 현행 제공·개인 1명 보관/가공 조건 문의 → 허용 후 소량 피드 검증 → 누락 창·정정·마감 처리 확인이다. 이번에는 문의하지 않았다. [R1·R2, 확인 2026-10-19]

### 확인 대상별 부재와 미확인의 구분

- **잡코리아:** 2014-05-30 공지가 2014-06-25 RSS 종료와 XML/API 안내를 명시한다. 현행 RSS 재개 공식 문서는 확인 못 함이다. 기존 RSS 소개나 오래된 URL을 현행 공급으로 채택하지 않는다. [R3, 확인 2026-10-19]
- **사람인:** 공식 도움말 영역과 공식 도메인 RSS 검색에서 현행 채용 전용 피드·개인 이용조건 확인 못 함이다. 사람인 API가 존재한다는 사실은 새 RSS의 근거가 아니다. [R4·P1, 확인 2026-10-19]
- **잡알리오:** 공식 도메인 RSS 검색에서 현행 피드·구독조건 확인 못 함이다. 기존 맞춤 푸시·메일은 RSS로 중복 계산하지 않는다. [R5·P1, 확인 2026-10-19]
- **나라일터:** 공식 도메인 RSS 검색에서 현재 배포 주소·조건 확인 못 함이다. 과거 언론 소개만으로 현재 작동을 확정하지 않았다. [R6, 확인 2026-10-19 검색 확인]
- **워크넷/고용24:** 고용24 용어사전은 RSS의 일반 개념을 설명하지만 현행 채용 피드 주소·범위·조건의 근거가 아니다. 확인 못 함이다. [R7, 확인 2026-10-19]
- **고용노동부:** 공식 RSS는 알려드립니다·정책자료·입법행정예고 3종이다. RSS 설명에 ‘채용공고’라는 예시 단어가 있어도 고용24 전체 채용정보 피드라고 해석하면 안 된다. [R8, 확인 2026-10-19]
- **대학:** 기존 부산대·고려대 RSS 외 새로운 검증 후보는 이번에 확보하지 않았다. 공개 열람·구독과 학교 추천전형 지원자격, 원문 복제 허락은 별도다. [P1, 기존 확인 2026-10-18·문서 확인 2026-10-19]
- **Atom·기업/포털 뉴스룸:** 조사 대상에서 새 채용 전용 Atom 또는 민간 신입 IT 공고 공급을 보장하는 뉴스룸 피드는 확인 못 함이다. 일반 정책·보도자료를 공고 소스로 세지 않았다. [R1·R4~R8의 제한된 검색·안내 검토, 확인 2026-10-19]

미확인 항목은 존재하지 않는다는 전수 조사 결론이 아니다. 특히 robots나 URL의 공개 상태만으로 피드 주소를 추정·생성하지 않았다.

## sitemap·JobPosting JSON-LD

schema.org는 `JobPosting`에 제목·설명·채용기관·게시일·지원 유효기간 등 공고 표현 필드를 정의하고, Google은 채용 상세 페이지에 구조화 데이터를 넣는 게시자용 방법을 안내한다. 이는 표준 형식·검색 노출 방식의 근거이며, 제3자 수집 API 계약이 아니다. [S1·S2, 확인 2026-10-19]

| 대상 | 실제로 확인한 것 | JobPosting JSON-LD 존재 | 약관상 읽기·보관 허용 판정 |
| --- | --- | --- | --- |
| 사람인 | 개인약관 제19조④의 무단 복제 등 제한. robots 도구 열람 실패 | **확인 못 함**: 상세 요청 금지 준수 | 개인 자동 상세 수신·원문 보관 허락 확인 못 함. 현재 수집 불가 [S4·S6, 2026-10-19] |
| 잡코리아 | robots에 sitemap 선언과 일부 크롤러별 차단 규칙 있음; sitemap 자체는 열지 않음 | **확인 못 함**: 상세 요청 안 함 | robots는 이용허가가 아님. 개인 원장 저장 허락 확인 못 함 [S3·S5, 2026-10-19] |
| 인크루트 | 개인약관 제19조④ 복제 등 제한; robots 도구 열람 실패 | **확인 못 함**: 상세 요청 안 함 | RSS 안내가 상세 전체 요청 허락을 대체하지 않음 [R1·R2·S7, 2026-10-19] |

RFC 9309는 robots 규칙이 접근 권한 부여 수단이 아니라고 명시한다. 따라서 ‘robots 미차단 → JSON-LD 가져와도 됨’이라는 추론을 사용하지 않는다. JSON-LD를 읽으려고 상세 HTML을 자동 요청하면 이 프로젝트에서 제외한 페이지 수집이라는 실행 방식도 그대로 남는다. 이미 정리된 레드팀 결론을 뒤집을 새 허가 근거는 확보하지 못했다. [S3·P1, 확인 2026-10-19]

## 사용자가 넘기는 링크·메일의 추가 아이디어

공유 URL, URL+직접 입력, 북마클릿, 모바일 공유, 본인 메일, 기업 구독메일, Google 알리미는 기존 C1~C7에서 다뤘다. 이번에 **새 외부 공급 경로는 확인 못 함**이다. 새 기능처럼 다시 나열하지 않는다. [P1, 문서 확인 2026-10-19]

추가할 수 있는 것은 공급처가 아니라 **수동 전달의 누락 방지 절차**다. 사용자가 이미 확보한 링크와 직접 쓴 제목·발견일을 한 번에 붙여 넣는 배치 접수함을 두고 접수번호·중복 여부·저장 결과를 보여주는 방안을 제안한다. 서버의 URL 미리보기·본문·JSON-LD 요청은 포함하지 않으며, 공급 권한·범위가 늘었다고 계산하지 않는다. 이는 구현·약관 검증을 마친 기능이 아닌 연구자 제안이다. [기존 C4의 확장 제안, P1, 2026-10-19]

## 판단과 다음 확인

**새 주력 소스 가능: 0개.** 인크루트 RSS는 가장 구체적인 신규 후보지만 현행 작동·저장권·누락 창이 미확정이다. Daum·Brave는 검색 기반 누락 표본 발견의 후보이고, NAVER HUB는 저장하지 않는 독립 검색 표시 범위에서만 보조 후보로 둔다. 여기서 검색 표본은 같은 색인·키워드 편향을 공유할 수 있으므로 전국 채용시장의 재현율 분모가 아니다. [N1~N5·K1~K4·B1~B4·R1~R2에 따른 추론, 확인 2026-10-19]

다음 행동은 인크루트 RSS 조건 문의와 Brave 저장권 플랜의 개인 적용 확인이다. 네이버는 API HUB 개인 자격·실제 쿼터 불일치를 확인해도 영구 원장 저장 제약이 해결되지 않으면 수신기로 채택하지 않는다. 새 키·실제 응답 검증은 사용자가 명시적으로 지시한 후속 작업에서만 한다. [위 공식 조건에 따른 제안, 2026-10-19]

## 출처 목록

아래는 모두 **확인일 2026-10-19**다. 검색만 확인했거나 도구 열람이 실패한 항목은 명시했다. 문서의 ID 인용은 이 URL·확인일을 함께 참조한다.

- **N1:** [NAVER API 서비스 이용약관](https://developers.naver.com/products/terms/) — 상단 2026-10-07 개정 표기; 검색 특약 2.1~2.4 및 이관 부칙. 과거 레퍼런스보다 현행 신청·권리 판정에 우선.
- **N2:** [NAVER API HUB 개요](https://guide.ncloud-docs.com/docs/apihub-overview) — 대상·월 한도·50 RPS·한시 무료.
- **N3:** [HUB 웹문서 명세](https://api.ncloud-docs.com/docs/naver-api-hub-search-webkr) — 필드·페이지와 일 25,000 잔존 문구.
- **N4:** [기존 네이버 웹문서 검색 명세](https://developers.naver.com/docs/serviceapi/search/web/web.md) — 기존 25,000/일 및 결과 창·필드.
- **N5:** [HUB 약관 개정 공지, 2026-09-20 시행](https://www.ncloud.com/support/notice/all/2243) — 공식 검색에 개정 비교표 확인; 본문 도구 파싱은 표 일부 미노출. 기존 API 약관 N1과 구분.
- **N6:** [NCP 회원 FAQ](https://www.ncloud.com/support/faq/mbr) — 공식 검색에서 개인→사업자 계정 변경 질문 확인; 본문 열람 실패. HUB 개인 발급 성공의 증거로 사용하지 않음.
- **N7:** [HUB Application 안내](https://guide.ncloud-docs.com/docs/apihub-application) — 제공 API 전체 목록·월 최대 호출·등록 절차.
- **K1:** [Daum 검색 REST API](https://developers.kakao.com/docs/ko/daum-search/dev-guide).
- **K2:** [Kakao 쿼터](https://developers.kakao.com/docs/ko/getting-started/quota).
- **K3:** [Kakao 서비스 약관](https://developers.kakao.com/terms/ko/site-terms) — 사전 승낙 없는 정보 복제·변경 등의 제한. 개별 수신기 허락은 확인 못 함.
- **K4:** [Daum 검색 이해하기](https://developers.kakao.com/docs/ko/daum-search/common) — 검색 대상 6종·정책.
- **G1:** [Custom Search JSON API 개요](https://developers.google.com/custom-search/v1/overview).
- **G2:** [cse.list 명세](https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list) — 100결과 제한.
- **G3:** [Search 응답 명세](https://developers.google.com/custom-search/v1/reference/rest/v1/Search) — `totalResults`는 추정치; 공식 명세 직접 열람.
- **M1:** [Bing Search APIs 종료 공지](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement) — Grounding with Bing Search는 LLM 응답용 이전 대상으로 소개되며 신규 공고 원장 API로 간주하지 않음.
- **B1:** [Brave Search API 상품·가격·FAQ](https://brave.com/search/api/).
- **B2:** [Brave Web Search 문서](https://api-dashboard.search.brave.com/documentation/services/web-search).
- **B3:** [Brave API 약관](https://api-dashboard.search.brave.com/terms-of-service) — 기본 저장·파생물 제한. B1의 별도 저장권 플랜 안내가 모든 플랜의 허용을 뜻하지 않음.
- **B4:** [Brave 인증 안내](https://api-dashboard.search.brave.com/documentation/guides/authentication).
- **R1:** [인크루트 RSS 공식 안내](https://people.incruit.com/rss/rss.asp) — 도움말 HTML만 열람; RSS 항목 요청 안 함.
- **R2:** [인크루트 개인회원 이용약관](https://help.incruit.com/docs/terms.asp) — 제19조④. 과거 2005·2009 약관이나 기업회원 약관을 개인 조건으로 대체하지 않음.
- **R3:** [잡코리아 RSS 종료 공식 공지](https://www.jobkorea.co.kr/help/notice/view?no=13169).
- **R4:** [사람인 공식 도움말](https://www2.saramin.co.kr/zf_user/help/help-word/main) — 공식 도메인 RSS 검색의 확인 범위; 현행 피드 확인 못 함.
- **R5:** [잡알리오 공식 도메인](https://www.jobalio.go.kr/) — `site:jobalio.go.kr RSS` 검색; 확인 못 함. 홈페이지 공고 목록은 열람 안 함.
- **R6:** [나라일터 공식 도메인](https://www.gojobs.go.kr/) — `site:gojobs.go.kr RSS` 검색; 현행 RSS 확인 못 함. 검색에 노출된 공고 요약은 증거 제외.
- **R7:** [고용24 용어사전](https://m.work24.go.kr/ua/common/selectDictionaryList.do) — RSS 정의만 확인; 공식 `work24.go.kr`, `work.go.kr` RSS 검색에서 채용 전용 현행 경로 확인 못 함.
- **R8:** [고용노동부 RSS 안내](https://www.moel.go.kr/site/rss/rssList.do).
- **S1:** [schema.org JobPosting](https://schema.org/JobPosting).
- **S2:** [Google 채용 구조화 데이터 안내](https://developers.google.com/search/docs/appearance/structured-data/job-posting).
- **S3:** [RFC 9309 §1](https://www.rfc-editor.org/rfc/rfc9309.html#section-1) — robots와 접근 허가의 구분.
- **S4:** [사람인 개인회원 이용약관](https://www.saramin.co.kr/zf_user/help/terms-of-service) — 제19조④.
- **S5:** [잡코리아 robots.txt](https://www.jobkorea.co.kr/robots.txt) — sitemap 선언까지만 확인; 특정 사용자 에이전트로 우회 시도 안 함.
- **S6:** [사람인 robots.txt](https://www.saramin.co.kr/robots.txt) — 도구 열람 실패, 허용/차단 판정 안 함.
- **S7:** [인크루트 robots.txt](https://www.incruit.com/robots.txt) — 도구 열람 실패, 허용/차단 판정 안 함.
- **P1:** 기존 내부 근거: [외부 API 검증](03-mvp-external-fact-check.md), [공공·RSS 경로](../ideation/2026-10-18-job-data-sources/02-public-channels.md), [메일·직접 입력 C1~C7](../ideation/2026-10-18-job-data-sources/03-product-reframe.md), [레드팀](../ideation/2026-10-18-job-data-sources/04-red-team.md). 기존 외부 확인일은 해당 문서에 따르며 이번에 재검증했다고 표시하지 않음.

## 검증 기록·남은 문제

- 변경 파일: 이 문서 하나. 기존 작업 중 파일은 수정하지 않았고 git commit·push를 하지 않았다. 기능 코드가 없어 TDD 대상은 없다.
- `make check` 실행: **종료 코드 2, 실패**. 첫 단계 `docker compose up -d --wait db`에서 `Cannot connect to the Docker daemon at unix:///Users/juhoseok/.docker/run/docker.sock`로 중단했다. 백엔드·웹 검사는 실행되지 않았으며 통과로 보고하지 않는다.
- 문서 정적 검사: **종료 코드 0, 통과**. 첫 5줄 요약, 표 2개/19행의 열수 일치, 출처 ID 35개, 로컬 링크 존재 및 미확인·검증 실패 표기를 확인했다. `git diff --check -- docs/research/06-job-intake-equivalents.md`도 종료 0이다. 외부 링크가 모두 작동한다는 검사는 아니다.
- 조사 도중 `python` 명령이 없어 종료 127; `python3`로 공식 도움말 HTML을 재확인해 종료 0. KISA RSS 도움말은 web 열람 실패·Python 인증서 검증 실패로 새 공급 후보에 포함하지 않았다. 네이버의 잘못 추정한 약관 경로·일부 문서 URL도 열람 실패 후 공식 검색/문서 링크로 정정했다.
- 남은 문제: 개인 실발급, 인크루트 RSS 실응답·권리·누락 창, Brave 저장권 조건, NCP 한도 불일치 및 포털 JSON-LD 현존은 확인 못 함이다. Docker를 켠 환경에서 `make check` 재실행이 필요하다.
