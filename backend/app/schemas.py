from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Materials --------------------------------------------------------------
class MaterialOut(ORMModel):
    id: int
    title: str
    source_type: str
    filename: str | None = None
    status: str
    error: str | None = None
    archived: bool = False
    folder_id: int | None = None
    created_at: datetime


class MaterialTextIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=100_000)


class LibraryFolderCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    parent_id: int | None = None


class LibraryFolderUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: int | None = None


class LibraryFolderOut(ORMModel):
    id: int
    name: str
    parent_id: int | None = None
    created_at: datetime


class MaterialFolderIn(BaseModel):
    folder_id: int | None = None


class ChapterCorrection(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    topic_ids: list[int]


class MaterialCorrectionIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    subject_name: str | None = Field(default=None, min_length=1, max_length=200)
    chapters: list[ChapterCorrection] | None = None


# ---- Concepts ---------------------------------------------------------------
class ConceptOut(ORMModel):
    id: int
    material_id: int
    parent_id: int | None = None
    title: str
    summary: str
    order_index: int
    difficulty: str


# ---- Lessons ----------------------------------------------------------------
class LessonOut(ORMModel):
    id: int
    material_id: int
    concept_id: int
    topic_id: int | None = None
    title: str
    objectives: list[str]
    content: str
    status: str
    language: str = "en"
    grounding: list[dict] = Field(default_factory=list)


class LessonSummary(ORMModel):
    id: int
    concept_id: int
    title: str
    status: str


class RegenerateLessonIn(BaseModel):
    simpler: bool = False


# ---- Quiz -------------------------------------------------------------------
class QuestionPublic(BaseModel):
    id: int
    type: str
    prompt: str
    options: list[str] | None = None
    difficulty: int


class QuizOut(BaseModel):
    lesson_id: int
    questions: list[QuestionPublic]


class AnswerIn(BaseModel):
    question_id: int
    response: str = ""


class QuizSubmitIn(BaseModel):
    answers: list[AnswerIn]


class AnswerCheckIn(BaseModel):
    question_id: int
    response: str = Field(max_length=4000)


class QuestionResult(BaseModel):
    question_id: int
    correct: bool
    correct_answer: str
    explanation: str


class ConceptMasteryOut(BaseModel):
    concept_id: int
    score: float


class QuizResultOut(BaseModel):
    lesson_id: int
    score: float
    results: list[QuestionResult]
    concept_mastery: list[ConceptMasteryOut]


# ---- Sessions ---------------------------------------------------------------
class SessionCreateIn(BaseModel):
    material_id: int


class SessionOut(ORMModel):
    id: int
    material_id: int
    current_concept_id: int | None = None
    status: str
    created_at: datetime


class NextActionOut(BaseModel):
    type: str  # advance | practice | reteach | complete
    message: str
    concept: ConceptOut | None = None
    lesson: LessonOut | None = None
    quiz: QuizOut | None = None


# ---- Curriculum -------------------------------------------------------------
class GroundingRef(BaseModel):
    chunk_id: int
    index: int
    relevance: float | None = None
    content: str
    source_pages: list[int] = Field(default_factory=list)


class TopicOut(ORMModel):
    id: int
    chapter_id: int
    concept_id: int | None = None
    title: str
    summary: str
    difficulty: str
    order_index: int


class TopicDetailOut(TopicOut):
    grounding: list[GroundingRef] = Field(default_factory=list)
    lessons: list[LessonSummary] = Field(default_factory=list)
    source_material_id: int | None = None
    source_title: str | None = None
    source_filename: str | None = None
    source_pages: list[int] = Field(default_factory=list)


class ChapterOut(ORMModel):
    id: int
    subject_id: int
    title: str
    order_index: int
    topics: list[TopicOut] = Field(default_factory=list)


class SubjectOut(ORMModel):
    id: int
    material_id: int | None = None
    name: str
    language: str
    order_index: int
    chapters: list[ChapterOut] = Field(default_factory=list)


class CurriculumOut(BaseModel):
    material_id: int
    subjects: list[SubjectOut] = Field(default_factory=list)


# ---- Auth -------------------------------------------------------------------
def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Invalid email address")
    return value


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            "Use a valid IANA time zone, such as Asia/Dubai."
        ) from exc
    return value


Email = Annotated[str, AfterValidator(_validate_email)]


class SignupIn(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    grade: int | None = Field(default=None, ge=1, le=12)
    language: str = Field(default="en", pattern="^(en|ar)$")
    timezone: str = Field(default="Asia/Dubai", max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return _validate_timezone(value)


class LoginIn(BaseModel):
    email: Email
    password: str = Field(min_length=1)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        return _validate_timezone(value) if value is not None else None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserOut(ORMModel):
    id: int
    email: str
    role: str
    display_name: str
    grade: int | None = None
    language: str
    timezone: str
    is_active: bool
    created_at: datetime


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    grade: int | None = Field(default=None, ge=1, le=12)
    language: str | None = Field(default=None, pattern="^(en|ar)$")
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        return _validate_timezone(value) if value is not None else None


class PasswordResetRequestIn(BaseModel):
    email: Email


class PasswordResetRequestOut(BaseModel):
    detail: str
    reset_token: str | None = None


class PasswordResetConfirmIn(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


# ---- Admin ------------------------------------------------------------------
class AdminUserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, pattern="^(student|admin|teacher|parent)$")
    is_active: bool | None = None
    grade: int | None = Field(default=None, ge=1, le=12)


class UserPage(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class AIUsageOut(ORMModel):
    id: int
    user_id: int | None = None
    provider: str
    model: str
    operation: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None = None
    latency_ms: int
    status: str
    error: str | None = None
    created_at: datetime


class AIUsageSummaryOut(BaseModel):
    calls: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    unpriced_calls: int


class AuditLogOut(ORMModel):
    id: int
    actor_user_id: int | None = None
    action: str
    target_type: str
    target_id: str
    meta: dict
    created_at: datetime


# ---- Spaced repetition ------------------------------------------------------
class ReviewScheduleOut(BaseModel):
    topic_id: int
    topic_title: str
    interval_days: int
    ease: float
    repetitions: int
    lapses: int
    due_at: datetime | None = None
    last_reviewed_at: datetime | None = None
    is_due: bool
    mastery: float
    retention: float


class ReviewQueueOut(BaseModel):
    items: list[ReviewScheduleOut]
    total: int


class ReviewSummaryOut(BaseModel):
    due_count: int
    scheduled_count: int
    reviewed_count: int


class ReviewSubmitIn(BaseModel):
    quality: int = Field(ge=0, le=5)


# ---- Mastery v2 -------------------------------------------------------------
class TopicMasteryOut(BaseModel):
    topic_id: int
    title: str
    concept_id: int | None = None
    mastery: float


class MasteryEventOut(ORMModel):
    id: int
    concept_id: int
    topic_id: int | None = None
    score: float
    delta: float
    is_correct: bool
    source: str
    created_at: datetime


# ---- Socratic tutor ---------------------------------------------------------
class TutorMessageOut(ORMModel):
    id: int
    role: str
    content: str
    grounding: list[dict] = Field(default_factory=list)
    created_at: datetime


class TutorConversationCreateIn(BaseModel):
    topic_id: int | None = None
    title: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, pattern="^(en|ar)$")


class TutorAskIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class TutorConversationOut(ORMModel):
    id: int
    topic_id: int | None = None
    title: str
    language: str
    created_at: datetime
    updated_at: datetime


class TutorConversationSummaryOut(TutorConversationOut):
    topic_title: str = ""
    message_count: int = 0


class TutorConversationDetailOut(TutorConversationOut):
    topic_title: str = ""
    messages: list[TutorMessageOut] = Field(default_factory=list)


class TutorReplyOut(BaseModel):
    user_message: TutorMessageOut
    reply: TutorMessageOut


# ---- Study planner ----------------------------------------------------------
class ExamDateCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    exam_date: date
    subject_id: int | None = None


class ExamDateOut(ORMModel):
    id: int
    subject_id: int | None = None
    title: str
    exam_date: date
    created_at: datetime


class PlanGenerateIn(BaseModel):
    exam_date_id: int
    daily_minutes: int = Field(default=60, ge=15, le=480)
    subject_id: int | None = None


class PlanItemOut(BaseModel):
    id: int
    topic_id: int | None = None
    topic_title: str = ""
    scheduled_for: date | None = None
    estimated_minutes: int
    status: str
    completed_at: datetime | None = None


class PlanItemUpdateIn(BaseModel):
    status: str = Field(pattern="^(pending|done)$")


class PlanOut(ORMModel):
    id: int
    exam_date_id: int | None = None
    status: str
    created_at: datetime


class PlanSummaryOut(PlanOut):
    exam_title: str = ""
    exam_date: date | None = None
    total_items: int = 0
    completed_items: int = 0
    percent_complete: float = 0.0


class PlanDetailOut(PlanSummaryOut):
    items: list[PlanItemOut] = Field(default_factory=list)


# ---- Gamification -----------------------------------------------------------
class StreakOut(BaseModel):
    current: int
    longest: int
    today_count: int
    last_active_date: date | None = None


class AchievementOut(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    unlocked: bool
    unlocked_at: datetime | None = None


class ActivePlanOut(BaseModel):
    id: int
    total_items: int
    completed_items: int
    percent_complete: float


class DashboardOut(BaseModel):
    streak: StreakOut
    topics_total: int
    topics_covered: int
    average_mastery: float
    due_reviews: int
    achievements_unlocked: int
    achievements_total: int
    active_plan: ActivePlanOut | None = None
    study_minutes: int = 0
    score_trend: list[dict] = Field(default_factory=list)
    upcoming_exams: list[dict] = Field(default_factory=list)
    subject_progress: list[dict] = Field(default_factory=list)


class TopicNotesOut(BaseModel):
    topic_id: int
    notes: dict


class TranslationIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    target_language: str = Field(default="ar", pattern="^(ar|en)$")


class TranslationOut(BaseModel):
    translated_text: str


class StudyTimeIn(BaseModel):
    duration_seconds: int = Field(ge=1, le=3600)


class StudyTodayItem(BaseModel):
    topic_id: int
    title: str
    reason: str
    priority: int
    due_at: datetime | None = None


class StudyTodayOut(BaseModel):
    items: list[StudyTodayItem]


class PracticeExamCreateIn(BaseModel):
    duration_minutes: int = Field(default=30, ge=1, le=240)


class PracticeExamAnswerIn(BaseModel):
    answers: dict[int, str] = Field(default_factory=dict)


class PracticeExamOut(BaseModel):
    id: int
    chapter_id: int
    duration_seconds: int
    started_at: datetime
    submitted_at: datetime | None
    score: float | None
    answers: dict[int, str] = Field(default_factory=dict)
    questions: list[QuestionPublic] = Field(default_factory=list)
    review: list[QuestionResult] = Field(default_factory=list)


class AcademicYearRolloverIn(BaseModel):
    label: str = Field(min_length=1, max_length=50)


class AcademicYearOut(BaseModel):
    id: int
    label: str
    is_active: bool
    archived_subjects: int = 0


# ---- Notifications ----------------------------------------------------------
class NotificationOut(ORMModel):
    id: int
    type: str
    title: str
    body: str
    read_at: datetime | None = None
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    unread: int


class MarkAllReadOut(BaseModel):
    updated: int
