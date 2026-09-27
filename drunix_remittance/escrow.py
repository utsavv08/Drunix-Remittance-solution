from decimal import Decimal
from datetime import datetime, timezone
from drunix_remittance.models import EscrowAccount, EscrowStatus, Milestone

class EscrowError(Exception):
    """Custom exception base class for escrow related errors."""

class EscrowFundsError(EscrowError):
    """Raised when there are insufficient funds or logic errors related to funding."""

class MilestoneError(EscrowError):
    """Raised when milestone operations fail."""

class EscrowService:
    """Manages the lifecycle of an escrow account, including funding and release."""

    def __init__(self):
        # In-memory storage acting as a database for demonstration purposes.
        self._escrows: dict[str, EscrowAccount] = {}

    def create_escrow(self, escrow_id: str, sender_id: str, recipient_id: str,
                      amount: Decimal, currency: str, milestones: list[Milestone]) -> EscrowAccount:
        """
        Creates and stores a new escrow account.

        Args:
            escrow_id: Unique identifier for the escrow instance.
            sender_id: Identifier of the fund sender.
            recipient_id: Identifier of the fund recipient.
            amount: Total amount of funds to be held.
            currency: Three-letter currency code.
            milestones: List of milestone conditions for fund release.

        Returns:
            The created EscrowAccount instance.
        """
        if sum(m.amount for m in milestones) != amount:
            raise EscrowError("Sum of milestone amounts must equal total amount.")

        escrow = EscrowAccount(
            escrow_id=escrow_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            total_amount=amount,
            currency=currency,
            milestones=milestones
        )
        self._escrows[escrow_id] = escrow
        return escrow

    def get_escrow(self, escrow_id: str) -> EscrowAccount:
        """Retrieves an escrow account by its ID."""
        escrow = self._escrows.get(escrow_id)
        if not escrow:
            raise EscrowError(f"Escrow account {escrow_id} not found.")
        return escrow

    def fund_escrow(self, escrow_id: str, amount: Decimal) -> None:
        """
        Funds the secure escrow balance.

        Args:
            escrow_id: ID of the escrow.
            amount: Amount being deposited.

        Raises:
            EscrowFundsError: If amount does not match total required or already funded.
        """
        escrow = self.get_escrow(escrow_id)
        if escrow.status != EscrowStatus.PENDING:
            raise EscrowFundsError(f"Escrow cannot be funded in status {escrow.status.value}")
        if amount != escrow.total_amount:
            raise EscrowFundsError(f"Funding amount {amount} must equal total {escrow.total_amount}")

        # Simulating secure locking of funds
        escrow.balance = amount
        escrow.status = EscrowStatus.FUNDED

    def release_milestone(self, escrow_id: str, milestone_id: str) -> Decimal:
        """
        Releases funds associated with a specific completed milestone.

        Args:
            escrow_id: ID of the escrow.
            milestone_id: ID of the milestone to release.

        Returns:
            The amount released.

        Raises:
            MilestoneError: If payment is not funded, milestone not found, or already released.
        """
        escrow = self.get_escrow(escrow_id)

        if escrow.status not in (EscrowStatus.FUNDED, EscrowStatus.RELEASED_PARTIAL):
            raise MilestoneError(f"Funds not available for release in status {escrow.status.value}")

        milestone = next((m for m in escrow.milestones if m.milestone_id == milestone_id), None)
        if not milestone:
            raise MilestoneError(f"Milestone {milestone_id} not found in escrow {escrow_id}")

        if milestone.is_completed:
            raise MilestoneError(f"Milestone {milestone_id} already completed.")

        milestone.is_completed = True
        milestone.completed_at = datetime.now(timezone.utc)
        released_amount = milestone.amount

        escrow.balance -= released_amount

        # Update global status
        if all(m.is_completed for m in escrow.milestones):
            escrow.status = EscrowStatus.RELEASED_FULL
        else:
            escrow.status = EscrowStatus.RELEASED_PARTIAL

        return released_amount