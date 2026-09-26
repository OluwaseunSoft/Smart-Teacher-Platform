from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), default="Student")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User | None"] = relationship(back_populates="student")
    materials: Mapped[list["Material"]] = relationship(back_populates="student")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(20), default="text")
    filename: Mapped[str | None] = mapped_column(String(300), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    student: Mapped[Student] = relationship(back_populates="materials")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="material", cascade="all, delete-orphan"
    )
    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="material", cascade="all, delete-orphan"
    )
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="material", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    material: Mapped[Material] = relationship(back_populates="chunks")


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("concepts.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[str] = mapped_column(String(20), default="core")

    material: Mapped[Material] = relationship(back_populates="concepts")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    content: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(5), default="en")
    grounding: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    simpler: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    concept: Mapped[Concept] = relationship(back_populates="lessons")
    topic: Mapped["Topic | None"] = relationship(back_populates="lessons")
    questions: Mapped[list["Question"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    type: Mapped[str] = mapped_column(String(20), default="mcq")
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=2)

    lesson: Mapped[Lesson] = relationship(back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    response: Mapped[str] = mapped_column(Text, default="")
    is_correct: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Mastery(Base):
    __tablename__ = "mastery"
    __table_args__ = (UniqueConstraint("student_id", "concept_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


class MasteryEvent(Base):
    """Immutable history of mastery changes (one row per graded attempt/review)."""

    __tablename__ = "mastery_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"), nullable=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.0)
    delta: Mapped[float] = mapped_column(Float, default=0.0)
    is_correct: Mapped[bool] = mapped_column(default=False)
    source: Mapped[str] = mapped_column(String(20), default="quiz")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    current_concept_id: Mapped[int | None] = mapped_column(
        ForeignKey("concepts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


# ---- Accounts, roles, sessions ---------------------------------------------
ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"  # Stretch
ROLE_PARENT = "parent"  # Stretch
ROLES = (ROLE_STUDENT, ROLE_ADMIN, ROLE_TEACHER, ROLE_PARENT)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=ROLE_STUDENT)
    display_name: Mapped[str] = mapped_column(String(120), default="")
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        cascade="all, delete-orphan"
    )
    student: Mapped["Student | None"] = relationship(back_populates="user")


class UserSession(Base):
    """A revocable server-side session backing an issued JWT (keyed by `jti`)."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_type: Mapped[str] = mapped_column(String(20), default="access")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_longest: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)


# ---- Multi-tenancy / academic calendar (Advanced) --------------------------
class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(50))
    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ---- Curriculum hierarchy: Subject -> Chapter -> Topic ---------------------
class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    material_id: Mapped[int | None] = mapped_column(
        ForeignKey("materials.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(5), default="en")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    material: Mapped["Material | None"] = relationship(back_populates="subjects")
    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="Chapter.order_index",
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    subject: Mapped[Subject] = relationship(back_populates="chapters")
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Topic.order_index",
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id"), index=True)
    concept_id: Mapped[int | None] = mapped_column(
        ForeignKey("concepts.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(20), default="core")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    chapter: Mapped[Chapter] = relationship(back_populates="topics")
    concept: Mapped["Concept | None"] = relationship()
    chunk_links: Mapped[list["TopicChunk"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    lessons: Mapped[list["Lesson"]] = relationship(back_populates="topic")


class TopicChunk(Base):
    """Grounding link between a topic and the source chunks that support it."""

    __tablename__ = "topic_chunks"
    __table_args__ = (UniqueConstraint("topic_id", "chunk_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), index=True)
    relevance: Mapped[float] = mapped_column(Float, default=0.0)

    topic: Mapped[Topic] = relationship(back_populates="chunk_links")
    chunk: Mapped["Chunk"] = relationship()


# ---- Spaced repetition ------------------------------------------------------
class ReviewSchedule(Base):
    __tablename__ = "review_schedules"
    __table_args__ = (UniqueConstraint("user_id", "topic_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    ease: Mapped[float] = mapped_column(Float, default=2.5)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )


# ---- Socratic tutor ---------------------------------------------------------
class TutorConversation(Base):
    __tablename__ = "tutor_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), default="")
    language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    topic: Mapped["Topic | None"] = relationship()
    messages: Mapped[list["TutorMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="TutorMessage.id",
    )


class TutorMessage(Base):
    __tablename__ = "tutor_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("tutor_conversations.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    grounding: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped[TutorConversation] = relationship(back_populates="messages")


# ---- Study planner ----------------------------------------------------------
class ExamDate(Base):
    __tablename__ = "exam_dates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    exam_date: Mapped[datetime] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    exam_date_id: Mapped[int | None] = mapped_column(
        ForeignKey("exam_dates.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("study_plans.id"), index=True)
    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id"), nullable=True
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# ---- Gamification -----------------------------------------------------------
class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(64), default="")
    criteria: Mapped[dict] = mapped_column(JSON, default=dict)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Streak(Base):
    __tablename__ = "streaks"
    __table_args__ = (UniqueConstraint("user_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(Date)
    activity_count: Mapped[int] = mapped_column(Integer, default=0)


# ---- Notifications ----------------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40), default="info")
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ---- Observability ----------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(80), default="")
    target_id: Mapped[str] = mapped_column(String(80), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    operation: Mapped[str] = mapped_column(String(80), default="")
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ok")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
