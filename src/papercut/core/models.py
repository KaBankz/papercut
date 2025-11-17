"""
Platform-agnostic ticket/issue models.
These models work across Linear, Jira, GitHub Issues, etc.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class Ticket(BaseModel):
    """
    Platform-agnostic ticket/issue model.

    This is the common format that all platform adapters convert to.
    """

    id: str
    identifier: str  # e.g., "WEB-17", "JIRA-123"
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assignee: Optional[str] = None
    labels: List[str] = []
    created_at: datetime
    created_by: str
    team: str
    due_date: Optional[date] = None
    url: str
    project: Optional[str] = None
    milestone: Optional[str] = None
    milestone_date: Optional[date] = None
