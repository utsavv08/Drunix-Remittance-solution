import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Ensure root modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import RemittanceEngine, RemittanceWorkflowError
from core.compliance import ComplianceEngine, ComplianceError
from drunix.blockchain import DrunixBlockchainSim
from payment_apis.simulator import PaymentAPISimulator


class handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()

        response = {
            "status": "online",
            "service": "Drunix Cross-Border Remittance API",
            "platform": "Vercel Serverless Python",
            "endpoints": {
                "POST /api/remit": "Execute end-to-end remittance",
                "GET /api/health": "Health check"
            }
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        parsed_path = urlparse(self.path).path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(post_data)
        except Exception:
            body = {}

        sender_id = body.get("sender_id", "USR_USA_001")
        receiver_id = body.get("receiver_id", "USR_MEX_001")
        amount = float(body.get("amount", 5000.0))
        currency = body.get("currency", "USD")

        compliance = ComplianceEngine()
        blockchain = DrunixBlockchainSim()
        payment_api = PaymentAPISimulator()
        engine = RemittanceEngine(compliance, blockchain, payment_api)

        try:
            result = engine.process_remittance(sender_id, receiver_id, amount, currency)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()

            response = {
                "success": True,
                "message": "Remittance processed successfully",
                "data": result
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()

            response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
