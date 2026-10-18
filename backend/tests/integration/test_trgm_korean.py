import pytest
from sqlalchemy import text

pytestmark = pytest.mark.db


def test_korean_similarity(db_connection):
    title_score, korean_score = db_connection.execute(
        text("""
        SELECT similarity('서버 운영 엔지니어 신입 채용', '서버운영 엔지니어 신입 모집'),
               similarity('서버운영', '서버관리')
    """)
    ).one()
    print(f"Korean pg_trgm: title={title_score}, Korean-only={korean_score}")
    assert title_score > 0.3
    assert korean_score > 0
