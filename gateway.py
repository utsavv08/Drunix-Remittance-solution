from config import Config

class PaymentGateway:
    def __init__(self):
        self.merchant_id = Config.GATEWAY_MERCHANT_ID
        self.currency = Config.CURRENCY

    def process_payment(self, amount, card_details):
        # In a real scenario, this would interact with the payment processor's API
        print(f"Processing payment of {amount} {self.currency} for merchant {self.merchant_id}")
        # Simulating successful payment
        return {"status": "success", "transaction_id": "gw_987654321"}
