import pytest
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


class TestComplianceEngine:
    def test_valid_compliance_check(self):
        engine = ComplianceEngine()
        assert engine.check_transaction("USR_001", "USR_002", 1000.0, "USD") is True

    def test_blocked_user_rejection(self):
        engine = ComplianceEngine()
        with pytest.raises(ComplianceError, match="restricted"):
            engine.check_transaction("USR_BLOCKED_99", "USR_002", 500.0, "USD")

    def test_amount_exceeded_rejection(self):
        engine = ComplianceEngine()
        with pytest.raises(ComplianceError, match="Limit exceeded"):
            engine.check_transaction("USR_001", "USR_002", 100000.0, "USD")


class TestDrunixBlockchain:
    def test_escrow_lifecycle(self):
        bc = DrunixBlockchainSim()
        contract_id = bc.create_escrow_contract("sender1", "receiver1", 500.0, "USD")
        assert contract_id.startswith("drx_esc_")
        
        status = bc.get_contract_status(contract_id)
        assert status["status"] == EscrowStatus.CREATED.value

        bc.fund_escrow_contract(contract_id, 500.0)
        status = bc.get_contract_status(contract_id)
        assert status["status"] == EscrowStatus.FUNDED.value

        bc.disburse_escrow_contract(contract_id)
        status = bc.get_contract_status(contract_id)
        assert status["status"] == EscrowStatus.DISBURSED.value

    def test_escrow_refund(self):
        bc = DrunixBlockchainSim()
        contract_id = bc.create_escrow_contract("sender2", "receiver2", 250.0, "USD")
        bc.fund_escrow_contract(contract_id, 250.0)
        bc.refund_escrow_contract(contract_id)
        status = bc.get_contract_status(contract_id)
        assert status["status"] == EscrowStatus.REFUNDED.value


class TestRemittanceEngine:
    def test_end_to_end_remittance_success(self):
        compliance = ComplianceEngine()
        blockchain = DrunixBlockchainSim()
        payment_api = PaymentAPISimulator()
        engine = RemittanceEngine(compliance, blockchain, payment_api)

        result = engine.process_remittance("USR_USA_001", "USR_MEX_001", 1500.0, "USD")
        assert result["workflow_status"] in ["SUCCESS", "FAILED_EXTERNAL_PAYMENT_REFUNDED"]
        assert "drunix_contract_id" in result
        assert result["amount"] == 1500.0

    def test_remittance_aborted_on_compliance_failure(self):
        compliance = ComplianceEngine()
        blockchain = DrunixBlockchainSim()
        payment_api = PaymentAPISimulator()
        engine = RemittanceEngine(compliance, blockchain, payment_api)

        with pytest.raises(RemittanceWorkflowError):
            engine.process_remittance("USR_BLOCKED", "USR_MEX_001", 1000.0, "USD")


class TestMilestoneEscrowService:
    def test_milestone_creation_and_release(self):
        service = EscrowService()
        milestones = [
            Milestone("m1", "Advance 30%", Decimal("300.00")),
            Milestone("m2", "Final 70%", Decimal("700.00")),
        ]
        escrow = service.create_escrow("esc_001", "alice", "bob", Decimal("1000.00"), "USD", milestones)
        assert escrow.total_amount == Decimal("1000.00")

        service.fund_escrow("esc_001", Decimal("1000.00"))
        assert escrow.balance == Decimal("1000.00")

        released = service.release_milestone("esc_001", "m1")
        assert released == Decimal("300.00")
        assert escrow.balance == Decimal("700.00")


class TestSrcRemittanceFlow:
    def test_src_escrow_and_conversion(self):
        validate_currency_code("EUR")
        validate_currency_code("NGN")
        amount = validate_amount(100.0)
        converted = convert_currency(amount, "EUR", "NGN")
        assert float(converted) > 0

        platform = DrunixPlatform()
        platform._ledger["alice"] = 500000.0
        platform._ledger["bob"] = 0.0
        platform._ledger["escrow_account"] = 0.0

        manager = EscrowManager(platform)
        manager.create_escrow("txn_101", "alice", "bob", 100000.0, "NGN")
        assert manager.get_transaction_status("txn_101") == SrcEscrowStatus.HELD

        released = manager.release_escrow("txn_101")
        assert released is True
        assert platform.get_balance("bob") == 100000.0
