from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.llm import LLMError
from app.models import Concept, Lesson, Material, Student
from app.schemas import ConceptOut, LessonSummary, MaterialOut, MaterialTextIn
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
        if name.lower().endswith(".pdf"):
            try:
                content = ingestion.extract_pdf(raw)
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
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[Material]:
    return list(
        db.scalars(
            select(Material)
            .where(Material.student_id == student.id)
            .order_by(Material.created_at.desc())
        )
    )


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
