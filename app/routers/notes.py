from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from sqlalchemy.orm.session import Session
from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from typing import Optional, List

from app.oauth2 import get_current_user


from app.schemas import (
    NoteResponse,
    NoteResponseWithParticipants,
    NoteBase,
    ShareNote,
    ShareNoteResponse,
)
from app.database import get_db
from app.models import Note, User, SharedNotes

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.get("", response_model=List[NoteResponse])
async def list_notes(
    request: Request,
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notes = (
        db.query(Note)
        .filter(
            Note.owner_id == current_user.id,
        )
        .order_by(desc(Note.created_at))
        .limit(limit)
        .offset(skip)
        .all()
    )

    return notes


@router.get("/search", response_model=List[NoteResponse])
async def search_notes(
    q: Optional[str] = "",
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notes = (
        db.query(Note)
        .filter(
            Note.owner_id == current_user.id,
            or_(
                Note.title.ilike(f"%{q}%"),
                Note.detail.ilike(f"%{q}%"),
            ),
        )
        .order_by(desc(Note.created_at))
        .limit(limit)
        .offset(skip)
        .all()
    )

    return notes


@router.get("/{id}", response_model=NoteResponseWithParticipants)
async def get_note(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id).first()
    )

    if note:
        participants = (
            db.query(User, SharedNotes.permission)
            .join(SharedNotes, SharedNotes.user_id == User.id)
            .filter(SharedNotes.note_id == note.id)
            .all()
        )

        participants_info = [
            {"user": user, "permission": permission}
            for user, permission in participants
        ]
        return {"note": note, "participants": participants_info}

    # If the note is not owned by the current user, check if it's shared
    shared_note = (
        db.query(Note)
        .join(SharedNotes, SharedNotes.note_id == Note.id)
        .filter(Note.id == id, SharedNotes.user_id == current_user.id)
        .first()
    )
    note = shared_note

    if not shared_note:
        raise HTTPException(
            detail=f"Note with id {id} is not shared with or owned by the current user",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    participants = (
        db.query(User, SharedNotes.permission)
        .join(SharedNotes, SharedNotes.user_id == User.id)
        .filter(SharedNotes.note_id == note.id)
        .all()
    )

    participants_info = [
        {"user": user, "permission": permission} for user, permission in participants
    ]

    return {"note": note, "participants": participants_info}


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
    note_query = db.query(Note).filter(Note.id == id)

    if not note_query.first():
        raise HTTPException(
            detail=f"Note with id {id} does not exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # Check if the current user has access to the note
    if note_query.first().owner_id != current_user.id:
        # Check if the note is shared with the current user
        shared_note = (
            db.query(SharedNotes)
            .filter(SharedNotes.note_id == id, SharedNotes.user_id == current_user.id)
            .first()
        )
        if not shared_note or shared_note.permission != "edit":
            raise HTTPException(
                detail="You do not have permission to edit this note",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    # Prevent updating owner_id
    if hasattr(updated_note, "owner_id"):
        delattr(updated_note, "owner_id")

    # Update the note
    note_query.update(updated_note.dict(), synchronize_session=False)
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


@router.post("/{id}/share", response_model=ShareNoteResponse)
async def share_note(
    share_note: ShareNote,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id).first()
    )
    if not note:
        raise HTTPException(
            detail=f"Note with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    other_user = db.query(User).filter(User.id == share_note.user_id).first()
    if not other_user:
        raise HTTPException(
            detail=f"User with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    try:
        shared = SharedNotes(**share_note.dict(), note_id=id)
        db.add(shared)
        db.commit()
    except Exception as e:
        db.rollback()
        if "duplicate key" in str(e):
            raise HTTPException(
                detail=f"Already sharing note with id: {id} with {other_user.username}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    return {"note": note, "user": other_user, "permission": share_note.permission}


@router.delete("/{id}/share")
async def unshare_note(
    id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id).first()
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {id} not found.",
        )
    if note.owner_id != current_user.id:
        raise HTTPException(
            detail="you are not the owner of this note",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    # Delete the shared note entry
    shared_note = (
        db.query(SharedNotes)
        .filter(SharedNotes.note_id == id, SharedNotes.user_id == user_id)
        .first()
    )
    if not shared_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note is not shared with user {user_id}.",
        )
    try:
        db.delete(shared_note)
        db.commit()

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error unsharing note: {str(e)}",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )  # 204 No Content for successful deletion


@router.put("/{id}/share", response_model=ShareNoteResponse)
async def update_permission(
    share_note: ShareNote,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = (
        db.query(Note).filter(Note.id == id, Note.owner_id == current_user.id).first()
    )
    if not note:
        raise HTTPException(
            detail=f"Note with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    if note.owner_id != current_user.id:
        raise HTTPException(
            detail="you are not the owner of this note",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    other_user = db.query(User).filter(User.id == share_note.user_id).first()
    if not other_user:
        raise HTTPException(
            detail=f"User with id {id} Does not Exist",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    shared_note = (
        db.query(SharedNotes)
        .filter(SharedNotes.note_id == id, SharedNotes.user_id == share_note.user_id)
        .first()
    )
    if not shared_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note is not shared with user {share_note.user_id}.",
        )

    try:
        shared_note.permission = share_note.permission
        db.add(shared_note)
        db.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating permission: {str(e)}",
        )
    return {"note": note, "user": other_user, "permission": share_note.permission}


@router.get("/shared/", response_model=List[NoteResponse])
async def list_shared_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: Optional[int] = 10,
    skip: Optional[int] = 0,
):
    shared_notes = (
        db.query(Note)
        .join(SharedNotes, SharedNotes.note_id == Note.id)
        .filter(SharedNotes.user_id == current_user.id)
        .order_by(desc(Note.created_at))
        .limit(limit)
        .offset(skip)
        .all()
    )
    return shared_notes
