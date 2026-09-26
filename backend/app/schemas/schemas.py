from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator


def _split_lines(v: Any) -> List[str]:
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    return [line for line in str(v).split("\n") if line]


class GitContextOut(BaseModel):
    repository_path: Optional[str] = None
    branch: Optional[str] = None
    last_commit_hash: Optional[str] = None
    last_commit_message: Optional[str] = None
    modified_files: List[str] = []
    untracked_files: List[str] = []

    _split_modified = field_validator("modified_files", mode="before")(_split_lines)
    _split_untracked = field_validator("untracked_files", mode="before")(_split_lines)

    class Config:
        from_attributes = True


class TerminalContextOut(BaseModel):
    working_directory: Optional[str] = None
    recent_commands: List[str] = []

    _split_commands = field_validator("recent_commands", mode="before")(_split_lines)

    class Config:
        from_attributes = True


class FileOut(BaseModel):
    path: str
    kind: str

    class Config:
        from_attributes = True


class BrowserTabOut(BaseModel):
    url: str
    title: Optional[str] = None

    class Config:
        from_attributes = True


class SnapshotOut(BaseModel):
    id: str
    project_id: str
    created_at: datetime
    trigger: str
    files: List[FileOut] = []
    browser_tabs: List[BrowserTabOut] = []
    git_context: Optional[GitContextOut] = None
    terminal_context: Optional[TerminalContextOut] = None

    class Config:
        from_attributes = True


class ProjectOut(BaseModel):
    id: str
    name: str
    path: str
    semantic_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SnapshotCreateRequest(BaseModel):
    """
    Manually trigger a snapshot for the given project path. In a real
    Windows deployment this is normally called by a local background
    checkpoint process (see services/snapshots/scheduler.py), but exposing
    it as an endpoint keeps the API testable cross-platform.
    """
    project_path: str
    trigger: str = "manual"


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3


class SearchResultItem(BaseModel):
    project: ProjectOut
    score: float
    rank: int
    breakdown: Dict[str, float]


class SearchResponse(BaseModel):
    intent: str
    query: str
    results: List[SearchResultItem]


class RestorePlanItem(BaseModel):
    component: str
    description: str
    safe: bool
    action: Dict


class RestoreRequest(BaseModel):
    project_id: str
    snapshot_id: Optional[str] = None  # defaults to latest
    confirm_unsafe: bool = False


class RestoreResponse(BaseModel):
    project_id: str
    plan: List[RestorePlanItem]
    executed: List[str]
    warnings: List[str]
    skipped_unsafe: List[RestorePlanItem]


class ChatRequest(BaseModel):
    message: str
    active_project_id: Optional[str] = None
    awaiting: Optional[str] = None
    context: Optional[Dict] = None
    unlocked: bool = False


class ChatResponse(BaseModel):
    reply: str
    active_project_id: Optional[str] = None
    active_project_path: Optional[str] = None
    awaiting: Optional[str] = None
    data: Dict = {}
    unlocked: Optional[bool] = None
