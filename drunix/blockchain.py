import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DrunixBlockchain")

class EscrowStatus(Enum):
    """Status states for an Escrow Contract."""
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    DISBURSED = "DISBURSED"
    REFUNDED = "REFUNDED"

class EscrowContract:
    """Represents a simulated Escrow Contract on Drunix Blockchain."""

    def __init__(self, contract_id: str, sender: str, recipient: str, amount: float, currency: str):
        self.contract_id = contract_id
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.currency = currency
        self.status = EscrowStatus.CREATED
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary representation of the contract."""
        return {
            "contract_id": self.contract_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class DrunixBlockchainSim:
    """Simulates interactions with the Drunix Blockchain state."""

    def __init__(self):
        # Simulated ledger storing contracts by ID
        self._ledger: Dict[str, EscrowContract] = {}

    def create_escrow_contract(self, sender: str, recipient: str, amount: float, currency: str) -> str:
        """
        Deploys a new escrow contract to the simulated blockchain.

        Args:
            sender: The wallet address or ID of the sender.
            recipient: The wallet address or ID of the recipient.
            amount: The amount of currency to be held.
            currency: The currency symbol.

        Returns:
            The unique ID of the created contract.
        """
        contract_id = f"drx_esc_{uuid.uuid4().hex[:12]}"
        contract = EscrowContract(contract_id, sender, recipient, amount, currency)
        self._ledger[contract_id] = contract
        logger.info(f"Deployed Escrow Contract {contract_id} | Sender: {sender}, Amount: {amount} {currency}")
        return contract_id

    def fund_escrow_contract(self, contract_id, amount):
        if contract_id in self._ledger:
            self._ledger[contract_id].status = EscrowStatus.FUNDED
            self._ledger[contract_id].updated_at = datetime.utcnow()
            logger.info(f"Escrow funded: {contract_id} with {amount}")
            return True
        return False

    def disburse_escrow_contract(self, contract_id):
        if contract_id in self._ledger:
            self._ledger[contract_id].status = EscrowStatus.DISBURSED
            self._ledger[contract_id].updated_at = datetime.utcnow()
            logger.info(f"Escrow disbursed: {contract_id}")
            return True
        return False

    def refund_escrow_contract(self, contract_id):
        if contract_id in self._ledger:
            self._ledger[contract_id].status = EscrowStatus.REFUNDED
            self._ledger[contract_id].updated_at = datetime.utcnow()
            logger.info(f"Escrow refunded: {contract_id}")
            return True
        return False

    def get_contract_status(self, contract_id):
        contract = self._ledger.get(contract_id)
        if contract:
            return contract.to_dict()
        return None

    def disburse_funds(self, contract_id: str) -> bool:
        """
        Simulates releasing funds from escrow to the recipient.

        Args:
            contract_id: The ID of the contract.

        Returns:
            True if disbursement was successful, False otherwise.
        """
        contract = self._ledger.get(contract_id)
        if not contract:
            logger.error(f"Disbursement failed: Contract {contract_id} not found.")
            return False

        if contract.status != EscrowStatus.FUNDED:
            logger.error(f"Disbursement failed: Contract {contract_id} is in status {contract.status.value}, expected FUNDED.")
            return False

        contract.status = EscrowStatus.DISBURSED
        contract.updated_at = datetime.utcnow()
        logger.info(f"Contract {contract_id} successfully DISBURSED to {contract.recipient}.")
        return True

    def get_contract_details(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the details of a contract from the ledger.

        Args:
            contract_id: The ID of the contract.

        Returns:
            A dictionary of contract details if found, else None.
        """
        contract = self._ledger.get(contract_id)
        if contract:
            return contract.to_dict()
        return None

if __name__ == "__main__":
    # Internal test/demonstration of functionality
    sim = DrunixBlockchainSim()
    tx_id = sim.create_escrow_contract("user_a", "user_b", 100.0, "USD")
    print(f"Contract Created: {sim.get_contract_details(tx_id)}")
    
    sim.fund_escrow_contract(tx_id, 100.0)
    print(f"Contract Funded: {sim.get_contract_details(tx_id)}")
    
    sim.disburse_funds(tx_id)
    print(f"Contract Disbursed: {sim.get_contract_details(tx_id)}")