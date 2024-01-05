from .database import Base
from sqlalchemy import Text, Enum, Column, ForeignKey, Integer, String, Index
from sqlalchemy.types import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.schema import UniqueConstraint


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    notes = relationship("Note", back_populates="owner")


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False, index=True)
    detail = Column(Text, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="notes")


class SharedNotes(Base):
    __tablename__ = "shared_notes"
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    note_id = Column(
        Integer,
        ForeignKey(
            "notes.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    )
    permission = Column(
        Enum("edit", "read_only", name="permissions"),
        nullable=False,
        default="read_only",
        index=True,
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
    )
