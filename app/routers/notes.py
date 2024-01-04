from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm.session import Session
from typing import Optional, List

from app.oauth2 import get_current_user


from app.schemas import NoteResponse, NoteBase
from app.database import get_db
from app.models import Note, User

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("", response_model=List[NoteResponse])
async def list_notes(
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    category_id: Optional[int] = None,
    search: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notes = (
        db.query(Note)
        .filter(
            User.id == current_user.id,
            Note.title.contains(search),
            Note.detail.contains(search),
            Note.category_id == category_id,
        )
        .limit(limit)
        .offset(skip)
        .all()
    )

    return notes


@router.get("/{id}", response_model=NoteResponse)
async def get_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id).first()
    )
    if not Note:
        raise HTTPException(
            detail=f"Note with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return note


@router.post("", response_model=NoteResponse)
async def create_note(
    note: NoteBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        new_note = Note(**note.dict(), owner_id=current_user.id)
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_404_NOT_FOUND)
    return new_note


@router.put("/{id}")
async def update_note(
    id: int,
    updated_note: NoteBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_query = db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id)
    note = note_query.first()
    if not note:
        raise HTTPException(
            detail=f"Note with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    updated_note.category_id = (
        None if updated_note.category_id == 0 else updated_note.category_id
    )
    updated_note = note_query.update(updated_note.dict(), synchronize_session=False)
    db.commit()

    return note_query.first()


@router.delete("/{id}", response_model=NoteResponse)
async def delete_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note_query = db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id)
    note = note_query.first()
    if not note:
        raise HTTPException(
            detail=f"Note with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    note_query.delete(synchronize_session=False)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# @router.post("/{id}/share")
# async def share_note()
