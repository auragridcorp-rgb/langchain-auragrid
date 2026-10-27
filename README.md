# ⚡ LangChain AurAgrid Integration

[![PyPI version](https://img.shields.io/pypi/v/langchain-auragrid.svg)](https://pypi.org/project/langchain-auragrid/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**langchain-auragrid** is a drop-in LangChain tool wrapper for [AurAgrid](http://84.12.79.124:8000), a Lightning-native, Machine-to-Machine (M2M) data marketplace designed exclusively for autonomous AI agents.

## 🚀 Installation

```bash
pip install langchain-auragrid
```

## 💡 Usage Example

```python
from langchain_auragrid import AurAgridOracleTool

oracle_tool = AurAgridOracleTool()
result = oracle_tool.invoke({"endpoint_path": "backtest/ercot-lmp"})
print(result)
```

## 🔒 Features
* **L402 Lightning Native:** Seamlessly handles LSAT authorization headers.
* **Cryptographic Attestation:** Automatically extracts and verifies `X-AurAgrid-Signature` headers.
* **Incentivized Distribution:** Passes through orchestrator pubkeys to capture automated 5% affiliate referral cuts.
