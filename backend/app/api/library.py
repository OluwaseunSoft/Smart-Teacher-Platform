from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user, owned_material
from app.db import get_db
from app.models import LibraryFolder, Material, Student, User
from app.schemas import (
    LibraryFolderCreateIn,
    LibraryFolderOut,
    LibraryFolderUpdateIn,
    MaterialOut,
    MaterialFolderIn,
)

router = APIRouter(prefix="/api", tags=["library"])


@router.get("/folders", response_model=list[LibraryFolderOut])
def list_folders(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[LibraryFolder]:
    return list(
        db.scalars(
            select(LibraryFolder)
            .where(LibraryFolder.user_id == user.id)
            .order_by(LibraryFolder.name, LibraryFolder.id)
        )
    )


@router.post(
    "/folders", response_model=LibraryFolderOut, status_code=status.HTTP_201_CREATED
)
def create_folder(
    payload: LibraryFolderCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LibraryFolder:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Folder name cannot be blank.")
    if payload.parent_id is not None:
        _owned_folder(db, payload.parent_id, user.id)
    folder = LibraryFolder(user_id=user.id, parent_id=payload.parent_id, name=name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.patch("/folders/{folder_id}", response_model=LibraryFolderOut)
def update_folder(
    folder_id: int,
    payload: LibraryFolderUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LibraryFolder:
    folder = _owned_folder(db, folder_id, user.id)
    if "name" in payload.model_fields_set:
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Folder name cannot be blank.")
        folder.name = name
    if "parent_id" in payload.model_fields_set:
        if payload.parent_id == folder.id:
            raise HTTPException(status_code=409, detail="A folder cannot contain itself.")
        if payload.parent_id is not None:
            parent = _owned_folder(db, payload.parent_id, user.id)
            ancestor = parent
            while ancestor is not None:
                if ancestor.id == folder.id:
                    raise HTTPException(
                        status_code=409, detail="Moving a folder into its descendant is not allowed."
                    )
                ancestor = db.get(LibraryFolder, ancestor.parent_id) if ancestor.parent_id else None
        folder.parent_id = payload.parent_id
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    folder = _owned_folder(db, folder_id, user.id)
    has_children = db.scalar(
        select(LibraryFolder.id).where(LibraryFolder.parent_id == folder.id).limit(1)
    )
    has_materials = db.scalar(
        select(Material.id).where(Material.folder_id == folder.id).limit(1)
    )
    if has_children is not None or has_materials is not None:
        raise HTTPException(
            status_code=409,
            detail="Move files and subfolders out before deleting this folder.",
        )
    db.delete(folder)
    db.commit()


@router.patch("/materials/{material_id}/folder", response_model=MaterialOut)
def move_material(
    material_id: int,
    payload: MaterialFolderIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Material:
    material = owned_material(db, material_id, student)
    if payload.folder_id is not None:
        _owned_folder(db, payload.folder_id, user.id)
    material.folder_id = payload.folder_id
    db.commit()
    db.refresh(material)
    return material


def _owned_folder(db: Session, folder_id: int, user_id: int) -> LibraryFolder:
    folder = db.get(LibraryFolder, folder_id)
    if folder is None or folder.user_id != user_id:
        raise HTTPException(status_code=404, detail="Folder not found.")
    return folder
