from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profile"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Criteria(Base):
    __tablename__ = "criteria"
    __table_args__ = (
        UniqueConstraint("profile_id", "version"),
        CheckConstraint("status IN ('draft', 'approved', 'superseded')", name="ck_criteria_status"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("profile.id"))
    version: Mapped[int] = mapped_column()
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    regions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    hard_filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    recommend_threshold: Mapped[int] = mapped_column(server_default=text("'60'"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'draft'"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExploreKeyword(Base):
    __tablename__ = "explore_keyword"
    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed', 'approved', 'rejected')", name="ck_explore_keyword_status"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    criteria_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("criteria.id"))
    keyword: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'proposed'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CollectionRun(Base):
    __tablename__ = "collection_run"
    __table_args__ = (
        CheckConstraint("trigger IN ('schedule', 'manual', 'ai')", name="ck_run_trigger"),
        CheckConstraint(
            "status IN ('running', 'succeeded', 'partial', 'failed')", name="ck_run_status"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    criteria_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("criteria.id"))
    trigger: Mapped[str] = mapped_column(Text)
    enabled_sources: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    status: Mapped[str] = mapped_column(Text, server_default=text("'running'"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    api_calls_used: Mapped[int] = mapped_column(server_default=text("'0'"))


class CollectionQuery(Base):
    __tablename__ = "collection_query"
    __table_args__ = (
        CheckConstraint("source IN ('saramin', 'work24')", name="ck_query_source"),
        CheckConstraint(
            "status IN ('pending', 'completed', 'partial', 'deferred', 'error')",
            name="ck_query_status",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("collection_run.id"))
    source: Mapped[str] = mapped_column(Text)
    keyword: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(Text)
    published_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
    pages_fetched: Mapped[int] = mapped_column(server_default=text("'0'"))
    total_reported: Mapped[int | None] = mapped_column()
    items_received: Mapped[int] = mapped_column(server_default=text("'0'"))
    error: Mapped[str | None] = mapped_column(Text)


class RawPosting(Base):
    __tablename__ = "raw_posting"
    __table_args__ = (
        UniqueConstraint("source", "source_posting_id"),
        Index("ix_raw_posting_run_id", "run_id"),
        CheckConstraint("source IN ('saramin', 'work24')", name="ck_raw_source"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source: Mapped[str] = mapped_column(Text)
    source_posting_id: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("collection_run.id"))


class QueryHit(Base):
    __tablename__ = "query_hit"
    collection_query_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("collection_query.id"), primary_key=True
    )
    raw_posting_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("raw_posting.id"), primary_key=True
    )


class QueryWatermark(Base):
    __tablename__ = "query_watermark"
    __table_args__ = (
        CheckConstraint("source IN ('saramin', 'work24')", name="ck_watermark_source"),
    )
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    keyword: Mapped[str] = mapped_column(Text, primary_key=True)
    region: Mapped[str] = mapped_column(Text, primary_key=True)
    last_completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ApiUsage(Base):
    __tablename__ = "api_usage"
    __table_args__ = (CheckConstraint("source IN ('saramin', 'work24')", name="ck_usage_source"),)
    usage_date: Mapped[date] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    calls: Mapped[int] = mapped_column(server_default=text("'0'"))


class Posting(Base):
    __tablename__ = "posting"
    __table_args__ = (
        Index("ix_posting_company_name_norm", "company_name_norm"),
        Index("ix_posting_first_seen_at", "first_seen_at"),
        Index(
            "ix_posting_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    company_name: Mapped[str | None] = mapped_column(Text)
    company_name_norm: Mapped[str | None] = mapped_column(Text)
    company_biz_no: Mapped[str | None] = mapped_column(Text)
    employee_count: Mapped[int | None] = mapped_column()
    title: Mapped[str] = mapped_column(Text)
    location_text: Mapped[str | None] = mapped_column(Text)
    region_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    employment_type: Mapped[str | None] = mapped_column(Text)
    career_type: Mapped[str | None] = mapped_column(Text)
    career_min: Mapped[int | None] = mapped_column()
    career_max: Mapped[int | None] = mapped_column()
    education_min: Mapped[str | None] = mapped_column(Text)
    salary_text: Mapped[str | None] = mapped_column(Text)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_type: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    job_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    provider: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(server_default=text("'true'"))


class PostingSource(Base):
    __tablename__ = "posting_source"
    __table_args__ = (CheckConstraint("source IN ('saramin', 'work24')", name="ck_posting_source"),)
    posting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posting.id"), primary_key=True)
    raw_posting_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("raw_posting.id"), primary_key=True
    )
    source: Mapped[str] = mapped_column(Text)


class FilterResult(Base):
    __tablename__ = "filter_result"
    posting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posting.id"), primary_key=True)
    criteria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("criteria.id"), primary_key=True
    )
    passed: Mapped[bool] = mapped_column()
    reason_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    needs_check_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    rules_version: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Evaluation(Base):
    __tablename__ = "evaluation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')", name="ck_evaluation_status"
        ),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_evaluation_score"),
    )
    posting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posting.id"), primary_key=True)
    criteria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("criteria.id"), primary_key=True
    )
    status: Mapped[str] = mapped_column(Text, server_default=text("'pending'"))
    score: Mapped[int | None] = mapped_column()
    match_reasons: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    missing: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    needs_check: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]")
    )
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(server_default=text("'0'"))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserMark(Base):
    __tablename__ = "user_mark"
    __table_args__ = (
        CheckConstraint("mark IN ('interested', 'applied', 'excluded')", name="ck_user_mark"),
    )
    posting_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("posting.id"), primary_key=True)
    mark: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExcludedCompany(Base):
    __tablename__ = "excluded_company"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('referral', 'applied', 'other')", name="ck_excluded_company_reason"
        ),
    )
    company_name_norm: Mapped[str] = mapped_column(Text, primary_key=True)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ToolCallLog(Base):
    __tablename__ = "tool_call_log"
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    run_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("collection_run.id"))
    tool: Mapped[str] = mapped_column(Text)
    input: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    output: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
