"""
Linear webhook models.
Pydantic models for Linear webhook payloads.
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


class Project(BaseModel):
    """A Linear project"""

    id: str
    name: str
    url: str


class Milestone(BaseModel):
    """A project milestone"""

    id: str
    name: str
    targetDate: date  # ISO date string like "2025-11-20"


class IssueData(BaseModel):
    """The full issue data"""

    # Required fields (always present)
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
    identifier: str  # e.g., "WEB-4"
    url: str
    subscriberIds: List[str]

    # Nested objects (always present)
    state: IssueState
    team: Team
    labels: List[Label]

    # Optional content fields
    description: Optional[str] = None
    descriptionData: Optional[str] = None  # JSON string with rich text format
    botActor: Optional[dict] = None

    # Assignment fields
    assigneeId: Optional[str] = None
    assignee: Optional[User] = None
    delegateId: Optional[str] = None  # User delegated to
    externalUserCreatorId: Optional[str] = None  # External user who created
    snoozedById: Optional[str] = None  # User who snoozed

    # Date/time fields
    dueDate: Optional[date] = None  # ISO date string like "2025-10-26"
    archivedAt: Optional[datetime] = None
    startedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    canceledAt: Optional[datetime] = None
    autoClosedAt: Optional[datetime] = None
    autoArchivedAt: Optional[datetime] = None
    snoozedUntilAt: Optional[datetime] = None

    # Triage timing
    startedTriageAt: Optional[datetime] = None
    triagedAt: Optional[datetime] = None

    # SLA timing fields
    slaStartedAt: Optional[datetime] = None
    slaMediumRiskAt: Optional[datetime] = None
    slaHighRiskAt: Optional[datetime] = None
    slaBreachesAt: Optional[datetime] = None

    # Project/Cycle/Milestone associations
    cycleId: Optional[str] = None
    projectId: Optional[str] = None
    projectMilestoneId: Optional[str] = None
    addedToProjectAt: Optional[datetime] = None
    addedToCycleAt: Optional[datetime] = None
    project: Optional[Project] = None
    milestone: Optional[Milestone] = None

    # Issue hierarchy
    parentId: Optional[str] = None  # For sub-issues
    subIssueSortOrder: Optional[float] = None

    # Status flags
    trashed: Optional[bool] = None  # True when issue is deleted/trashed
    estimate: Optional[int] = None  # Story points or time estimate

    # Template and activity fields
    lastAppliedTemplateId: Optional[str] = None
    recurringIssueTemplateId: Optional[str] = None
    sourceCommentId: Optional[str] = None  # Comment that created this issue
    activitySummary: Optional[str] = None


class LinearWebhook(BaseModel):
    """
    Linear webhook payload for Issue events.

    Supports all webhook actions: "create", "update", "remove"
    All other webhook types are filtered out before parsing.

    See: https://linear.app/developers/webhooks#data-change-events-payload
    """

    action: str  # "create", "update", "remove"
    actor: Actor
    createdAt: datetime
    data: IssueData  # Issue data for Issue webhooks
    type: str  # "Issue", "Comment", "Project", etc.
    organizationId: str
    webhookTimestamp: int  # Unix timestamp in milliseconds
    webhookId: str
    url: Optional[str] = None  # Present for create/update, absent for remove
    updatedFrom: Optional[dict] = None  # Only present for "update" actions

    class Config:
        # Allow extra fields for different webhook types
        extra = "allow"
