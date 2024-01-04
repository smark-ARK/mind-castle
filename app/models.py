from .database import Base
from sqlalchemy import Boolean, Enum, Column, ForeignKey, Integer, String, Table
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


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref="categories")

    __table_args__ = (  # Enclose within a tuple
        UniqueConstraint(name, user_id, name="unique_category_per_user"),
    )


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=True,
    )
    owner = relationship("User", backref="notes")
    category = relationship("Category", backref="notes")


class SharedNotes(Base):
    __tablename__ = "shared_notes"
    user_id = Column(
        Integer,
        ForeignKey("Users.id", ondelete="CASCADE"),
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
    )
