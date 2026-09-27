import unittest
from decimal import Decimal
from core.compliance import ComplianceEngine, ComplianceError
from core.engine import RemittanceEngine, RemittanceWorkflowError
from drunix.blockchain import DrunixBlockchainSim, EscrowStatus
from payment_apis.simulator import PaymentAPISimulator, PaymentStatus
from drunix_remittance.escrow import EscrowService, EscrowError, MilestoneError
from drunix_remittance.models import Milestone
from src.utils.helpers import validate_currency_code, validate_amount, convert_currency, CurrencyValidationError
from src.drunix import DrunixPlatform
from src.core.escrow import EscrowManager, EscrowStatus as SrcEscrowStatus


class TestComplianceEngine(unittest.TestCase):
    def test_valid_compliance_check(self):
        engine = ComplianceEngine()
        self.assertTrue(engine.check_transaction("USR_001", "USR_002", 1000.0, "USD"))

    def test_blocked_user_rejection(self):
        engine = ComplianceEngine()
        with self.assertRaises(ComplianceError):
            engine.check_transaction("blacklisted_user_01", "USR_002", 500.0, "USD")

    def test_amount_exceeded_rejection(self):
        engine = ComplianceEngine()
        with self.assertRaises(ComplianceError):
            engine.check_transaction("USR_001", "USR_002", 150000.0, "USD")


class TestDrunixBlockchain(unittest.TestCase):
    def test_escrow_lifecycle(self):
        bc = DrunixBlockchainSim()
        contract_id = bc.create_escrow_contract("sender1", "receiver1", 500.0, "USD")
        self.assertTrue(contract_id.startswith("drx_esc_"))
        
        status = bc.get_contract_status(contract_id)
        self.assertEqual(status["status"], EscrowStatus.CREATED.value)

        bc.fund_escrow_contract(contract_id, 500.0)
        status = bc.get_contract_status(contract_id)
        self.assertEqual(status["status"], EscrowStatus.FUNDED.value)

        bc.disburse_escrow_contract(contract_id)
        status = bc.get_contract_status(contract_id)
        self.assertEqual(status["status"], EscrowStatus.DISBURSED.value)

    def test_escrow_refund(self):
        bc = DrunixBlockchainSim()
        contract_id = bc.create_escrow_contract("sender2", "receiver2", 250.0, "USD")
        bc.fund_escrow_contract(contract_id, 250.0)
        bc.refund_escrow_contract(contract_id)
        status = bc.get_contract_status(contract_id)
        self.assertEqual(status["status"], EscrowStatus.REFUNDED.value)


class TestRemittanceEngine(unittest.TestCase):
    def test_end_to_end_remittance_success(self):
        compliance = ComplianceEngine()
        blockchain = DrunixBlockchainSim()
        payment_api = PaymentAPISimulator()
        engine = RemittanceEngine(compliance, blockchain, payment_api)

        result = engine.process_remittance("USR_USA_001", "USR_MEX_001", 1500.0, "USD")
        self.assertIn(result["workflow_status"], ["SUCCESS", "FAILED_EXTERNAL_PAYMENT_REFUNDED"])
        self.assertIn("drunix_contract_id", result)
        self.assertEqual(result["amount"], 1500.0)

    def test_remittance_aborted_on_compliance_failure(self):
        compliance = ComplianceEngine()
        blockchain = DrunixBlockchainSim()
        payment_api = PaymentAPISimulator()
        engine = RemittanceEngine(compliance, blockchain, payment_api)

        with self.assertRaises(RemittanceWorkflowError):
            engine.process_remittance("blacklisted_user_01", "USR_MEX_001", 1000.0, "USD")


class TestMilestoneEscrowService(unittest.TestCase):
    def test_milestone_creation_and_release(self):
        service = EscrowService()
        milestones = [
            Milestone("m1", "Advance 30%", Decimal("300.00")),
            Milestone("m2", "Final 70%", Decimal("700.00")),
        ]
        escrow = service.create_escrow("esc_001", "alice", "bob", Decimal("1000.00"), "USD", milestones)
        self.assertEqual(escrow.total_amount, Decimal("1000.00"))

        service.fund_escrow("esc_001", Decimal("1000.00"))
        self.assertEqual(escrow.balance, Decimal("1000.00"))

        released = service.release_milestone("esc_001", "m1")
        self.assertEqual(released, Decimal("300.00"))
        self.assertEqual(escrow.balance, Decimal("700.00"))


class TestSrcRemittanceFlow(unittest.TestCase):
    def test_src_escrow_and_conversion(self):
        validate_currency_code("EUR")
        validate_currency_code("NGN")
        amount = validate_amount(100.0)
        converted = convert_currency(amount, "EUR", "NGN")
        self.assertGreater(float(converted), 0)

        platform = DrunixPlatform()
        platform._ledger["alice"] = 500000.0
        platform._ledger["bob"] = 0.0
        platform._ledger["escrow_account"] = 0.0

        manager = EscrowManager(platform)
        manager.create_escrow("txn_101", "alice", "bob", 100000.0, "NGN")
        self.assertEqual(manager.get_transaction_status("txn_101"), SrcEscrowStatus.HELD)

        released = manager.release_escrow("txn_101")
        self.assertTrue(released)
        self.assertEqual(platform.get_balance("bob"), 100000.0)


if __name__ == "__main__":
    unittest.main()
