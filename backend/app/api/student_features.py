from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user, owned_topic
from app.db import get_db
from app.llm import LLMError, get_llm
from app.models import (
    AcademicYear,
    Attempt,
    Chapter,
    Lesson,
    Material,
    PracticeExam,
    Question,
    Student,
    StudyTimeEvent,
    Subject,
    Topic,
    TopicNotes,
    User,
)
from app.schemas import (
    AcademicYearOut,
    AcademicYearRolloverIn,
    PracticeExamAnswerIn,
    PracticeExamCreateIn,
    PracticeExamOut,
    QuestionPublic,
    QuestionResult,
    StudyTimeIn,
    StudyTodayItem,
    StudyTodayOut,
    TopicNotesOut,
    TranslationIn,
    TranslationOut,
)
from app.services.ai_usage import track_ai
from app.services import adaptive, assessment, repetition

router = APIRouter(prefix="/api", tags=["student features"])


@router.get("/topics/{topic_id}/notes", response_model=TopicNotesOut)
def get_topic_notes(
    topic_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> TopicNotesOut:
    topic = owned_topic(db, topic_id, student)
    record = db.scalar(select(TopicNotes).where(TopicNotes.topic_id == topic.id))
    if record is None:
        source_pages = sorted(
            {
                page
                for link in topic.chunk_links
                if link.chunk is not None
                for page in (link.chunk.source_pages or [])
            }
        )
        excerpt = " ".join(
            link.chunk.content
            for link in topic.chunk_links
            if link.chunk is not None
        )
        key_points = [
            {
                "text": point.strip(),
                "source_pages": source_pages,
            }
            for point in excerpt.split(".")
            if point.strip()
        ][:8]
        flashcards = [
            {"front": topic.title, "back": topic.summary, "source_pages": source_pages}
        ] if topic.summary else []
        record = TopicNotes(
            topic_id=topic.id,
            notes={
                "summary": {
                    "text": topic.summary or excerpt[:1200],
                    "source_pages": source_pages,
                },
                "key_points": key_points,
                "flashcards": flashcards,
            },
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    return TopicNotesOut(topic_id=topic.id, notes=record.notes)


@router.post("/translate", response_model=TranslationOut)
def translate_text(
    payload: TranslationIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TranslationOut:
    provider = get_llm()
    language = "Arabic" if payload.target_language == "ar" else "English"
    system = (
        f"Translate the supplied study note into {language}. "
        + (
            "Preserve every English technical term verbatim in square brackets "
            "immediately after its Arabic translation. "
            if payload.target_language == "ar"
            else "Keep technical terms accurate and natural in English. "
        )
        + "Return only the translated note."
    )
    try:
        with track_ai(db, provider, "notes.translate", user_id=user.id):
            result = provider.complete(
                [{"role": "user", "content": payload.text}],
                system=system,
                temperature=0.1,
                max_tokens=3000,
            )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return TranslationOut(translated_text=result.strip())


@router.post("/study-time", status_code=204)
def record_study_time(
    payload: StudyTimeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.add(StudyTimeEvent(user_id=user.id, duration_seconds=payload.duration_seconds))
    db.commit()


@router.get("/study-today", response_model=StudyTodayOut)
def study_today(
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyTodayOut:
    due = repetition.due_reviews(db, user.id, limit=100)
    mastery = adaptive.topic_mastery_map(db, student.id)
    topic_ids = {schedule.topic_id for schedule in due}
    wrong_topic_ids = set(
        db.scalars(
            select(Topic.id)
            .join(Question, Question.concept_id == Topic.concept_id)
            .join(Attempt, Attempt.question_id == Question.id)
            .where(Attempt.student_id == student.id, Attempt.is_correct.is_(False))
            .distinct()
        )
    )
    topic_ids.update(wrong_topic_ids)
    schedules = {schedule.topic_id: schedule for schedule in due}
    topics = list(db.scalars(select(Topic).where(Topic.id.in_(topic_ids)))) if topic_ids else []
    items = [
        StudyTodayItem(
            topic_id=topic.id,
            title=topic.title,
            reason=(
                "Incorrect answer"
                if topic.id in wrong_topic_ids
                else "Review due"
            ),
            priority=(
                0 if topic.id in wrong_topic_ids
                else 10 + round(mastery.get(topic.id, 0.0) * 100)
            ),
            due_at=schedules[topic.id].due_at if topic.id in schedules else None,
        )
        for topic in topics
    ]
    items.sort(key=lambda item: (item.priority, item.due_at or datetime.min))
    return StudyTodayOut(items=items)


@router.post("/academic-years/rollover", response_model=AcademicYearOut)
def rollover_academic_year(
    payload: AcademicYearRolloverIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AcademicYearOut:
    old_year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.user_id == user.id, AcademicYear.is_active.is_(True)
        )
    )
    if old_year is None:
        old_year = AcademicYear(
            label="Previous academic year", user_id=user.id, is_active=False
        )
        db.add(old_year)
        db.flush()
    owned_subjects = select(Subject).outerjoin(
        Material, Material.id == Subject.material_id
    ).where(
        or_(Subject.user_id == user.id, Material.student_id == student.id),
        Subject.archived.is_(False),
    )
    for subject in db.scalars(owned_subjects):
        subject.archived = True
        subject.academic_year_id = old_year.id
    old_year.is_active = False
    year = AcademicYear(label=payload.label, user_id=user.id, is_active=True)
    db.add(year)
    db.commit()
    db.refresh(year)
    return AcademicYearOut(id=year.id, label=year.label, is_active=True)


@router.get("/academic-years", response_model=list[AcademicYearOut])
def list_academic_years(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AcademicYearOut]:
    years = list(db.scalars(select(AcademicYear).where(AcademicYear.user_id == user.id)))
    return [
        AcademicYearOut(
            id=year.id,
            label=year.label,
            is_active=year.is_active,
            archived_subjects=db.scalar(
                select(func.count(Subject.id)).where(
                    Subject.academic_year_id == year.id
                )
            ) or 0,
        )
        for year in years
    ]


@router.get("/academic-years/{year_id}/search")
def search_archived_year(
    year_id: int,
    q: str = Query(min_length=1, max_length=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.id == year_id, AcademicYear.user_id == user.id
        )
    )
    if year is None:
        raise HTTPException(status_code=404, detail="Academic year not found")
    pattern = f"%{q.strip().lower()}%"
    rows = db.execute(
        select(Subject.name, Chapter.title, Topic.id, Topic.title)
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Topic, Topic.chapter_id == Chapter.id)
        .where(
            Subject.academic_year_id == year.id,
            or_(
                func.lower(Subject.name).like(pattern),
                func.lower(Chapter.title).like(pattern),
                func.lower(Topic.title).like(pattern),
            ),
        )
    ).all()
    return [
        {"subject": subject, "chapter": chapter, "topic_id": topic_id, "topic": topic}
        for subject, chapter, topic_id, topic in rows
    ]


@router.post(
    "/chapters/{chapter_id}/practice-exams",
    response_model=PracticeExamOut,
    status_code=201,
)
def create_practice_exam(
    chapter_id: int,
    payload: PracticeExamCreateIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeExamOut:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    material = db.get(Material, chapter.subject.material_id)
    if material is None or material.student_id != student.id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    question_ids = list(
        db.scalars(
            select(Question.id)
            .join(Lesson, Lesson.id == Question.lesson_id)
            .join(Topic, Topic.id == Lesson.topic_id)
            .where(Topic.chapter_id == chapter.id)
            .order_by(Question.id)
        )
    )
    if not question_ids:
        raise HTTPException(status_code=409, detail="Chapter has no assessment questions")
    exam = PracticeExam(
        user_id=user.id,
        chapter_id=chapter.id,
        question_ids=question_ids,
        duration_seconds=payload.duration_minutes * 60,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return _exam_out(db, exam, include_review=False)


@router.get("/practice-exams/{exam_id}", response_model=PracticeExamOut)
def get_practice_exam(
    exam_id: int,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeExamOut:
    exam = _owned_exam(db, exam_id, user.id)
    if exam.submitted_at is None and _expired(exam):
        saved = {int(key): value for key, value in exam.answers.items()}
        _submit_exam(db, exam, saved, student=student)
    return _exam_out(db, exam, include_review=exam.submitted_at is not None)


@router.patch("/practice-exams/{exam_id}/answers", status_code=204)
def save_practice_exam_answers(
    exam_id: int,
    payload: PracticeExamAnswerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    exam = _owned_exam(db, exam_id, user.id)
    if exam.submitted_at is not None or _expired(exam):
        raise HTTPException(status_code=409, detail="Practice exam is no longer in progress")
    if not set(payload.answers).issubset(set(exam.question_ids)):
        raise HTTPException(status_code=422, detail="Answer contains a question outside this exam")
    exam.answers = {str(key): value for key, value in payload.answers.items()}
    db.commit()


@router.post("/practice-exams/{exam_id}/submit", response_model=PracticeExamOut)
def submit_practice_exam(
    exam_id: int,
    payload: PracticeExamAnswerIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PracticeExamOut:
    exam = _owned_exam(db, exam_id, user.id)
    if exam.submitted_at is None:
        if not set(payload.answers).issubset(set(exam.question_ids)):
            raise HTTPException(
                status_code=422,
                detail="Answer contains a question outside this exam",
            )
        saved = {int(key): value for key, value in exam.answers.items()}
        saved.update(payload.answers)
        _submit_exam(db, exam, saved, student=student)
    return _exam_out(db, exam, include_review=True)


def _owned_exam(db: Session, exam_id: int, user_id: int) -> PracticeExam:
    exam = db.get(PracticeExam, exam_id)
    if exam is None or exam.user_id != user_id:
        raise HTTPException(status_code=404, detail="Practice exam not found")
    return exam


def _expired(exam: PracticeExam) -> bool:
    started = exam.started_at.replace(tzinfo=timezone.utc) if exam.started_at.tzinfo is None else exam.started_at
    return datetime.now(timezone.utc) >= started + timedelta(seconds=exam.duration_seconds)


def _submit_exam(
    db: Session,
    exam: PracticeExam,
    answers: dict[int, str],
    student: Student | None = None,
) -> None:
    questions = list(db.scalars(select(Question).where(Question.id.in_(exam.question_ids))))
    questions.sort(key=lambda question: exam.question_ids.index(question.id))
    results = []
    correct_count = 0
    graded: list[tuple[Question, str, bool, str]] = []
    for question in questions:
        response = answers.get(question.id, "")
        try:
            correct, explanation = assessment.grade_answer(question, response, db=db, user_id=exam.user_id)
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        graded.append((question, response, correct, explanation))

    for question, response, correct, explanation in graded:
        correct_count += int(correct)
        results.append(
            QuestionResult(
                question_id=question.id,
                correct=correct,
                correct_answer=question.answer,
                explanation=explanation,
            ).model_dump()
        )
        if student is not None:
            db.add(Attempt(student_id=student.id, question_id=question.id, response=response, is_correct=correct))
            adaptive.update_mastery(
                db,
                student.id,
                question.concept_id,
                correct,
                question.difficulty,
                source="practice_exam",
                commit=False,
            )
    exam.answers = {str(key): value for key, value in answers.items()}
    exam.review = results
    exam.score = correct_count / len(questions) if questions else 0.0
    exam.submitted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(exam)


def _exam_out(db: Session, exam: PracticeExam, *, include_review: bool) -> PracticeExamOut:
    questions = list(db.scalars(select(Question).where(Question.id.in_(exam.question_ids))))
    questions.sort(key=lambda question: exam.question_ids.index(question.id))
    return PracticeExamOut(
        id=exam.id,
        chapter_id=exam.chapter_id,
        duration_seconds=exam.duration_seconds,
        started_at=exam.started_at,
        submitted_at=exam.submitted_at,
        score=exam.score,
        answers={int(key): value for key, value in exam.answers.items()},
        questions=[
            QuestionPublic(
                id=q.id,
                type=q.type,
                prompt=q.prompt,
                options=q.options,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
        review=[QuestionResult(**result) for result in exam.review] if include_review else [],
    )
