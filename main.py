import sys
import logging
from core.engine import RemittanceEngine
from core.compliance import ComplianceEngine
from drunix.blockchain import DrunixBlockchainSim
from payment_apis.simulator import PaymentAPISimulator

# Configure logging for the demo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RemittanceDemo")

def run_demo() -> None:
    """
    Executes the end-to-end cross-border remittance workflow demo.
    This demonstrates 
    
    payment initiation, compliance checks, escrow locking,
    simulated tracking, and final settlement on the Drunix platform.
    """
    logger.info("Starting Cross-Border Remittance Demo")
    
    # Initialize dependencies
    compliance = ComplianceEngine()
    blockchain = DrunixBlockchainSim()
    payment_api = PaymentAPISimulator()
    
    # Initialize the core remittance engine with dependencies
    engine = RemittanceEngine(
        compliance_engine=compliance,
        blockchain_sim=blockchain,
        payment_api=payment_api
    )
    
    # Demo transaction details
    sender_id = "USR_USA_001"
    receiver_id = "USR_MEX_001"
    amount = 5000.00
    source_currency = "USD"
    destination_currency = "MXN"
    
    logger.info(
        f"Initiating remittance: {amount} {source_currency} from {sender_id} "
        f"to {receiver_id} in {destination_currency}"
    )

    try:
        # Step 1: Process the remittance
        transaction_id = engine.process_remittance(
            sender_id,
            receiver_id,
            amount,
            'USD'
        )
        
        logger.info(f"Remittance processed successfully. Transaction ID: {transaction_id}")
        
        logger.info("Demo completed successfully.")

    except Exception as e:
        logger.error(f"Remittance flow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_demo()