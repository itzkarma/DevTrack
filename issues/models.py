"""OOP domain models for DevTrack.

These are plain Python classes (not Django ORM models). Data is persisted to
JSON files; these classes encapsulate validation and serialization behaviour.
"""

from abc import ABC, abstractmethod
from datetime import datetime


# Allowed values, defined once so views and models stay in sync.
ISSUE_STATUSES = ('open', 'in_progress', 'resolved', 'closed')
ISSUE_PRIORITIES = ('low', 'medium', 'high', 'critical')


class BaseEntity(ABC):
    """Abstract base shared by every persisted entity.

    Subclasses must implement ``validate``. ``to_dict`` serializes whatever
    instance attributes were set in ``__init__`` into a plain dict ready for
    JSON storage / a JsonResponse.
    """

    @abstractmethod
    def validate(self):
        """Raise ValueError if the instance fails business-rule checks."""

    def to_dict(self):
        """Serialize instance attributes to a plain dict for JSON storage."""
        return dict(self.__dict__)


class Reporter(BaseEntity):
    """A person who files issues."""

    def __init__(self, entity_id, name, email, team):
        self.id = entity_id
        self.name = name
        self.email = email
        self.team = team

    def validate(self):
        if not self.name:
            raise ValueError('Name cannot be empty')
        if not self.email or '@' not in self.email:
            raise ValueError('Invalid email')
        if not self.team:
            raise ValueError('Team cannot be empty')


class Issue(BaseEntity):
    """A bug report or task filed by a Reporter (1 Reporter -> many Issues)."""

    # An Issue genuinely has six independent fields; grouping them into a
    # container would only obscure the data model.
    def __init__(self, entity_id, title, description, status, priority, reporter_id):  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self.id = entity_id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.reporter_id = reporter_id
        # Brief: optional, use str(datetime.now())
        self.created_at = str(datetime.now())

    def validate(self):
        if not self.title:
            raise ValueError('Title cannot be empty')
        if self.status not in ISSUE_STATUSES:
            raise ValueError(
                'Status must be one of: ' + ', '.join(ISSUE_STATUSES)
            )
        if self.priority not in ISSUE_PRIORITIES:
            raise ValueError(
                'Priority must be one of: ' + ', '.join(ISSUE_PRIORITIES)
            )

    def describe(self):
        """Return a short human-readable summary of this issue."""
        return f"{self.title} [{self.priority}]"


class CriticalIssue(Issue):
    """Critical-priority issue with an urgent description."""

    def describe(self):
        return f"[URGENT] {self.title} — needs immediate attention"


class LowPriorityIssue(Issue):
    """Low-priority issue with a relaxed description."""

    def describe(self):
        return f"{self.title} — low priority, handle when free"
