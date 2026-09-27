import logging
from typing import Dict, Any

from core.compliance import ComplianceEngine, ComplianceError
from drunix.blockchain import DrunixBlockchainSim, EscrowStatus
from payment_apis.simulator import PaymentAPISimulator, PaymentStatus

# Configure logging for the core engine
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('RemittanceEngine')

class RemittanceWorkflowError(Exception):
    """Exception raised when the remittance workflow fails at any stage."""
    pass

class RemittanceEngine:
    """Orchestrates the cross-border remittance workflow connecting all components."""

    def __init__(self, compliance_engine: ComplianceEngine, blockchain_sim: DrunixBlockchainSim, payment_api: PaymentAPISimulator) -> None:
        """
        Initializes the RemittanceEngine with necessary component instances.

        Args:
            compliance_engine: Instance of the ComplianceEngine.
            blockchain_sim: Instance of DrunixBlockchainSim.
            payment_api: Instance of PaymentAPISimulator.
        """
        self.compliance = compliance_engine
        self.blockchain = blockchain_sim
        self.payment_api = payment_api

    def process_remittance(self, sender_id: str, receiver_id: str, amount: float, currency: str) -> Dict[str, Any]:
        """
        Executes the full end-to-end remittance workflow.

        Args:
            sender_id: The identifier of the sender.
            receiver_id: The identifier of the receiver.
            amount: The transaction amount.
            currency: The transaction currency.

        Returns:
            Dict: Details of the finalized sequence including final status.

        Raises:
            RemittanceWorkflowError: If any stage of the workflow fails.
        """
        logger.info(f"Processing remittance: {sender_id} -> {receiver_id}, {amount} {currency}")

        # Step 1: Compliance Check
        try:
            self.compliance.check_transaction(sender_id, receiver_id, amount, currency)
            logger.info("Stage 1/4: Compliance check passed.")
        except ComplianceError as e:
            logger.error(f"Stage 1/4 Failed: Compliance rejection. {e}")
            raise RemittanceWorkflowError(f"Workflow aborted during compliance: {e}")

        # Step 2: Payment Initiation (External)
        payment_init = self.payment_api.initiate_payment(sender_id, amount, currency)
        tx_id = payment_init["transaction_id"]
        if payment_init["status"] != PaymentStatus.PENDING.value:
            logger.error(f"Stage 2/4 Failed: External payment initiation failed. Reason: {payment_init['details']}")
            raise RemittanceWorkflowError(f"Workflow aborted during payment initiation: {payment_init['details']}")
        logger.info(f"Stage 2/4: Payment initiated. Tracking ID: {tx_id}")

        # Step 3: Blockchain Escrow Creation and Funding
        try:
            contract_id = self.blockchain.create_escrow_contract(sender_id, receiver_id, amount, currency)
            self.blockchain.fund_escrow_contract(contract_id, amount)
            logger.info(f"Stage 3/4: Escrow contract {contract_id} created and funded on Drunix.")
        except Exception as e:
            logger.error(f"Stage 3/4 Failed: Blockchain interaction failure. {e}")
            raise RemittanceWorkflowError(f"Workflow aborted during blockchain escrow funding: {e}")

        # Step 4: Final Settlement / Disbursal
        # In a real workflow, polling or notifications would occur here to confirm external payment success.
        # We simulate checking status.
        payment_record = self.payment_api.get_payment_status(tx_id)
        
        # Simulate successful external processing for this demo workflow to proceed with disbursal
        if payment_record and random_success_scenario(): # Logic function defined below for simulation purposes
             payment_record["status"] = PaymentStatus.SUCCESS.value

        if payment_record and payment_record["status"] == PaymentStatus.SUCCESS.value:
            try:
                self.blockchain.disburse_escrow_contract(contract_id)
                logger.info(f"Stage 4/4: External payment succeeded. Escrow {contract_id} disbursed to recipient.")
                final_status = "SUCCESS"
            except Exception as e:
                logger.error(f"Stage 4/4 Failed: Disbursal failure. {e}")
                raise RemittanceWorkflowError(f"Workflow failed during final disbursal: {e}")
        else:
            try:
                self.blockchain.refund_escrow_contract(contract_id)
                logger.warning(f"Stage 4/4: External payment failed. Escrow {contract_id} refunded to sender.")
                final_status = "FAILED_EXTERNAL_PAYMENT_REFUNDED"
            except Exception as e:
                 logger.error(f"Stage 4/4 Critical Failure: Refund failure after external payment failure. {e}")
                 raise RemittanceWorkflowError(f"Critical workflow failure during refund process: {e}")

        return {
            "workflow_status": final_status,
            "external_tracking_id": tx_id,
            "drunix_contract_id": contract_id,
            "amount": amount,
            "currency": currency
        }

def random_success_scenario() -> bool:
    """Helper to simulate that external payment eventually succeeds in the workflow flow."""
    import random
    return random.random() > 0.01 # 99% success rate for simulation flow persistence