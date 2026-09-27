import requests
from config import Config

class DrunixClient:
    def __init__(self):
        self.base_url = Config.DRUNIX_NODE_URL
        self.timeout = Config.DRUNIX_API_TIMEOUT

    def get_transaction_status(self, tx_hash):
        try:
            response = requests.get(f"{self.base_url}/tx/{tx_hash}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
