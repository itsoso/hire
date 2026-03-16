from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Developer(Base):
    __tablename__ = "developers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    github_username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    github_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    scholar_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    social_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    profile_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_tags: Mapped[list] = mapped_column(JSONB, default=list)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    network: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query_text: Mapped[str] = mapped_column(Text)
    parsed_intent: Mapped[dict] = mapped_column(JSONB, default=dict)
    results: Mapped[list] = mapped_column(JSONB, default=list)
    employer_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
