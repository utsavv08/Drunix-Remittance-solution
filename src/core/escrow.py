from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional
from drunix import DrunixPlatform

class EscrowStatus(Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"

class EscrowTransaction:
    def __init__(self, transaction_id: str, sender_id: str, recipient_id: str, amount: float, currency: str, timeout_days: int = 3):
        self.transaction_id = transaction_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.amount = amount
        self.currency = currency
        self.status = EscrowStatus.PENDING
        self.created_at = datetime.utcnow()
        self.release_deadline = self.created_at + timedelta(days=timeout_days)

class EscrowManager:
    """
    Manages escrow state and automated release logic for remittance transactions.
    """

    def __init__(self, drunix_api: DrunixPlatform):
        self.drunix_api = drunix_api
        # Temporary in-memory storage, would be a database in production
        self._escrow_ledger: Dict[str, EscrowTransaction] = {}

    def create_escrow(self, transaction_id: str, sender_id: str, recipient_id: str, amount: float, currency: str) -> None:
        """
        Initializes an escrow transaction, holding funds conceptually.
        In reality, calls Drunix API to hold the user's balance.
        """
        try:
            # Simulate platform hold via mock API
            # Implicit functionality assumed based on broken source code, mapped to DrunixPlatform interface
            # Since DrunixPlatform only shows create_account, get_balance, transfer, 
            # this logic remains logically consistent with the abstraction.
            success = self.drunix_api.transfer(sender_id, "escrow_account", amount) 
            if not success:
                raise Exception(f"Insufficient funds or platform error for sender {sender_id}")

            transaction = EscrowTransaction(transaction_id, sender_id, recipient_id, amount, currency)
            transaction.status = EscrowStatus.HELD
            self._escrow_ledger[transaction_id] = transaction

        except Exception as e:
            # Log error in production
            print(f"Error creating escrow: {e}")
            raise

    def release_funds(self, transaction_id: str) -> bool:
        """
        Releases held funds to the recipient.
        """
        try:
            transaction = self._escrow_ledger.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found in escrow.")

            if transaction.status != EscrowStatus.HELD:
                raise ValueError(f"Cannot release funds for transaction {transaction_id}. Status is {transaction.status.value}")

            # Simulate platform release via mock API
            success = self.drunix_api.transfer("escrow_account", transaction.recipient_id, transaction.amount)
            if not success:
                 raise Exception("Platform funds transfer failed.")

            transaction.status = EscrowStatus.RELEASED
            return True

        except (ValueError, Exception) as e:
            # Log error in production
            print(f"Error releasing escrow {transaction_id}: {e}")
            return False

    def release_escrow(self, transaction_id: str) -> bool:
        """Alias for release_funds."""
        return self.release_funds(transaction_id)

    def refund_sender(self, transaction_id: str) -> bool:
        """
        Returns held funds back to the sender.
        """
        try:
            transaction = self._escrow_ledger.get(transaction_id)
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found in escrow.")

            if transaction.status != EscrowStatus.HELD:
                 raise ValueError(f"Cannot refund funds for transaction {transaction_id}. Status is {transaction.status.value}")

            # Simulate platform release of hold via mock API
            success = self.drunix_api.transfer("escrow_account", transaction.sender_id, transaction.amount)
            if not success:
                 raise Exception("Platform hold release failed.")

            transaction.status = EscrowStatus.REFUNDED
            return True

        except (ValueError, Exception) as e:
             # Log error in production
            print(f"Error refunding escrow {transaction_id}: {e}")
            return False

    def check_automated_releases(self) -> None:
        """
        Scans ledger for expired transactions and processes automated release or dispute handling.
        Normally ran by a scheduled job.
        """
        now = datetime.utcnow()
        for txn_id, txn in self._escrow_ledger.items():
            if txn.status == EscrowStatus.HELD and now > txn.release_deadline:
                # Automated logic here: simple release in this flow
                self.release_funds(txn_id)

    def get_transaction_status(self, transaction_id: str) -> Optional[EscrowStatus]:
        """
        Returns current status of an escrow transaction.
        """
        transaction = self._escrow_ledger.get(transaction_id)
        return transaction.status if transaction else None