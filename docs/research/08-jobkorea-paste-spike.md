# 잡코리아 검색 결과 붙여넣기 파서 스파이크

1. 제공된 1페이지 텍스트만으로 전체 109건, 페이지 크기 40, 본 목록 40건을 추출했다.
2. 스마트픽 광고 3건과 파견대행 1건은 본 목록에서 분리했고, 조건 7개와 공고별 표시 필드를 보존했다.
3. 체크리스트의 페이지 번호 1을 주면 “69건 부족, 2·3페이지 미입력”을 계산하며 같은 페이지 재입력은 중복 제거한다.
4. 복사 텍스트에는 활성 페이지·공고 URL·ID가 없어 페이지 자동 확정과 실제 고유 공고 수·완전성 보장은 불가능하다.
5. 결론: 사용자 수동 입력 체크리스트의 보조 검증으로는 가능하며, 안정적인 정렬·입력 검토·보수적인 완료 표시가 필요하다.

작성일: 2026-10-19. **제품 코드가 아닌 오프라인 실험**이다. 외부 사실을 새로 조사하지 않았으며 잡코리아에 어떤 요청도 보내지 않았다. 표준 라이브러리만 사용하고 의존성·backend/·web/·샘플은 변경하지 않았다. 기존 탐색 배경은 [수신 경로 조사](06-job-intake-equivalents.md), 모집 단위 처리 원칙은 [설계 검토 0-1절](../mvp-design-review.md)의 사용자 승인 결정을 참고했다.

## 범위와 재현

- 입력: `research/spikes/jobkorea-paste/samples/page1-seoul-newgrad.txt` 한 개. 실제 2·3페이지나 다른 브라우저의 복사 결과는 없다.
- 구현: `research/spikes/jobkorea-paste/jobkorea_paste.py`.
- 테스트: `research/spikes/jobkorea-paste/test_jobkorea_paste.py`.
- 상세검색 URL 생성·사이트 조작·상세 공고 수집·필터 탈락 판정·AI 평가는 이번 범위가 아니다.
- 전체 복사 텍스트에는 계정 영역이 있을 수 있으므로 파서 출력에 전체 페이지 텍스트를 싣지 않는다. 테스트는 기존 샘플을 참조하고 변형은 메모리에서만 만든다.

```sh
python3 -m unittest discover -s research/spikes/jobkorea-paste -v
python3 research/spikes/jobkorea-paste/jobkorea_paste.py \
  research/spikes/jobkorea-paste/samples/page1-seoul-newgrad.txt --page-number 1
```

`parse_page(text, page_number=None)`은 JSON으로 직렬화할 수 있는 dict를 반환한다. `reconcile([page1, page2, ...])`은 동일 조건·페이지 크기·정렬·표시 총수의 입력끼리 합친다. 다른 조건이나 총수가 섞이면 `unverifiable`로 판정한다. CLI는 한 파일의 파싱 결과와 대조 결과를 함께 출력한다.

## 확인된 결과와 출력 계약

| 필드 | 샘플 결과 / 의미 |
| --- | --- |
| `reported_total` | 109. 직무 메뉴의 괄호 숫자가 아닌 `전체 (109건)`에서 읽음 |
| `page_size` | 40. 본 목록 시작의 `40개씩`에서 읽음; 파견 영역의 10개씩은 사용하지 않음 |
| `pages_shown` | `[1, 2, 3]`. 표시된 숫자이며 실제로 입력된 페이지 목록은 아님 |
| `current_page` | 기본 `null`; 호출자가 체크리스트 번호 1을 주면 1 |
| `current_page_evidence` | 활성 표시가 텍스트에 없어 추론 불가 / 호출자 제공 번호라는 근거 |
| `applied_filters` | 서울, 신입, 대학졸업(2,3년), 백엔드개발자, 웹개발자, 소프트웨어개발자, 시스템엔지니어 |
| `sort_order` | 추천순. 샘플에서 확인한 정렬만 인식하며 다른 정렬 형식은 미검증 |
| `items` | 40건. 첫 회사 `㈜위즈브레인`, 제목 `영상관제/IP WALL 시스템 엔지니어 채용` |
| `excluded_blocks` | `smartpick_ad` 3건, `dispatch_agency_section` 1건. 회사·제목·해당 블록 줄과 사유를 남김 |
| `warnings` | 대체 키 위험은 항상 경고. 페이지 번호 미제공·미지원 형식·미파싱 잔여 줄·예상 공고 수 차이도 표시 |

공고 필드: `company`, `title`, `experience`, `education`, `location`, `employment_type`, `tail`, `keywords`, `registration`, `deadline`. 첫 공고는 `신입·경력 / 초대졸↑ / 서울 금천구 / 정규직`이다. `서울 금천구 외`, `정규직 외`를 보존하고 연봉·직급 등 남은 부분은 `tail`에 둔다. 키워드가 없는 한네트 공고는 빈 문자열이다. `6일 전 등록`, `상시채용`, `모레마감`은 원문 문자열을 보존하며 절대 날짜로 환산하지 않는다. 등록일에 연도도 없고 복사 시각도 없으므로 환산하면 근거가 부족하다.

파서는 빈 줄과 줄 앞뒤 공백·탭, CRLF를 정리한 뒤 본 목록 경계와 `등록일 → 마감` 구조로 공고를 나눈다. 광고는 스마트픽 영역과 썸네일 경계, 파견은 별도 영역 경계로 구분한다. **현재 메타데이터 문법은 샘플의 서울·초대졸↑·정규직/계약직에 한정**된다. 다른 학력·지역·고용형태·마감 표현을 처리한다고 주장하지 않는다. 미지원 문법이 있으면 해당 블록을 억지로 변환하지 않고 경고하며 대조 상태를 `unverifiable`로 둔다. 이는 검색 조건으로 공고를 탈락시키는 기능이 아니다.

### 현재 페이지 번호의 근거

샘플의 페이지네이션은 `1 2 3`뿐이다. 글자 스타일·활성 요소가 사라졌으므로 “숫자 중 첫 번째가 현재 페이지”라는 추정은 쓰지 않았다. 코디네이터에게 질의했고 **체크리스트가 ‘페이지 N 주소를 열어 붙여 넣으세요’를 제공하므로 번호를 체크리스트에서 받는다**는 승인을 받았다. 번호가 없으면 부족 건수는 계산하되 누락 페이지는 `null`과 “페이지 식별 불가”로 반환한다. 사용자 오입력까지 검증한 번호는 아니므로 다른 페이지를 붙여 넣고 번호만 바꾸는 오류는 텍스트만으로 막을 수 없다.

### 대조 결과

```json
{
  "status": "incomplete",
  "reported_total": 109,
  "unique_count": 40,
  "missing_count": 69,
  "missing_pages": [2, 3],
  "duplicate_count": 0,
  "identity_conflicts": 0,
  "completeness_verified": false
}
```

위 결과는 `parse_page(text, page_number=1)`을 하나 넣은 경우다. 같은 것을 두 번 넣으면 `unique_count=40`, `missing_count=69`, `missing_pages=[2,3]`, `duplicate_count=40`이다. `missing_count`는 대체 키로 중복을 제거한 수와 표시 총수의 차이이며 실제 누락 공고 수의 확정값은 아니다. 번호 없이 입력하면 `missing_pages=null`이다. 누락 페이지 계산은 `ceil(109/40)=3`을 사용한다. 페이지별 기대 수는 1·2페이지 40, 3페이지 29이지만 실제 2·3페이지 내용은 확인하지 않았다.

상태는 `incomplete`(입력 부족), `unverifiable`(구조·메타데이터·키 충돌 등으로 검증 불가), `count_matches_provisionally`(대체 키 건수 일치)다. 마지막 상태에서도 `completeness_verified=false`다. 합성 40+40+29건 테스트는 이 분기와 합산만 검증하며 실제 109건을 확보했다는 증거가 아니다.

## 되는 것과 안 되는 것

**되는 것:** 이 샘플에서 본 목록과 부가 영역 분리, 표시된 조건·공고 필드·건수 추출, 상대 날짜 원문 보존, 체크리스트 번호를 이용한 미입력 페이지 안내, 재붙여넣기 중복 제거, 불완전 복사·미지원 구조 경고, 총수/조건 변화 감지.

**안 되는 것:** 텍스트만으로 현재 페이지 확정, 실제 ID 기준 중복 판별, 정확한 원문 지원 링크 생성, 모집 단위별 자격 파악, 검색 결과 밖의 시장 전체 포함률 측정, 실제 2·3페이지·모바일·다른 브라우저 레이아웃 보장, 잡코리아 상세검색 파라미터 유효성 검증. 원문 URL이 없으므로 제목으로 URL을 만들어 지원 링크를 제공해서는 안 된다. 통합 공고는 제목이나 목록 정보만으로 제외하지 않고 기존 제품 불변식대로 세부 자격 확인 필요로 다뤄야 한다.

### 대체 고유 키 평가

키는 공백을 정리한 `(회사명, 제목, 등록일 문자열)`이다. 회사명만 쓰면 샘플의 `㈜에이엔에이치코리아` 두 공고를 하나로 잘못 합치지만 제목이 각각 `POWER BI 개발자`, `ERP 재무 컨설턴트 / Dynamics 365`여서 현재 키에서는 두 건 모두 남는다. 이는 이 샘플에서의 구분 성공이며 일반적인 유일성 증명이 아니다.

- 동일 회사·제목·등록일인 별도 공고는 합쳐질 수 있다. 다른 지역 등 필드 차이가 있으면 `identity_conflicts`로 경고하지만 모든 필드까지 같으면 알아낼 수 없다.
- 같은 공고의 제목 수정, 회사 표기 차이, 상대 등록일 변화(`6일 전`→`7일 전`)는 서로 다른 키가 되어 과대 계산될 수 있다.
- 등록일을 빼면 수정·시간 경과에는 덜 민감해지지만 재게시·동일 제목 공고의 충돌 위험이 커진다. 현재 샘플 하나로 어느 쪽의 오차가 작은지 측정할 수 없다.
- 충돌 때문에 빠진 건수와 중복 때문에 부풀려진 건수가 상쇄되면 총수 109와 일치해도 누락이 있을 수 있다. 통계적 충돌 확률을 계산할 근거는 없다.

## 취약점과 제품화 권고

| 취약점 | 영향 | 권고 |
| --- | --- | --- |
| 화면 개편·AD/파견 구조 변경 | 경계가 바뀌거나 본 목록에 섞일 수 있음 | 파서 버전과 경고 보존, 표시 총수·페이지별 건수 대조, 미파싱 블록 사용자 검토 |
| 복사 범위 차이 | 헤더·마지막 공고·페이지네이션 누락 | 전체 선택 안내, 40/40/29건 기대값 확인, 불완전 입력은 완료로 표시하지 않기 |
| 브라우저별 줄바꿈 | 제목·메타데이터가 분리되거나 합쳐질 수 있음 | 현재는 CRLF·공백 변형만 검증. 실제 브라우저별 추가 표본 확보 후 문법 확대 |
| 추천순의 페이지 간 변동 | 중복과 누락이 생길 수 있음. 실제 변동은 이번 실험에서 미측정 | **등록일순 권장**. 해당 화면 복사 형식·URL 값은 별도 검증. 같은 세션에서 연속 입력하고 총수·조건·정렬 변화 시 재시작 |
| 등록일순도 실시간 변화 가능 | 새 등록·동일 날짜 정렬·마감으로 페이지 경계가 밀릴 수 있음 | 정렬만으로 스냅샷 보장하지 않기, 복사 시각·세션 기록, 완료 표현은 건수 대조 수준으로 제한 |
| 고유 키 부재 | 잘못된 합치기·과대 계산·가짜 일치 | 대체 키라는 사실 표시, 충돌 검토, 건수 일치를 완전성 인증으로 표현하지 않기 |
| 체크리스트와 실제 페이지 불일치 | 번호만 다르게 주면 동일 페이지를 여러 페이지로 착각 | 입력 미리보기·중복 경고, 페이지별 재입력 관리, 번호의 출처 표시 |
| 목록 정보 부족 | 지원 링크·모집 단위 자격을 알 수 없음 | 사용자가 원문에서 확인, 제목만으로 통합 공고를 제외하지 않기 |

권장 제품 문구는 “표시 총수와 입력 건수가 일치합니다(공고 식별자 없음)”이며 “전체 공고 수집 완료”는 피한다. 페이지 입력을 단순 누적하기보다 체크리스트 항목별로 교체할 수 있게 하고, 원본은 승인된 정책에 따라 최소 범위로 관리하며 계정 영역은 공고 데이터와 분리하는 편이 낫다. 이번 스파이크는 제품 저장 정책이나 이용 조건 허용 여부를 새로 확정하지 않는다.

### 사용자 1회 작업 시간 (추정)

109건·40개씩·3페이지 기준, 조건/정렬 확인 20~40초 + 각 페이지 열기·전체 선택·복사·붙여넣기·건수 확인 15~30초 × 3 + 마지막 대조 10~20초 = **약 75~150초(1분 15초~2분 30초)**. 누락 재입력·느린 로딩·복사 실수 시 3~5분 이상 걸릴 수 있다. 실제 사용자 실험을 하지 않은 추정이며, URL 생성으로 초기 입력 시간이 줄어드는 효과도 측정하지 않았다. 페이지가 많아지면 시간은 거의 페이지 수에 비례할 것으로 추정한다.

## 검증 증거

### 테스트 우선 실패 (구현 파일 작성 전)

명령: `python3 -m unittest discover -s research/spikes/jobkorea-paste -v`, **종료 코드 1**.

```text
test_jobkorea_paste (unittest.loader._FailedTest.test_jobkorea_paste) ... ERROR
ImportError: Failed to import test module: test_jobkorea_paste
  File "/Users/juhoseok/Desktop/recruitment/research/spikes/jobkorea-paste/test_jobkorea_paste.py", line 6, in <module>
    from jobkorea_paste import parse_page, reconcile
ModuleNotFoundError: No module named 'jobkorea_paste'
Ran 1 test in 0.000s
FAILED (errors=1)
```

14개 테스트를 먼저 작성한 뒤 미구현 모듈로 실패를 확인했다. 첫 구현 실행에서는 14개 중 합성 완료 테스트 1개가 실패했다(`'unverifiable' != 'count_matches_provisionally'`, 종료 코드 1). 원인은 실제 40건 샘플을 3페이지라고 파싱해 기대 29건 경고를 만든 뒤 테스트가 29건으로 잘랐기 때문이다. 합성 페이지는 미지정 번호로 파싱 후 합성 체크리스트 번호와 항목을 설정하도록 픽스처를 고쳤다. 실제 데이터의 경고를 무시하도록 구현을 약화하지 않았다. 범위 밖 번호·미지원 메타데이터 테스트 2개를 추가했다.

### 최종 통과

같은 명령, **종료 코드 0**. 16개 테스트 전체 실행 출력:

```text
test_conflicting_totals_and_filters (test_jobkorea_paste.PasteTests.test_conflicting_totals_and_filters) ... ok
test_current_page_not_visible (test_jobkorea_paste.PasteTests.test_current_page_not_visible) ... ok
test_exclusions (test_jobkorea_paste.PasteTests.test_exclusions) ... ok
test_filters (test_jobkorea_paste.PasteTests.test_filters) ... ok
test_key_collision_detected (test_jobkorea_paste.PasteTests.test_key_collision_detected) ... ok
test_known_page_and_duplicate (test_jobkorea_paste.PasteTests.test_known_page_and_duplicate) ... ok
test_missing_structure_never_complete (test_jobkorea_paste.PasteTests.test_missing_structure_never_complete) ... ok
test_newline_and_whitespace_variants (test_jobkorea_paste.PasteTests.test_newline_and_whitespace_variants) ... ok
test_out_of_range_and_short_copy (test_jobkorea_paste.PasteTests.test_out_of_range_and_short_copy) ... ok
test_same_company_different_titles_retained (test_jobkorea_paste.PasteTests.test_same_company_different_titles_retained) ... ok
test_sample_counts_and_first (test_jobkorea_paste.PasteTests.test_sample_counts_and_first) ... ok
test_synthetic_complete_is_only_provisional (test_jobkorea_paste.PasteTests.test_synthetic_complete_is_only_provisional) ... ok
test_truncated_item_warns (test_jobkorea_paste.PasteTests.test_truncated_item_warns) ... ok
test_unknown_metadata_layout_warns (test_jobkorea_paste.PasteTests.test_unknown_metadata_layout_warns) ... ok
test_unknown_page_numbers (test_jobkorea_paste.PasteTests.test_unknown_page_numbers) ... ok
test_variants_and_empty_keywords (test_jobkorea_paste.PasteTests.test_variants_and_empty_keywords) ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.020s

OK
```

### 전체 프로젝트 검사

`make check`도 실행했으나 **종료 코드 2**, Docker 데몬 연결 실패로 DB 준비 단계에서 중단됐다. 백엔드·웹 검사가 통과했다고 보고하지 않는다.

```text
docker compose up -d --wait db
unable to get image 'postgres:17': Cannot connect to the Docker daemon at unix:///Users/juhoseok/.docker/run/docker.sock. Is the docker daemon running?
make: *** [db-up] Error 1
```

## 남은 문제와 다음 할 일

이번 스파이크 수용 테스트는 통과했다. 전체 프로젝트 검사는 Docker 시작 후 코디네이터가 재실행해야 한다. 제품화 전에는 사용자가 직접 복사한 실제 2·3페이지, 등록일순 화면, 다른 브라우저·다른 지역/학력/마감 표현 표본으로 문법을 확장하고, 수동 완료 시간과 대체 키 충돌을 측정해야 한다. 화면 주소를 생성할 조건→URL 매핑과 저장·사용 범위는 별도 검증 대상으로 남는다.
