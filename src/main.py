import uuid
import decimal
import logging
from typing import Dict, Any

from drunix import DrunixPlatform
from utils.helpers import (
    validate_currency_code,
    validate_amount,
    convert_currency,
    CurrencyValidationError,
)
from core.escrow import EscrowManager, EscrowStatus

# Configure basic logging for the execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RemittanceService:
    """
    Orchestrates cross-border remittance flows combining currency conversion
    and escrow mechanisms on the Drunix platform.
    """

    def __init__(self, drunix_api: DrunixPlatform):
        """
        Initializes the RemittanceService.

        Args:
            drunix_api: An instance of the Drunix platform API.
        """
        self.drunix_api = drunix_api
        self.escrow_manager = EscrowManager(drunix_api)

    def initiate_cross_border_payment(
        self,
        sender_id: str,
        recipient_id: str,
        send_amount: float,
        send_currency: str,
        receive_currency: str
    ) -> Dict[str, Any]:
        """
        Processes a remittance from initiation to escrow holding with conversion.

        Args:
            sender_id: The ID of the sending user.
            recipient_id: The ID of the receiving user.
            send_amount: The amount being sent.
            send_currency: The currency the sender is using.
            receive_currency: The currency the recipient expects.

        Returns:
            Dict containing details of the initiated transaction.

        Raises:
            CurrencyValidationError: If inputs are invalid.
            Exception: If the process fails on the platform.
        """
        logger.info(f"Initiating remittance: {sender_id} -> {recipient_id}, "
                    f"{send_amount} {send_currency} -> {receive_currency}")

        try:
            # 1. Validation
            validate_currency_code(send_currency)
            validate_currency_code(receive_currency)
            decimal_send_amount = validate_amount(send_amount)

            # 2. Conversion
            converted_amount = convert_currency(
                decimal_send_amount, send_currency, receive_currency
            )
            final_receive_amount = float(converted_amount)
            
            logger.info(f"Converted {send_amount} {send_currency} to "
                        f"{final_receive_amount} {receive_currency}")

            # 3. Create Escrow
            transaction_id = str(uuid.uuid4())
            self.escrow_manager.create_escrow(
                transaction_id,
                sender_id,
                recipient_id,
                final_receive_amount,
                receive_currency
            )

            logger.info(f"Remittance successful. Funds held in escrow: {transaction_id}")

            return {
                "transaction_id": transaction_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "send_amount": send_amount,
                "send_currency": send_currency,
                "receive_amount": final_receive_amount,
                "receive_currency": receive_currency,
                "status": "FUNDS_HELD_IN_ESCROW"
            }

        except CurrencyValidationError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Remittance initiation failed: {e}")
            raise

    def confirm_receipt_and_release(self, transaction_id: str) -> bool:
        """
        Confirms receipt and releases funds to the recipient.

        Args:
            transaction_id: The ID of the escrow transaction.

        Returns:
            bool: True if funds were released successfully.
        """
        logger.info(f"Releasing funds for transaction: {transaction_id}")
        return self.escrow_manager.release_escrow(transaction_id)

if __name__ == "__main__":
    # Mock initialization for demonstration
    mock_drunix_api = DrunixPlatform()
    remittance_service = RemittanceService(mock_drunix_api)

    try:
        # Example: Alice (EUR) sends to Bob (NGN)
        transaction_data = remittance_service.initiate_cross_border_payment(
            sender_id="alice",
            recipient_id="bob",
            send_amount=100.0,
            send_currency="EUR",
            receive_currency="NGN"
        )
        print("\nTransaction Initiated:")
        print(transaction_data)

        # Alice confirms delivery, releasing funds
        tx_id = transaction_data["transaction_id"]
        release_success = remittance_service.confirm_receipt_and_release(tx_id)
        print(f"\nFunds released successfully: {release_success}")

    except Exception as e:
        print(f"\nError processing payment: {e}")