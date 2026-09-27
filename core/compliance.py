import logging

# Configure logging for the compliance module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('compliance')

class ComplianceError(Exception):
    """Exception raised when a compliance check fails."""
    pass

class ComplianceEngine:
    """Mock Regulatory Compliance Engine for screening transactions."""

    def __init__(self) -> None:
        # Simple hardcoded mock list for demonstration purposes
        self._sanctioned_users = {"blacklisted_user_01", "fraud_account_99", "blocked_entity_x"}

    def check_transaction(self, sender_id: str, receiver_id: str, amount: float, currency: str) -> bool:
        """
        Simulate regulatory checks (AML/KYC/Sanctions) on a transaction.

        Args:
            sender_id: The ID of the transaction sender.
            receiver_id: The ID of the transaction receiver.
            amount: The transaction amount.
            currency: The transaction currency.

        Returns:
            bool: True if the transaction passes compliance.

        Raises:
            ComplianceError: If the transaction fails compliance check.
        """
        logger.info(f"Initiating compliance check for TX: {sender_id} -> {receiver_id}, Amount: {amount} {currency}")

        # Simulating basic sanction screening
        if sender_id in self._sanctioned_users:
            message = f"Compliance Rejected: Sender {sender_id} is on a sanctioned list."
            logger.warning(message)
            raise ComplianceError(message)

        if receiver_id in self._sanctioned_users:
            message = f"Compliance Rejected: Receiver {receiver_id} is on a sanctioned list."
            logger.warning(message)
            raise ComplianceError(message)

        # Simulating transaction amount limits (e.g., triggering enhanced review)
        if amount > 100000.0:
            message = f"Compliance Rejected: Amount {amount} {currency} exceeds immediate processing threshold ($100,000)."
            logger.warning(message)
            raise ComplianceError(message)

        logger.info(f"Compliance Passed for TX: {sender_id} -> {receiver_id}")
        return True

if __name__ == "__main__":
    # Small demo to test compliance logic in isolation
    engine = ComplianceEngine()
    
    # Test pass case
    try:
        engine.check_transaction("alice_01", "bob_02", 5000.0, "USD")
        print("Test 1 Passed: Valid transaction cleared.")
    except ComplianceError as e:
        print(f"Test 1 Failed: {e}")

    # Test failure case: Sanctioned sender
    try:
        engine.check_transaction("blacklisted_user_01", "bob_02", 5000.0, "USD")
        print("Test 2 Failed: Should have caught sanctioned sender.")
    except ComplianceError as e:
        print(f"Test 2 Passed: Correctly blocked sanctioned sender: {e}")

    # Test failure case: Amount limit
    try:
        engine.check_transaction("alice_01", "bob_02", 150000.0, "USD")
        print("Test 3 Failed: Should have caught excessive amount.")
    except ComplianceError as e:
        print(f"Test 3 Passed: Correctly blocked excessive amount: {e}")