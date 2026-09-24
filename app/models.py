from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    student_external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    group_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    language: Mapped[str] = mapped_column(String(16), nullable=False, default="cpp")

    code: Mapped[str] = mapped_column(Text, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    code_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    tokens: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tokens_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tokens_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    feedback: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    parser_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_submissions_student_time", "student_external_id", "submitted_at"),
        Index("ix_submissions_task_student", "task_external_id", "student_external_id"),
        Index("ix_submissions_group_time", "group_external_id", "submitted_at"),
        Index("ix_submissions_code_hash", "code_hash"),
        Index("ix_submissions_tokens_hash", "tokens_hash"),
        Index("ix_submissions_status", "status"),
    )


class PlagiarismPair(Base):
    __tablename__ = "plagiarism_pairs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    submission_a_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    submission_b_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )

    metric: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    ngram_size: Mapped[int] = mapped_column(Integer, nullable=False)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "submission_a_id",
            "submission_b_id",
            "metric",
            "ngram_size",
            name="uq_plagiarism_pair",
        ),
        Index("ix_plagiarism_a", "submission_a_id"),
        Index("ix_plagiarism_b", "submission_b_id"),
    )