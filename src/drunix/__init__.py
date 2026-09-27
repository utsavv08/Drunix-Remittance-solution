import uuid
from typing import Dict, Any


class DrunixPlatformError(Exception):
    """Raised when an operation on the Drunix platform fails."""
    pass


class DrunixPlatform:
    """Mock interface for the Drunix platform APIs, handling ledgers and payments."""

    def __init__(self) -> None:
        self._ledger: Dict[str, float] = {}

    def get_balance(self, account_id: str) -> float:
        """
        Retrieves the current balance for an account.

        Args:
            account_id: The unique identifier for the account.

        Returns:
            The account balance.
        """
        return self._ledger.get(account_id, 0.0)

    def create_account(self, initial_balance: float = 0.0) -> str:
        """
        Creates a new account on the platform.

        Args:
            initial_balance: The opening balance for the account.

        Returns:
            The new account identifier.
        """
        account_id = str(uuid.uuid4())
        self._ledger[account_id] = initial_balance
        return account_id

    def transfer(self, source_account: str, destination_account: str, amount: float) -> bool:
        """
        Executes a transfer of funds between accounts.

        Args:
            source_account: Identifier for the source.
            destination_account: Identifier for the recipient.
            amount: Quantity to transfer.

        Raises:
            DrunixPlatformError: If balance is insufficient or account not found.

        Returns:
            True if successful.
        """
        if amount <= 0:
            raise DrunixPlatformError("Transfer amount must be positive.")

        if source_account not in self._ledger:
            raise DrunixPlatformError(f"Source account {source_account} not found.")

        if destination_account not in self._ledger:
            raise DrunixPlatformError(f"Destination account {destination_account} not found.")

        if self._ledger[source_account] < amount:
            raise DrunixPlatformError(f"Insufficient funds in account {source_account}.")

        self._ledger[source_account] -= amount
        self._ledger[destination_account] += amount
        return True


# Global mock instance for dependency injection simulation
platform_api = DrunixPlatform()