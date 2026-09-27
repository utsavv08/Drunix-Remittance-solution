# Drunix Cross-Border Remittance Solution

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.md)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()

A secure, institutional-grade cross-border remittance and programmable escrow solution built on the **Drunix blockchain platform**, integrating real payment gateway simulation, automated regulatory AML/KYC compliance checks, and multi-currency settlement.

---

## 🌟 Key Features

* **Blockchain Escrow & Settlement:** Programmatically locks and disburses remittance funds using smart escrow contracts on the Drunix platform.
* **Automated Compliance Engine:** Real-time AML/KYC screening, sanction list verification, and transaction threshold monitoring.
* **Payment Gateway Integration:** Bridges external banking rails with on-chain escrow locks and disbursals.
* **Multi-Currency Conversion & Milestones:** Supports automated currency conversion with milestone-based partial/full release mechanisms.
* **Zero External Dependencies Required:** Runs out-of-the-box using standard Python 3.10+.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/utsavv08/Drunix-Remittance-solution.git
cd Drunix-Remittance-solution
```

### 2. Install Dependencies (Optional)
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Demos

### Option A: Run the End-to-End Remittance Workflow Demo
Simulates compliance screening, external payment initiation, Drunix escrow deployment, and final disbursal:
```bash
python main.py
```

### Option B: Run the Multi-Currency Escrow Demo
Simulates EUR to NGN currency conversion with automated escrow creation and delivery release:
```bash
python src/main.py
```

---

## 🧪 Running Automated Unit Tests

Run the built-in test suite covering compliance screening, blockchain escrow state transitions, and currency conversions:

```bash
python -m unittest discover -s tests -p "test_all.py"
```

---

## 📁 Repository Structure

```
Drunix-Remittance-solution/
├── core/
│   ├── compliance.py        # Regulatory screening (AML/KYC/Sanction lists)
│   └── engine.py            # Master remittance orchestration workflow
├── drunix/
│   ├── __init__.py          # Drunix platform & ledger mock interface
│   └── blockchain.py        # Drunix smart escrow contract state engine
├── drunix_remittance/
│   ├── compliance.py        # Regulatory reporting & audit reference generator
│   ├── escrow.py            # Multi-milestone escrow service
│   └── models.py            # Dataclasses & Escrow status enums
├── payment_apis/
│   └── simulator.py         # External payment gateway simulator
├── src/
│   ├── core/escrow.py       # Time-locked escrow manager with timeout release
│   ├── utils/helpers.py     # Currency validation & conversion rates
│   └── main.py              # Multi-currency cross-border demo runner
├── tests/
│   └── test_all.py          # Complete unit test suite
├── main.py                  # Primary demo entrypoint
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
