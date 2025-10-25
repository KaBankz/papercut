"""
Pydantic models for Linear webhook payloads.
Provides type-safe access to all webhook data.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel


class Actor(BaseModel):
    """The user/integration that triggered the webhook"""

    id: str
    name: str
    email: Optional[str] = None
    url: str
    type: Optional[str] = None  # "user", "integration", "oauth_client"


class User(BaseModel):
    """A Linear user (simplified, used for assignee)"""

    id: str
    name: str
    email: str
    url: str


class IssueState(BaseModel):
    """The state/status of an issue"""

    id: str
    color: str
    name: str
    type: str  # "backlog", "unstarted", "started", "completed", "canceled"


class Team(BaseModel):
    """The team the issue belongs to"""

    id: str
    key: str
    name: str


class Label(BaseModel):
    """An issue label"""

    id: str
    color: str
    name: str


class IssueData(BaseModel):
    """The full issue data"""

    id: str
    createdAt: datetime
    updatedAt: datetime
    number: int
    title: str
    priority: int  # 0=None, 1=Urgent, 2=High, 3=Normal, 4=Low
    sortOrder: float
    prioritySortOrder: float
    slaType: str
    addedToTeamAt: datetime
    labelIds: List[str]
    teamId: str
    previousIdentifiers: List[str]
    creatorId: str
    stateId: str
    reactionData: List[dict]
    priorityLabel: str
    botActor: Optional[dict] = None
    identifier: str  # e.g., "WEB-4"
    url: str
    subscriberIds: List[str]
    state: IssueState
    team: Team
    labels: List[Label]
    description: Optional[str] = None
    descriptionData: Optional[str] = None  # JSON string with rich text format
    assigneeId: Optional[str] = None
    assignee: Optional[User] = None
    dueDate: Optional[date] = None  # ISO date string like "2025-10-26"


class LinearWebhook(BaseModel):
    """The complete Linear webhook payload"""

    action: str  # "create", "update", "remove"
    actor: Actor
    createdAt: datetime
    data: IssueData
    url: str
    type: str  # "Issue", "Comment", "Project", etc.
    organizationId: str
    webhookTimestamp: int  # Unix timestamp in milliseconds
    webhookId: str
    updatedFrom: Optional[dict] = None  # Only present for "update" actions
