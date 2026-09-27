import os

class Config:
    # Blockchain Node Configuration
    DRUNIX_NODE_URL = os.getenv("DRUNIX_NODE_URL", "http://localhost:8545")
    DRUNIX_API_TIMEOUT = int(os.getenv("DRUNIX_API_TIMEOUT", "30"))

    # Gateway Configuration
    GATEWAY_MERCHANT_ID = os.getenv("GATEWAY_MERCHANT_ID", "merchant_12345")
    CURRENCY = os.getenv("CURRENCY", "USD")

    # Security Configuration
    TRANSACTION_SIGNATURE_KEY = os.getenv("TRANSACTION_SIGNATURE_KEY", "")
