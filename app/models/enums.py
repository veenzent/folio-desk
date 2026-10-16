from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    client = "client"


class ClientTier(str, Enum):
    standard = "standard"
    retainer = "retainer"
    premium = "premium"


class ProjectStatus(str, Enum):
    active = "active"
    maintenance = "maintenance"
    paused = "paused"
    archived = "archived"


class RequestType(str, Enum):
    bug = "bug"
    update = "update"
    feature = "feature"


class RequestStatus(str, Enum):
    new = "new"
    triaged = "triaged"
    in_progress = "in_progress"
    awaiting_client = "awaiting_client"
    done = "done"
    rejected = "rejected"
    cancelled = "cancelled"