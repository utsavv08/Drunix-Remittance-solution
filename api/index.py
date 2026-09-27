import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

# Ensure root modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# In-Memory Trade Deals Database
deals_db = {}

def get_default_deal():
    deal_id = "DEAL-CITI-2026-0901"
    if deal_id not in deals_db:
        deals_db[deal_id] = {
            "id": deal_id,
            "dealReference": "PO-BHARAT-PUMP-9821",
            "buyerName": "Bharat Solar Infrastructures Ltd (Mumbai, India)",
            "buyerVpa": "bharatsolar@icici",
            "buyerAddress": "0x71C836642F3eAA161E2b212f7188B60cDe2b8E11",
            "sellerName": "Nordic Turbine Technologies AG (Hamburg, Germany)",
            "sellerVpa": "nordicturbine@citibank",
            "sellerAddress": "0x94B73229b46eB8927807b5dFE3b313d4b68e98E2",
            "citiEscrowAccount": "CITI-IN-ESC-482910482",
            "currency": "MULTI",
            "totalAmountUSD": 50000.0,
            "totalAmountINR": 4212500.0,
            "fxRate": 84.25,
            "status": "CREATED",
            "rwaTokenId": 101,
            "rwaDetails": {
                "blNumber": "BL-HAPAG-2026-DEIN-4491",
                "cargoDescription": "12x High-Efficiency Industrial Solar Inverters & Turbines",
                "portOfLoading": "Port of Hamburg (DEHAM)",
                "portOfDischarge": "Nhava Sheva JNPT (INNSA)",
                "carrierName": "Hapag-Lloyd Express",
                "containerNumber": "HLXU8912401",
                "currentShipmentStatus": "ConsignmentCreated",
                "metadataHash": "ipfs://QmX9z7NqUaG4tG3E8YmK8m7B8d2W3r4J9s5F6h7g8a9b0c",
                "titleHolder": "Nordic Turbine Technologies AG"
            },
            "milestones": [
                {
                    "id": "m1",
                    "index": 0,
                    "description": "Milestone 1: 20% Advance on Purchase Order & Factory Acceptance Test",
                    "payoutPercentage": 20,
                    "payoutAmountUSD": 10000.0,
                    "payoutAmountINR": 842500.0,
                    "isCompleted": False,
                    "isReleased": False,
                    "requiredStatus": "ConsignmentCreated"
                },
                {
                    "id": "m2",
                    "index": 1,
                    "description": "Milestone 2: 30% Customs Export Clearance & On-Board Vessel e-BL Issued",
                    "payoutPercentage": 30,
                    "payoutAmountUSD": 15000.0,
                    "payoutAmountINR": 1263750.0,
                    "isCompleted": False,
                    "isReleased": False,
                    "requiredStatus": "CustomsClearedOrigin"
                },
                {
                    "id": "m3",
                    "index": 2,
                    "description": "Milestone 3: 30% Nhava Sheva Port Arrival & ICEGATE Import Customs Cleared",
                    "payoutPercentage": 30,
                    "payoutAmountUSD": 15000.0,
                    "payoutAmountINR": 1263750.0,
                    "isCompleted": False,
                    "isReleased": False,
                    "requiredStatus": "PortArrival"
                },
                {
                    "id": "m4",
                    "index": 3,
                    "description": "Milestone 4: 20% Site Delivery, IoT Sensors Signoff & DvP Title Handover",
                    "payoutPercentage": 20,
                    "payoutAmountUSD": 10000.0,
                    "payoutAmountINR": 842500.0,
                    "isCompleted": False,
                    "isReleased": False,
                    "requiredStatus": "DeliveredAndVerified"
                }
            ],
            "auditLogs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "DEAL_INITIALIZED",
                    "actor": "Bharat Solar Infrastructures Ltd",
                    "details": "Trade deal initialized with 4 milestones and linked to e-BL #BL-HAPAG-2026-DEIN-4491"
                }
            ]
        }
    return deals_db[deal_id]

# Pre-populate default deal
get_default_deal()


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
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if not path.startswith("/api"):
            rel_path = path.lstrip("/")
            if not rel_path or rel_path == "":
                rel_path = "index.html"
            
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(root_dir, "public", rel_path)
            if not os.path.exists(file_path):
                file_path = os.path.join(root_dir, rel_path)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self._send_cors_headers()
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
                return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()

        if path == "/api/health" or path == "/api":
            resp = {
                "status": "online",
                "service": "CitiFlow Escrow & Drunix Remittance Engine",
                "version": "2.0.0",
                "network": "Drunix Testnet",
                "rails": ["NPCI UPI 2.0", "e-RUPI", "Citi Treasury ISO 20022"]
            }
        elif path == "/api/deals":
            resp = list(deals_db.values())
        elif path.startswith("/api/deals/"):
            deal_id = path.split("/")[-1]
            resp = deals_db.get(deal_id, {"error": "Deal not found"})
        elif path in ["/api/citi/fx-rates", "/api/fx-rate"]:
            live_rate = 88.50
            source_info = "Citi Global Treasury FX Desk"
            try:
                import urllib.request
                req = urllib.request.Request(
                    "https://open.er-api.com/v6/latest/USD",
                    headers={"User-Agent": "CitiFlow-Treasury/2.0"}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    fx_data = json.loads(response.read().decode("utf-8"))
                    if "rates" in fx_data and "INR" in fx_data["rates"]:
                        live_rate = round(float(fx_data["rates"]["INR"]), 4)
                        source_info = "Citi Global Markets Real-Time FX Live Feed"
            except Exception as e:
                live_rate = 88.50
                source_info = f"Citi Internal Fallback FX Desk (Error: {str(e)})"

            resp = {
                "base": "USD",
                "target": "INR",
                "pair": "USD/INR",
                "spotRate": live_rate,
                "forwardHedge30Day": round(live_rate * 1.0015, 4),
                "forwardHedge90Day": round(live_rate * 1.0042, 4),
                "citiLiquiditySpread": "0.015%",
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "source": source_info,
                "status": "LIVE"
            }
        else:
            resp = list(deals_db.values())

        self.wfile.write(json.dumps(resp).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(post_data)
        except Exception:
            body = {}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()

        # 1. Create New Trade Deal
        if path == "/api/deals":
            deal_id = f"DEAL-CITI-{int(time.time()) % 1000000}"
            total_usd = float(body.get("totalAmountUSD", 50000.0))
            fx_rate = 84.25
            total_inr = total_usd * fx_rate
            buyer_name = body.get("buyerName", "Indian Importer Corp")
            seller_name = body.get("sellerName", "Global Industrial Supplier")

            new_deal = {
                "id": deal_id,
                "dealReference": body.get("dealReference", f"PO-{int(time.time()) % 100000}"),
                "buyerName": buyer_name,
                "buyerVpa": body.get("buyerVpa", "buyer@upi"),
                "buyerAddress": "0x" + uuid.uuid4().hex[:40],
                "sellerName": seller_name,
                "sellerVpa": body.get("sellerVpa", "seller@citibank"),
                "sellerAddress": "0x" + uuid.uuid4().hex[:40],
                "citiEscrowAccount": f"CITI-IN-ESC-{uuid.uuid4().hex[:9].upper()}",
                "currency": "MULTI",
                "totalAmountUSD": total_usd,
                "totalAmountINR": total_inr,
                "fxRate": fx_rate,
                "status": "CREATED",
                "rwaTokenId": int(time.time()) % 1000 + 100,
                "rwaDetails": {
                    "blNumber": f"BL-EXP-{int(time.time()) % 10000}",
                    "cargoDescription": body.get("cargoDescription", "Industrial Equipment"),
                    "portOfLoading": body.get("portOfLoading", "Port of Rotterdam (NLRTM)"),
                    "portOfDischarge": body.get("portOfDischarge", "Chennai Port (INMAA)"),
                    "carrierName": body.get("carrierName", "Maersk Line"),
                    "containerNumber": f"MSKU{int(time.time()) % 10000000}",
                    "currentShipmentStatus": "ConsignmentCreated",
                    "metadataHash": f"ipfs://Qm{uuid.uuid4().hex}",
                    "titleHolder": seller_name
                },
                "milestones": [
                    {
                        "id": "m1", "index": 0,
                        "description": "Milestone 1: 20% Advance on Purchase Order Signing",
                        "payoutPercentage": 20, "payoutAmountUSD": total_usd * 0.2, "payoutAmountINR": total_inr * 0.2,
                        "isCompleted": False, "isReleased": False, "requiredStatus": "ConsignmentCreated"
                    },
                    {
                        "id": "m2", "index": 1,
                        "description": "Milestone 2: 30% Origin Customs Export Clearance & e-BL Issued",
                        "payoutPercentage": 30, "payoutAmountUSD": total_usd * 0.3, "payoutAmountINR": total_inr * 0.3,
                        "isCompleted": False, "isReleased": False, "requiredStatus": "CustomsClearedOrigin"
                    },
                    {
                        "id": "m3", "index": 2,
                        "description": "Milestone 3: 30% Destination Port Arrival & ICEGATE Cleared",
                        "payoutPercentage": 30, "payoutAmountUSD": total_usd * 0.3, "payoutAmountINR": total_inr * 0.3,
                        "isCompleted": False, "isReleased": False, "requiredStatus": "PortArrival"
                    },
                    {
                        "id": "m4", "index": 3,
                        "description": "Milestone 4: 20% Final Inspection, IoT Signoff & DvP Title Handover",
                        "payoutPercentage": 20, "payoutAmountUSD": total_usd * 0.2, "payoutAmountINR": total_inr * 0.2,
                        "isCompleted": False, "isReleased": False, "requiredStatus": "DeliveredAndVerified"
                    }
                ],
                "auditLogs": [{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "DEAL_CREATED",
                    "actor": buyer_name,
                    "details": f"Created deal for ${total_usd:,.2f} (₹{total_inr:,.2f})"
                }]
            }
            deals_db[deal_id] = new_deal
            self.wfile.write(json.dumps(new_deal).encode("utf-8"))
            return

        deal_id = body.get("dealId", "DEAL-CITI-2026-0901")
        deal = deals_db.get(deal_id) or get_default_deal()

        # 2. NPCI UPI Intent & QR Generator
        if path == "/api/npci/upi/generate-intent":
            ref = f"UPI-DRUNIX-{uuid.uuid4().hex[:8].upper()}"
            vpa = "citiflow.escrow@citi"
            name = "CitiFlow Trade Escrow"
            amount_inr = deal["totalAmountINR"]
            tx_note = f"Escrow Lock for {deal['dealReference']}"
            upi_uri = f"upi://pay?pa={vpa}&pn={name}&mc=6012&tid={ref}&tr={ref}&tn={tx_note}&am={amount_inr}&cu=INR"
            
            resp = {
                "success": True,
                "transactionRef": ref,
                "upiUri": upi_uri,
                "amountINR": amount_inr,
                "payeeVpa": vpa,
                "payeeName": name
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # 3. NPCI UPI / Payment Verification (Fund Escrow)
        if path == "/api/npci/upi/verify-payment":
            rail = body.get("paymentRail", "UPI_APP")
            utr = body.get("utr") or f"NPCI{int(time.time() * 1000) % 1000000000000}"
            deal["status"] = "FUNDED"
            deal["fundingDetails"] = {
                "paymentRail": rail,
                "txRef": utr,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            deal["auditLogs"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "ESCROW_FUNDED_NPCI",
                "actor": deal["buyerName"],
                "details": f"Locked ₹{deal['totalAmountINR']:,.2f} (${deal['totalAmountUSD']:,.2f}) via {rail}. UTR: {utr}",
                "proofHash": f"0x{utr.encode('utf-8').hex()}"
            })
            resp = {"success": True, "message": "Funds locked via NPCI rail", "deal": deal}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # 4. Citi Corporate Escrow Deposit Lock
        if path == "/api/citi/escrow/lock-deposit":
            iso_id = f"CITI-CAMT053-{int(time.time() * 1000)}"
            deal["status"] = "FUNDED"
            deal["fundingDetails"] = {
                "paymentRail": "CITI_ESCROW_WIRE",
                "txRef": iso_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            deal["auditLogs"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "ESCROW_FUNDED_CITI_TREASURY",
                "actor": "Citi Escrow Operations",
                "details": f"Locked ${deal['totalAmountUSD']:,.2f} in Citi Escrow Vault ({deal['citiEscrowAccount']}) under ISO 20022 {iso_id}"
            })
            resp = {"success": True, "message": "Funds locked in Citi Vault", "isoMessageId": iso_id, "deal": deal}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # 5. Logistics / Customs Oracle Attestation
        if path == "/api/oracle/attest-milestone":
            m_idx = int(body.get("milestoneIndex", 0))
            if m_idx < len(deal["milestones"]):
                milestone = deal["milestones"][m_idx]
                proof_hash = f"ORACLE-ICEGATE-SIG-{uuid.uuid4().hex[:12].upper()}"
                milestone["isCompleted"] = True
                milestone["completedAt"] = datetime.now(timezone.utc).isoformat()
                milestone["verificationProof"] = proof_hash

                if deal.get("rwaDetails"):
                    deal["rwaDetails"]["currentShipmentStatus"] = milestone["requiredStatus"]
                if deal["status"] == "FUNDED":
                    deal["status"] = "IN_EXECUTION"

                deal["auditLogs"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": f"MILESTONE_{m_idx + 1}_VERIFIED",
                    "actor": "ICEGATE & Logistics Oracle",
                    "details": f"Attested milestone: {milestone['description']} with proof {proof_hash}",
                    "proofHash": proof_hash
                })
                resp = {"success": True, "proofHash": proof_hash, "deal": deal}
            else:
                resp = {"success": False, "error": "Invalid milestone index"}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # 6. Citi ISO 20022 pacs.008 Cross-Border Payout Release
        if path == "/api/citi/cross-border/payout":
            m_idx = int(body.get("milestoneIndex", 0))
            if m_idx < len(deal["milestones"]):
                milestone = deal["milestones"][m_idx]
                pacs_id = f"CITI-PACS008-XML-{int(time.time() * 1000)}"
                milestone["isReleased"] = True
                milestone["releasedAt"] = datetime.now(timezone.utc).isoformat()
                milestone["citiIsoMessageId"] = pacs_id

                deal["auditLogs"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": f"MILESTONE_{m_idx + 1}_RELEASED_CITI",
                    "actor": "Citi Treasury Gateway",
                    "details": f"Released ${milestone['payoutAmountUSD']:,.2f} (₹{milestone['payoutAmountINR']:,.2f}) to {deal['sellerName']} via ISO 20022 wire",
                    "proofHash": f"0x{pacs_id.encode('utf-8').hex()}"
                })

                # Atomic DvP check: If all released, transfer e-BL title
                if all(m["isReleased"] for m in deal["milestones"]):
                    deal["status"] = "COMPLETED"
                    if deal.get("rwaDetails"):
                        deal["rwaDetails"]["titleHolder"] = deal["buyerName"]
                        deal["rwaDetails"]["currentShipmentStatus"] = "DeliveredAndVerified"
                    deal["auditLogs"].append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action": "ATOMIC_DVP_TITLE_TRANSFERRED",
                        "actor": "Drunix Smart Escrow Contract",
                        "details": f"All milestones completed! Legal title of e-BL #{deal['rwaDetails']['blNumber']} atomically transferred to {deal['buyerName']}"
                    })

                resp = {
                    "success": True,
                    "pacs008Id": pacs_id,
                    "payoutAmountUSD": milestone["payoutAmountUSD"],
                    "payoutAmountINR": milestone["payoutAmountINR"],
                    "deal": deal
                }
            else:
                resp = {"success": False, "error": "Invalid milestone index"}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # 7. NPCI e-RUPI Purpose Voucher Issuance
        if path == "/api/npci/erupi/issue-voucher":
            m_idx = int(body.get("milestoneIndex", 0))
            if m_idx < len(deal["milestones"]):
                milestone = deal["milestones"][m_idx]
                voucher_code = f"ERUPI-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
                otp = f"{int(time.time() * 1000) % 900000 + 100000}"
                resp = {
                    "success": True,
                    "voucherCode": voucher_code,
                    "amountINR": milestone["payoutAmountINR"],
                    "amountUSD": milestone["payoutAmountUSD"],
                    "purpose": body.get("purpose", "Customs & Port Logistics Clearance"),
                    "mccCode": "4789",
                    "redemptionOtp": otp
                }
            else:
                resp = {"success": False, "error": "Invalid milestone"}
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        # Fallback to general Remittance endpoint
        resp = {"success": True, "message": "Action processed", "deal": deal}
        self.wfile.write(json.dumps(resp).encode("utf-8"))

if __name__ == "__main__":
    from http.server import HTTPServer
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"================================================================")
    print(f" 🏛️ CitiFlow Escrow — Institutional Trade Portal & API Server")
    print(f" Running at: http://localhost:{port}")
    print(f" Network: Drunix L1 Blockchain (Mock Testnet)")
    print(f" Settlement Rails: Citi ISO 20022 + NPCI UPI 2.0 / e-RUPI")
    print(f"================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CitiFlow server.")
