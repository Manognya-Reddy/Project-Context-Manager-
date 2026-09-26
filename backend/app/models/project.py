import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, Float, Integer, Boolean, Index
)
from sqlalchemy.orm import relationship

from app.database.db import Base


def gen_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    semantic_description = Column(Text, nullable=True)
    # Embedding stored as a comma-separated float string (kept simple —
    # avoids adding a vector DB dependency; see FAISS note in retrieval
    # service for the optional upgrade path).
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=now)
    trigger = Column(String, default="manual")  # manual|periodic|git_branch_change|...

    project = relationship("Project", back_populates="snapshots")
    files = relationship("SnapshotFile", back_populates="snapshot", cascade="all, delete-orphan")
    browser_tabs = relationship("BrowserTab", back_populates="snapshot", cascade="all, delete-orphan")
    git_context = relationship("GitContext", back_populates="snapshot", uselist=False, cascade="all, delete-orphan")
    terminal_context = relationship("TerminalContext", back_populates="snapshot", uselist=False, cascade="all, delete-orphan")


class SnapshotFile(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=gen_id)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)
    path = Column(String, nullable=False)
    kind = Column(String, default="recent")  # open|recent
    last_modified = Column(DateTime, nullable=True)
    size_bytes = Column(Integer, nullable=True)

    snapshot = relationship("Snapshot", back_populates="files")


class BrowserTab(Base):
    __tablename__ = "browser_tabs"

    id = Column(String, primary_key=True, default=gen_id)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    warning = Column(String, nullable=True)

    snapshot = relationship("Snapshot", back_populates="browser_tabs")


class GitContext(Base):
    __tablename__ = "git_context"

    id = Column(String, primary_key=True, default=gen_id)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)
    repository_path = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    last_commit_hash = Column(String, nullable=True)
    last_commit_message = Column(Text, nullable=True)
    modified_files = Column(Text, nullable=True)  # newline-joined list
    untracked_files = Column(Text, nullable=True)
    diff_patch = Column(Text, nullable=True)
    untracked_content = Column(Text, nullable=True)  # json map

    snapshot = relationship("Snapshot", back_populates="git_context")


class TerminalContext(Base):
    __tablename__ = "terminal_context"

    id = Column(String, primary_key=True, default=gen_id)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)
    working_directory = Column(String, nullable=True)
    recent_commands = Column(Text, nullable=True)  # newline-joined, redacted
    active_venv = Column(String, nullable=True)
    running_processes = Column(Text, nullable=True)  # newline-joined

    snapshot = relationship("Snapshot", back_populates="terminal_context")


class RestorationLog(Base):
    """Structured logging for experiments (spec section 28)."""
    __tablename__ = "restoration_logs"

    id = Column(String, primary_key=True, default=gen_id)
    timestamp = Column(DateTime, default=now)
    query = Column(Text, nullable=True)
    retrieved_project_id = Column(String, nullable=True)
    correct_project_id = Column(String, nullable=True)
    similarity_score = Column(Float, nullable=True)
    retrieval_rank = Column(Integer, nullable=True)
    restoration_components = Column(Text, nullable=True)  # JSON string
    restoration_success = Column(Boolean, nullable=True)
    time_taken_seconds = Column(Float, nullable=True)
    manual_intervention = Column(Boolean, nullable=True)


class MemoryItem(Base):
    """
    One row per individual thing PCM has ever seen inside a snapshot: a
    file, a browser tab, a commit message. Each gets its own embedding so
    a vague query ("the resume I sent Microsoft") can match a single file
    or tab by meaning, not just the project it lives under.
    """
    __tablename__ = "memory_items"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    snapshot_id = Column(String, ForeignKey("snapshots.id"), nullable=False)
    kind = Column(String, nullable=False)  # file | tab | commit
    text = Column(Text, nullable=False)     # what got embedded
    locator = Column(Text, nullable=False)  # file path or tab url
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)


class Event(Base):
    """
    Persistent history, separate from snapshots. A snapshot is "what does
    my workspace look like right now" - an event is "something happened".
    Events survive across projects and across time, which is what lets us
    answer things like "where's the PNG I added yesterday" from a
    different project than the one it happened in.
    """
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_created_at", "created_at"),
        Index("ix_events_project_id", "project_id"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_path", "path"),
    )

    id = Column(String, primary_key=True, default=gen_id)
    created_at = Column(DateTime, default=now)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    event_type = Column(String, nullable=False)
    source = Column(String, nullable=False)  # file | git | chrome | vscode | terminal | project
    path = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)  # json string, free-form per event_type
    embedding = Column(Text, nullable=True)
    important = Column(Boolean, default=False)


class AccessLock(Base):
    __tablename__ = "access_lock"

    id = Column(String, primary_key=True, default=gen_id)
    pin_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)
