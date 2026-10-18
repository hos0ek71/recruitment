"""행정 시도 코드 → 고용24 근무지역 코드.

출처: W3 목록 명세의 '근무지역코드 보기' 공식 XLS(2026-10-17 확인):
https://openapi.work.go.kr/opi/opi/common/useApi/apiCdList.do?cdGbn=region
공식 코드표에 29000/46000이 없어 광주·전남은 '전남광주' 12000으로 넓게
수집한다. 정확한 지역 거르기는 2단계 REGION_OUT 필터가 맡는다.
세종은 공식 표의 36110, 강원·전북은 변경된 51000/52000을 사용한다.
"""

REGION_CODES: dict[str, str] = {
    "11": "11000",  # 서울
    "26": "26000",  # 부산
    "27": "27000",  # 대구
    "28": "28000",  # 인천
    "29": "12000",  # 광주 (전남광주)
    "30": "30000",  # 대전
    "31": "31000",  # 울산
    "36": "36110",  # 세종
    "41": "41000",  # 경기
    "43": "43000",  # 충북
    "44": "44000",  # 충남
    "46": "12000",  # 전남 (전남광주)
    "47": "47000",  # 경북
    "48": "48000",  # 경남
    "50": "50000",  # 제주
    "51": "51000",  # 강원
    "52": "52000",  # 전북
}


def region_code(administrative_code: str) -> str:
    """알 수 없는 지역은 무조건 전체 조회로 바꾸지 않고 호출자에게 알린다."""
    try:
        return REGION_CODES[administrative_code]
    except KeyError:
        raise ValueError(f"Unknown administrative region code: {administrative_code}") from None
