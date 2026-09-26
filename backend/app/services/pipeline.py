from __future__ import annotations

from sqlalchemy.orm import Session

from app.llm import LLMError
from app.models import Material
from app.services import ingestion, structuring, teaching


def process_material(db: Session, material: Material) -> Material:
    """Run the full pipeline: ingest → structure → teach.

    The material.status field reflects progress and is what the frontend polls.
    """
    material.status = "processing"
    material.error = None
    db.commit()

    try:
        # 1. Read
        material.subjects.clear()
        material.concepts.clear()
        db.flush()
        material.chunks.clear()
        db.flush()
        student = material.student
        user_id = student.user_id if student is not None else None
        for chunk in ingestion.ingest(
            material.raw_text, db=db, user_id=user_id
        ):
            chunk.material_id = material.id
            db.add(chunk)
        db.commit()

        # 2. Organize (Subject -> Chapter -> Topic + concepts + grounding)
        concepts = structuring.build_curriculum(db, material)

        # 3. Teach
        if concepts:
            teaching.generate_all_lessons(db, material)

        material.status = "ready"
        db.commit()
    except (LLMError, ValueError) as exc:
        db.rollback()
        material.status = "failed"
        material.error = str(exc)
        db.commit()

    db.refresh(material)
    return material
