"""Deterministic demo-data seeder.

Creates demo accounts (a student with several weeks of realistic progress and an
administrator) plus sample study material in two subjects, complete with the
Subject -> Chapter -> Topic curriculum, grounding, lessons, quizzes, attempts and
mastery history.

This module never calls an LLM: chunks are created without embeddings (retrieval
falls back to lexical matching) and curriculum/lessons/questions are hand-authored.

Usage (from ``backend/``)::

    .\\.venv\\Scripts\\python.exe -m app.seed
    .\\.venv\\Scripts\\python.exe -m app.seed --reset   # drop + recreate everything
"""

from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import (
    ROLE_ADMIN,
    ROLE_STUDENT,
    Attempt,
    Chapter,
    Chunk,
    Concept,
    Lesson,
    Mastery,
    MasteryEvent,
    Material,
    Question,
    ReviewSchedule,
    Student,
    StudentProfile,
    StudySession,
    Subject,
    Topic,
    TopicChunk,
    User,
)
from app.security import hash_password
from app.services.ingestion import chunk_text
from app.services.retrieval import rank_chunks

ALPHA = 0.35


# --------------------------------------------------------------------------- #
# Authored curriculum content
# --------------------------------------------------------------------------- #
DEMO_CURRICULUM: list[dict] = [
    {
        "subject": "Biology",
        "language": "en",
        "raw_text": (
            "Cell biology is the study of the structure and function of cells, the "
            "basic unit of life. Every cell is bounded by a plasma membrane that "
            "controls what enters and leaves the cell. Prokaryotic cells, such as "
            "bacteria, have no nucleus and no membrane-bound organelles. Eukaryotic "
            "cells contain a true nucleus and many organelles. The nucleus stores the "
            "cell's genetic material in the form of DNA and controls cellular "
            "activities. Mitochondria are the powerhouse of the cell: they carry out "
            "cellular respiration to produce ATP, the energy currency of the cell. "
            "Ribosomes assemble proteins from amino acids. The endoplasmic reticulum "
            "transports materials, and the Golgi apparatus packages and modifies "
            "proteins. Plant cells also contain chloroplasts where photosynthesis "
            "converts light energy into glucose. Cells divide to grow and repair "
            "tissues. During mitosis a parent cell produces two genetically identical "
            "daughter cells, passing a complete copy of its DNA to each. DNA is a "
            "double helix made of four bases, and genes are sections of DNA that code "
            "for traits. Alleles are different versions of a gene, and an organism's "
            "phenotype results from the interaction of its genotype with the "
            "environment."
        ),
        "chapters": [
            {
                "title": "Cell Biology",
                "topics": [
                    {
                        "title": "Cell Structure",
                        "summary": "The plasma membrane, prokaryotes vs eukaryotes and the basic parts of a cell.",
                        "difficulty": "intro",
                        "lesson": {
                            "title": "Inside the Cell",
                            "objectives": [
                                "Describe the role of the plasma membrane",
                                "Compare prokaryotic and eukaryotic cells",
                            ],
                            "content": (
                                "## Inside the Cell\n\n"
                                "The **plasma membrane** is a selectively permeable "
                                "barrier around every cell. **Prokaryotic** cells (e.g. "
                                "bacteria) lack a nucleus; **eukaryotic** cells have a "
                                "true nucleus and membrane-bound organelles.\n\n"
                                "### Key idea\n"
                                "Every living cell is enclosed by a membrane that "
                                "controls the movement of substances in and out."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "Which structure controls what enters and leaves a cell?",
                                "options": ["Nucleus", "Plasma membrane", "Ribosome", "Golgi apparatus"],
                                "answer": "Plasma membrane",
                                "explanation": "The plasma membrane is selectively permeable.",
                                "difficulty": 1,
                            },
                            {
                                "type": "short",
                                "prompt": "Name one key difference between prokaryotic and eukaryotic cells.",
                                "answer": "Eukaryotic cells have a nucleus; prokaryotic cells do not.",
                                "explanation": "Prokaryotes lack a true nucleus and membrane-bound organelles.",
                                "difficulty": 2,
                            },
                        ],
                    },
                    {
                        "title": "Organelles and Their Functions",
                        "summary": "Nucleus, mitochondria, ribosomes, ER, Golgi and chloroplasts.",
                        "difficulty": "core",
                        "lesson": {
                            "title": "Organelles at Work",
                            "objectives": [
                                "Match organelles to their functions",
                                "Explain why mitochondria are called the powerhouse",
                            ],
                            "content": (
                                "## Organelles at Work\n\n"
                                "- **Nucleus** - stores DNA and controls the cell.\n"
                                "- **Mitochondria** - produce ATP through respiration.\n"
                                "- **Ribosomes** - assemble proteins.\n"
                                "- **Endoplasmic reticulum** - transports materials.\n"
                                "- **Golgi apparatus** - packages and modifies proteins.\n"
                                "- **Chloroplasts** (plants) - carry out photosynthesis."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "Which organelle produces ATP during cellular respiration?",
                                "options": ["Nucleus", "Mitochondria", "Golgi apparatus", "Ribosome"],
                                "answer": "Mitochondria",
                                "explanation": "Mitochondria are the powerhouse of the cell.",
                                "difficulty": 2,
                            },
                            {
                                "type": "mcq",
                                "prompt": "Where does photosynthesis take place in a plant cell?",
                                "options": ["Chloroplast", "Nucleus", "Mitochondria", "Vacuole"],
                                "answer": "Chloroplast",
                                "explanation": "Chloroplasts convert light energy into glucose.",
                                "difficulty": 2,
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Cell Division and Genetics",
                "topics": [
                    {
                        "title": "Mitosis",
                        "summary": "How a parent cell produces two identical daughter cells.",
                        "difficulty": "core",
                        "lesson": {
                            "title": "Understanding Mitosis",
                            "objectives": [
                                "Summarise the outcome of mitosis",
                                "Explain why daughter cells are identical",
                            ],
                            "content": (
                                "## Understanding Mitosis\n\n"
                                "Mitosis is the process by which one parent cell divides "
                                "into **two genetically identical daughter cells**. A "
                                "complete copy of the DNA is passed to each daughter cell, "
                                "which allows organisms to grow and repair tissues."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "How many daughter cells does mitosis produce?",
                                "options": ["One", "Two", "Four", "Eight"],
                                "answer": "Two",
                                "explanation": "Mitosis produces two identical daughter cells.",
                                "difficulty": 1,
                            },
                            {
                                "type": "short",
                                "prompt": "Why are the daughter cells of mitosis genetically identical to the parent cell?",
                                "answer": "Each daughter cell receives a complete copy of the DNA.",
                                "explanation": "DNA is replicated and divided equally.",
                                "difficulty": 3,
                            },
                        ],
                    },
                    {
                        "title": "DNA and Inheritance",
                        "summary": "DNA, genes, alleles, genotype and phenotype.",
                        "difficulty": "advanced",
                        "lesson": {
                            "title": "From DNA to Traits",
                            "objectives": [
                                "Describe the structure of DNA",
                                "Relate genes, alleles and phenotype",
                            ],
                            "content": (
                                "## From DNA to Traits\n\n"
                                "DNA is a **double helix** built from four bases. A "
                                "**gene** is a section of DNA that codes for a trait. "
                                "Different versions of a gene are called **alleles**. An "
                                "organism's **genotype** is its genetic makeup, while its "
                                "**phenotype** is the observable result of that genotype "
                                "interacting with the environment."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "What is the shape of a DNA molecule?",
                                "options": ["Single strand", "Double helix", "Triple helix", "Circle"],
                                "answer": "Double helix",
                                "explanation": "DNA is a double helix of paired bases.",
                                "difficulty": 2,
                            },
                            {
                                "type": "short",
                                "prompt": "What is an allele?",
                                "answer": "A different version of a gene.",
                                "explanation": "Alleles are alternative forms of a gene.",
                                "difficulty": 3,
                            },
                        ],
                    },
                ],
            },
        ],
    },
    {
        "subject": "Algebra",
        "language": "en",
        "raw_text": (
            "Algebra is the branch of mathematics that uses symbols to represent "
            "numbers and relationships. A linear equation is an equation in which the "
            "highest power of the variable is one, for example 2x + 3 = 11. To solve "
            "it, apply inverse operations to isolate the variable. A linear function "
            "can be written in slope-intercept form y = mx + b, where m is the slope "
            "and b is the y-intercept. A system of linear equations is a set of two or "
            "more equations that share variables; the solution is the point where the "
            "lines intersect. Systems can be solved by substitution or elimination. "
            "When the lines are parallel there is no solution, and when they are the "
            "same line there are infinitely many solutions. A quadratic equation has "
            "the form ax^2 + bx + c = 0 and its graph is a parabola. Quadratics can be "
            "solved by factoring, by completing the square, or by the quadratic "
            "formula x = (-b +/- sqrt(b^2 - 4ac)) / 2a. The discriminant b^2 - 4ac "
            "tells us how many real roots exist: positive means two, zero means one, "
            "and negative means none. The product of two binomials such as (x + 2)(x + "
            "3) expands using the distributive property."
        ),
        "chapters": [
            {
                "title": "Linear Equations",
                "topics": [
                    {
                        "title": "Solving Linear Equations",
                        "summary": "Isolating a variable with inverse operations.",
                        "difficulty": "intro",
                        "lesson": {
                            "title": "Solving Step by Step",
                            "objectives": [
                                "Solve one-variable linear equations",
                                "Use inverse operations correctly",
                            ],
                            "content": (
                                "## Solving Step by Step\n\n"
                                "A **linear equation** has a variable to the first power. "
                                "To solve `2x + 3 = 11`, subtract 3 from both sides to get "
                                "`2x = 8`, then divide both sides by 2 to get `x = 4`. "
                                "Always keep the equation balanced."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "Solve for x: 2x + 3 = 11",
                                "options": ["x = 2", "x = 4", "x = 7", "x = 8"],
                                "answer": "x = 4",
                                "explanation": "Subtract 3 then divide by 2.",
                                "difficulty": 1,
                            },
                            {
                                "type": "short",
                                "prompt": "Solve for x: 3x - 6 = 9",
                                "answer": "x = 5",
                                "explanation": "Add 6 to get 3x = 15, then divide by 3.",
                                "difficulty": 2,
                            },
                        ],
                    },
                    {
                        "title": "Systems of Linear Equations",
                        "summary": "Solving two equations with two variables by substitution or elimination.",
                        "difficulty": "core",
                        "lesson": {
                            "title": "Two Equations, Two Unknowns",
                            "objectives": [
                                "Interpret a solution as an intersection point",
                                "Solve a system by substitution",
                            ],
                            "content": (
                                "## Two Equations, Two Unknowns\n\n"
                                "A **system** of linear equations shares variables. Its "
                                "solution is the point where the lines **intersect**. "
                                "Parallel lines mean no solution; identical lines mean "
                                "infinitely many. Use **substitution** or **elimination** "
                                "to solve."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "A system of two parallel lines has how many solutions?",
                                "options": ["One", "Two", "None", "Infinitely many"],
                                "answer": "None",
                                "explanation": "Parallel lines never intersect.",
                                "difficulty": 2,
                            },
                            {
                                "type": "short",
                                "prompt": "Solve: y = x + 1 and y = 2x - 1",
                                "answer": "x = 2, y = 3",
                                "explanation": "Set x + 1 = 2x - 1, so x = 2 and y = 3.",
                                "difficulty": 3,
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Quadratic Equations",
                "topics": [
                    {
                        "title": "Factoring Quadratics",
                        "summary": "Expressing a quadratic as a product of binomials to find its roots.",
                        "difficulty": "core",
                        "lesson": {
                            "title": "Factoring to Find Roots",
                            "objectives": [
                                "Factor simple quadratics",
                                "Use the zero-product property",
                            ],
                            "content": (
                                "## Factoring to Find Roots\n\n"
                                "A **quadratic** has the form `ax^2 + bx + c = 0` and graphs "
                                "as a parabola. To factor, find two numbers that multiply "
                                "to `c` and add to `b`. For example `x^2 + 5x + 6 = (x + 2)"
                                "(x + 3)`, so the roots are `x = -2` and `x = -3`."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "Factor x^2 + 5x + 6",
                                "options": ["(x+2)(x+3)", "(x+1)(x+6)", "(x-2)(x-3)", "(x+5)(x+1)"],
                                "answer": "(x+2)(x+3)",
                                "explanation": "2 and 3 multiply to 6 and add to 5.",
                                "difficulty": 2,
                            },
                            {
                                "type": "short",
                                "prompt": "What are the roots of (x + 2)(x + 3) = 0?",
                                "answer": "x = -2 and x = -3",
                                "explanation": "Use the zero-product property.",
                                "difficulty": 3,
                            },
                        ],
                    },
                    {
                        "title": "The Quadratic Formula",
                        "summary": "Using the discriminant and the quadratic formula to solve any quadratic.",
                        "difficulty": "advanced",
                        "lesson": {
                            "title": "The Quadratic Formula",
                            "objectives": [
                                "Apply the quadratic formula",
                                "Interpret the discriminant",
                            ],
                            "content": (
                                "## The Quadratic Formula\n\n"
                                "For `ax^2 + bx + c = 0`,\n\n"
                                "`x = (-b +/- sqrt(b^2 - 4ac)) / 2a`.\n\n"
                                "The **discriminant** `b^2 - 4ac` tells you the number of "
                                "real roots: positive -> two, zero -> one, negative -> none."
                            ),
                        },
                        "questions": [
                            {
                                "type": "mcq",
                                "prompt": "What does a discriminant of zero mean?",
                                "options": ["Two real roots", "One real root", "No real roots", "A straight line"],
                                "answer": "One real root",
                                "explanation": "When b^2 - 4ac = 0 there is exactly one real root.",
                                "difficulty": 3,
                            },
                            {
                                "type": "short",
                                "prompt": "State the quadratic formula.",
                                "answer": "x = (-b +/- sqrt(b^2 - 4ac)) / 2a",
                                "explanation": "It solves any quadratic equation.",
                                "difficulty": 3,
                            },
                        ],
                    },
                ],
            },
        ],
    },
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _apply_mastery(score: float, correct: bool, difficulty: int) -> float:
    weight = 0.6 + 0.1 * max(1, min(5, difficulty))
    observed = 1.0 if correct else 0.0
    target = weight * observed + (1 - weight) * 0.5
    return max(0.0, min(1.0, (1 - ALPHA) * score + ALPHA * target))


def is_seeded(db: Session) -> bool:
    return (
        db.scalar(
            select(User.id).where(User.email == settings.SEED_DEMO_STUDENT_EMAIL)
        )
        is not None
    )


def _create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: str,
    display_name: str,
    grade: int | None = None,
    language: str = "en",
    timezone_name: str = "UTC",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        display_name=display_name,
        grade=grade,
        language=language,
        timezone=timezone_name,
    )
    db.add(user)
    db.flush()
    if role == ROLE_STUDENT:
        db.add(StudentProfile(user_id=user.id))
    return user


def _build_material(
    db: Session, student: Student, spec: dict, now: datetime
) -> tuple[Material, list[tuple[Topic, Concept, Lesson]]]:
    material = Material(
        student_id=student.id,
        title=spec["subject"],
        source_type="text",
        raw_text=spec["raw_text"],
        status="ready",
        created_at=now - timedelta(days=24),
        updated_at=now - timedelta(days=24),
    )
    db.add(material)
    db.flush()

    for index, content in enumerate(chunk_text(spec["raw_text"])):
        db.add(Chunk(material_id=material.id, index=index, content=content))
    db.commit()

    subject = Subject(
        user_id=student.user_id,
        material_id=material.id,
        name=spec["subject"],
        language=spec.get("language", "en"),
    )
    db.add(subject)
    db.flush()

    created: list[tuple[Topic, Concept, Lesson]] = []
    chapter_order = 0
    topic_order = 0
    for chapter_spec in spec["chapters"]:
        chapter = Chapter(
            subject_id=subject.id,
            title=chapter_spec["title"],
            order_index=chapter_order,
        )
        db.add(chapter)
        chapter_order += 1
        db.flush()

        for topic_spec in chapter_spec["topics"]:
            topic = Topic(
                chapter_id=chapter.id,
                title=topic_spec["title"],
                summary=topic_spec["summary"],
                difficulty=topic_spec["difficulty"],
                order_index=topic_order,
            )
            db.add(topic)
            topic_order += 1
            db.flush()

            concept = Concept(
                material_id=material.id,
                title=topic_spec["title"],
                summary=topic_spec["summary"],
                order_index=topic.order_index,
                difficulty=topic_spec["difficulty"],
            )
            db.add(concept)
            db.flush()
            topic.concept_id = concept.id

            ranked = rank_chunks(db, material.id, f"{topic.title}. {topic.summary}")
            for chunk, relevance in ranked:
                db.add(
                    TopicChunk(
                        topic_id=topic.id, chunk_id=chunk.id, relevance=relevance
                    )
                )

            lesson_spec = topic_spec["lesson"]
            lesson = Lesson(
                material_id=material.id,
                concept_id=concept.id,
                topic_id=topic.id,
                title=lesson_spec["title"],
                objectives=list(lesson_spec["objectives"]),
                content=lesson_spec["content"],
                language=spec.get("language", "en"),
                grounding=[
                    {"chunk_id": chunk.id, "index": chunk.index} for chunk, _ in ranked
                ],
                status="ready",
                simpler=False,
            )
            db.add(lesson)
            db.flush()

            for question_spec in topic_spec["questions"]:
                db.add(
                    Question(
                        lesson_id=lesson.id,
                        concept_id=concept.id,
                        type=question_spec["type"],
                        prompt=question_spec["prompt"],
                        options=question_spec.get("options"),
                        answer=question_spec["answer"],
                        explanation=question_spec["explanation"],
                        difficulty=question_spec["difficulty"],
                    )
                )

            created.append((topic, concept, lesson))

    db.commit()
    return material, created


def _seed_progress(
    db: Session,
    student: Student,
    entries: list[tuple[Material, list[tuple[Topic, Concept, Lesson]]]],
    now: datetime,
) -> None:
    """Simulate ~3 weeks of adaptive study producing attempts and mastery."""
    rng = random.Random(2024)

    concepts: list[tuple[Material, Topic, Concept, Lesson]] = [
        (material, topic, concept, lesson)
        for material, rows in entries
        for topic, concept, lesson in rows
    ]

    for index, (material, topic, concept, lesson) in enumerate(concepts):
        questions = list(
            db.scalars(select(Question).where(Question.lesson_id == lesson.id))
        )
        if not questions:
            continue

        base_days_ago = max(2, 22 - index * 2)
        rounds = 2 + (index % 3)
        target = min(0.95, max(0.55, 0.55 + (len(concepts) - index) * 0.05))

        score = 0.0
        attempts = 0
        correct_count = 0
        last_ts = now - timedelta(days=base_days_ago)

        for round_index in range(rounds):
            timestamp = now - timedelta(
                days=base_days_ago - round_index, hours=rng.randint(0, 4)
            )
            for question in questions:
                is_correct = rng.random() < target
                db.add(
                    Attempt(
                        student_id=student.id,
                        question_id=question.id,
                        response=question.answer if is_correct else "Incorrect attempt",
                        is_correct=is_correct,
                        created_at=timestamp,
                    )
                )
                previous = score
                score = _apply_mastery(score, is_correct, question.difficulty)
                db.add(
                    MasteryEvent(
                        student_id=student.id,
                        concept_id=concept.id,
                        topic_id=topic.id,
                        score=round(score, 6),
                        delta=round(score - previous, 6),
                        is_correct=is_correct,
                        source="quiz",
                        created_at=timestamp,
                    )
                )
                attempts += 1
                correct_count += 1 if is_correct else 0
                last_ts = timestamp

        db.add(
            Mastery(
                student_id=student.id,
                concept_id=concept.id,
                score=round(score, 4),
                attempts=attempts,
                correct=correct_count,
                updated_at=last_ts,
            )
        )
        db.add(
            ReviewSchedule(
                user_id=student.user_id,
                topic_id=topic.id,
                interval_days=7 if score >= 0.8 else 1,
                ease=2.6 if score >= 0.8 else 2.3,
                repetitions=3 if score >= 0.8 else 1,
                lapses=0 if score >= 0.8 else 2,
                last_reviewed_at=last_ts,
                due_at=now + timedelta(days=6) if score >= 0.8 else now,
            )
        )

    db.commit()


def seed(db: Session, *, now: datetime | None = None) -> dict:
    """Seed demo data. Idempotent: a no-op if the demo student already exists."""
    now = now or datetime.now(timezone.utc)
    if is_seeded(db):
        return {"created": False, "reason": "demo data already present"}

    student_user = _create_user(
        db,
        email=settings.SEED_DEMO_STUDENT_EMAIL,
        password=settings.SEED_DEMO_STUDENT_PASSWORD,
        role=ROLE_STUDENT,
        display_name="Amina Yusuf",
        grade=8,
        language="en",
        timezone_name="UTC",
    )
    _create_user(
        db,
        email=settings.SEED_DEMO_ADMIN_EMAIL,
        password=settings.SEED_DEMO_ADMIN_PASSWORD,
        role=ROLE_ADMIN,
        display_name="Demo Administrator",
    )

    student = Student(user_id=student_user.id, name=student_user.display_name)
    db.add(student)
    db.flush()

    entries: list[tuple[Material, list[tuple[Topic, Concept, Lesson]]]] = []
    for spec in DEMO_CURRICULUM:
        entries.append(_build_material(db, student, spec, now))

    _seed_progress(db, student, entries, now)

    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == student_user.id)
    )
    if profile is not None:
        profile.onboarding_completed = True
        profile.streak_current = 6
        profile.streak_longest = 21
        profile.last_active_date = now.date()
        db.add(profile)

    # One active study session on the (weaker) Biology material.
    biology, biology_rows = entries[0]
    db.add(
        StudySession(
            student_id=student.id,
            material_id=biology.id,
            current_concept_id=biology_rows[-1][1].id,
            status="active",
            created_at=now - timedelta(days=22),
            updated_at=now - timedelta(days=1),
        )
    )
    db.commit()

    return {
        "created": True,
        "student_email": settings.SEED_DEMO_STUDENT_EMAIL,
        "student_password": settings.SEED_DEMO_STUDENT_PASSWORD,
        "admin_email": settings.SEED_DEMO_ADMIN_EMAIL,
        "admin_password": settings.SEED_DEMO_ADMIN_PASSWORD,
        "subjects": [s["subject"] for s in DEMO_CURRICULUM],
        "materials": len(entries),
        "concepts": db.scalar(select(func.count()).select_from(Concept)),
        "attempts": db.scalar(select(func.count()).select_from(Attempt)),
        "mastery_events": db.scalar(
            select(func.count()).select_from(MasteryEvent)
        ),
    }


def _reset() -> None:
    from app.db import Base, engine

    Base.metadata.drop_all(bind=engine)
    init_db()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Suhail Smart demo data.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="drop ALL tables and recreate them before seeding (destructive)",
    )
    args = parser.parse_args()

    if args.reset:
        _reset()
    else:
        init_db()

    db = SessionLocal()
    try:
        result = seed(db)
    finally:
        db.close()

    if not result["created"]:
        print(f"No changes: {result['reason']}. Use --reset to recreate.")
        return

    print("Seeded demo data:")
    print(f"  student : {result['student_email']} / {result['student_password']}")
    print(f"  admin   : {result['admin_email']} / {result['admin_password']}")
    print(f"  subjects: {', '.join(result['subjects'])}")
    print(
        f"  material: {result['materials']} | concepts: {result['concepts']} "
        f"| attempts: {result['attempts']} "
        f"| mastery events: {result['mastery_events']}"
    )


if __name__ == "__main__":
    main()
