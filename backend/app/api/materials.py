from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.llm import LLMError
from app.models import Chapter, Concept, Lesson, Material, Student, Subject, Topic
from app.schemas import (
    ConceptOut,
    LessonSummary,
    MaterialCorrectionIn,
    MaterialOut,
    MaterialTextIn,
)
from app.services import ingestion, pipeline

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.post("", response_model=MaterialOut, status_code=201)
def upload_material(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    title: str | None = Form(default=None),
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    if file is not None:
        name = file.filename or "upload"
        raw = file.file.read()
        pages: list[str] = []
        if name.lower().endswith(".pdf"):
            try:
                pages = ingestion.extract_pdf_pages(raw)
                content = "\n\n".join(pages)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            source_type = "pdf"
        elif name.lower().endswith((".txt", ".md")):
            content = raw.decode("utf-8", errors="replace")
            source_type = "text"
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported file type. Use PDF, TXT, or MD."
            )
        material = Material(
            student_id=student.id,
            title=title or name,
            source_type=source_type,
            filename=name,
            raw_text=ingestion.normalize(content),
            raw_pages=pages,
        )
    elif text:
        material = Material(
            student_id=student.id,
            title=title or "Untitled material",
            source_type="text",
            raw_text=ingestion.normalize(text),
        )
    else:
        raise HTTPException(status_code=400, detail="Provide a file or text.")

    if not material.raw_text:
        raise HTTPException(status_code=400, detail="No readable text found.")

    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.post("/text", response_model=MaterialOut, status_code=201)
def upload_text(
    payload: MaterialTextIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    material = Material(
        student_id=student.id,
        title=payload.title,
        source_type="text",
        raw_text=ingestion.normalize(payload.text),
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.get("", response_model=list[MaterialOut])
def list_materials(
    include_archived: bool = Query(default=False),
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[Material]:
    stmt = select(Material).where(Material.student_id == student.id)
    if not include_archived:
        stmt = stmt.where(Material.archived.is_(False))
    return list(db.scalars(stmt.order_by(Material.created_at.desc())))


@router.patch("/{material_id}/corrections", response_model=MaterialOut)
def correct_material(
    material_id: int,
    payload: MaterialCorrectionIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    material = owned_material(db, material_id, student)
    if (
        (payload.subject_name is not None or payload.chapters is not None)
        and material.status != "ready"
    ):
        raise HTTPException(status_code=409, detail="Process material before moving or splitting chapters.")
    if payload.title is not None:
        material.title = payload.title
    if payload.subject_name is not None:
        subject = db.scalar(select(Subject).where(Subject.material_id == material.id))
        if subject is None:
            subject = Subject(
                user_id=student.user_id,
                material_id=material.id,
                name=payload.subject_name,
            )
            db.add(subject)
        else:
            subject.name = payload.subject_name
    if payload.chapters is not None:
        subject = db.scalar(select(Subject).where(Subject.material_id == material.id))
        if subject is None:
            raise HTTPException(status_code=409, detail="Process material before editing chapters")
        topics = list(
            db.scalars(
                select(Topic)
                .join(Chapter, Chapter.id == Topic.chapter_id)
                .where(Chapter.subject_id == subject.id)
            )
        )
        topic_by_id = {topic.id: topic for topic in topics}
        requested_ids = [topic_id for chapter in payload.chapters for topic_id in chapter.topic_ids]
        if len(requested_ids) != len(set(requested_ids)) or set(requested_ids) != set(topic_by_id):
            raise HTTPException(
                status_code=422,
                detail="Every existing topic must appear exactly once in the corrected chapter list.",
            )
        old_chapter_ids = [chapter.id for chapter in subject.chapters]
        for chapter_index, corrected in enumerate(payload.chapters):
            chapter = Chapter(
                subject_id=subject.id,
                title=corrected.title,
                order_index=chapter_index,
            )
            db.add(chapter)
            db.flush()
            for topic_index, topic_id in enumerate(corrected.topic_ids):
                topic = topic_by_id[topic_id]
                topic.chapter_id = chapter.id
                topic.order_index = topic_index
        db.flush()
        if old_chapter_ids:
            db.execute(delete(Chapter).where(Chapter.id.in_(old_chapter_ids)))
    if payload.title is not None or payload.subject_name is not None or payload.chapters is not None:
        material.corrections_locked = True
    db.commit()
    db.refresh(material)
    return material


@router.post("/{material_id}/archive", response_model=MaterialOut)
def archive_material(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    material = owned_material(db, material_id, student)
    material.archived = True
    db.commit()
    db.refresh(material)
    return material


@router.get("/{material_id}", response_model=MaterialOut)
def get_material(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    return owned_material(db, material_id, student)


@router.post("/{material_id}/process", response_model=MaterialOut)
def process_material(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Material:
    material = owned_material(db, material_id, student)
    if material.status == "processing":
        raise HTTPException(status_code=409, detail="Material is already processing")

    try:
        return pipeline.process_material(db, material)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{material_id}/concepts", response_model=list[ConceptOut])
def list_concepts(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[Concept]:
    owned_material(db, material_id, student)
    return list(
        db.scalars(
            select(Concept)
            .where(Concept.material_id == material_id)
            .order_by(Concept.order_index)
        )
    )


@router.get("/{material_id}/lessons", response_model=list[LessonSummary])
def list_lessons(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[Lesson]:
    owned_material(db, material_id, student)
    return list(
        db.scalars(
            select(Lesson)
            .where(Lesson.material_id == material_id)
            .order_by(Lesson.id)
        )
    )


@router.delete("/{material_id}", status_code=204)
def delete_material(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> None:
    material = owned_material(db, material_id, student)
    db.delete(material)
    db.commit()
