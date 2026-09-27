import random
import time
import uuid
from typing import Dict, Any, Optional
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class PaymentAPISimulator:
    """Simulates external payment service provider interfaces."""

    def __init__(self):
        # In-memory storage to simulate remote state
        self._transactions: Dict[str, Dict[str, Any]] = {}

    def initiate_payment(self, sender_id: str, amount: float, currency: str) -> Dict[str, Any]:
        """
        Simulates initiating a payment via an external processor.
        
        Args:
            sender_id: Identifier for the sender.
            amount: Amount to send.
            currency: Currency code.

        Returns:
            Dict containing transaction details including a tracking ID and status.
        """
        transaction_id = str(uuid.uuid4())
        
        # Simulate network latency
        time.sleep(0.1)

        # Randomly fail for simulation realism
        if random.random() < 0.05:
            status = PaymentStatus.FAILED.value
            details = "Simulated bank network error"
        else:
            status = PaymentStatus.PENDING.value
            details = "Payment initiated successfully."

        transaction_data = {
            "transaction_id": transaction_id,
            "sender_id": sender_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "details": details,
            "created_at": time.time()
        }
        
        self._transactions[transaction_id] = transaction_data
        return transaction_data

    def get_payment_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Polls the status of a specific payment.

        Args:
            transaction_id: The tracking ID of the payment.

        Returns:
            Dict with updated status or None if not found.
        """
        record = self._transactions.get(transaction_id)
        if not record:
            return None

        # Simulate state transition if PENDING
        if record["status"] == PaymentStatus.PENDING.value:
            if random.random() < 0.9:  # 90% chance to complete
                record["status"] = PaymentStatus.SUCCESS.value
                record["details"] = "Funds successfully cleared."
            else:
                record["status"] = PaymentStatus.FAILED.value
                record["details"] = "Insufficient funds or processor rejection."

        return record

    def simulate_incoming_notification(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Simulates a push notification/webhook from the external API.

        Args:
            transaction_id: The ID of the transaction to update.

        Returns:
            Notification data dict.
        """
        updated_state = self.get_payment_status(transaction_id)
        if not updated_state:
            return None

        return {
            "event": "payment_update",
            "timestamp": time.time(),
            "data": updated_state
        }

if __name__ == "__main__":
    # Self-test demonstration
    simulator = PaymentAPISimulator()
    print("Initiating payment...")
    init_res = simulator.initiate_payment("usr_123", 1500.0, "USD")
    tx_id = init_res["transaction_id"]
    print(f"Initiated: {init_res}")

    print("\nSimulating notification check...")
    notif = simulator.simulate_incoming_notification(tx_id)
    print(f"Notification received: {notif}")