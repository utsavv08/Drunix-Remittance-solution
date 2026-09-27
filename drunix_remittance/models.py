import enum
from datetime import datetime
from dataclasses import dataclass, field
from decimal import Decimal

class EscrowStatus(enum.Enum):
    """Enumeration of possible statuses for an Escrow transaction."""
    PENDING = "PENDING"
    FUNDED = "FUNDED"
    RELEASED_PARTIAL = "RELEASED_PARTIAL"
    RELEASED_FULL = "RELEASED_FULL"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"

@dataclass
class Milestone:
    """Represents a specific condition or phase for fund release."""
    milestone_id: str
    description: str
    amount: Decimal
    is_completed: bool = False
    completed_at: datetime | None = None

@dataclass
class EscrowAccount:
    """Represents an escrow agreement holding funds securely."""
    escrow_id: str
    sender_id: str
    recipient_id: str
    total_amount: Decimal
    currency: str
    milestones: list[Milestone]
    status: EscrowStatus = EscrowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    balance: Decimal = Decimal('0.00')

@dataclass
class RemittanceRecord:
    """Record of a cross-border remittance transaction."""
    transaction_id: str
    sender_id: str
    recipient_id: str
    amount: Decimal
    currency: str
    escrow_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)