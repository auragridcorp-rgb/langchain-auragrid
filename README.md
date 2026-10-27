# ⚡ LangChain AurAgrid Integration

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
result = oracle_tool.invoke({"endpoint_path": "batch/ercot-lmp"})
print(result)
```

## 🔒 Features
* **L402 Lightning Native:** Handles HTTP 402 payment challenges via LND mainnet invoices.
* **Cryptographic Attestation:** Validates `X-AurAgrid-Signature` headers signed by the oracle node.
* **Affiliate Attribution:** Passes `orchestrator_pubkey` to receive 5% revenue splits upon invoice settlement.

## 🌐 Available Endpoints (22 Total)

### Retail Telemetry
* `/api/v1/esg/carbon` - Satellite-verified ESG carbon offset telemetry.
* `/api/v1/energy/grid` - Real-time energy grid frequency and renewable mix.
* `/api/v1/sar/commodities` - Synthetic aperture radar (SAR) commodity volume estimates.
* `/api/v1/maritime/congestion` - Global shipping chokepoint vessel queues and delays.
* `/api/v1/weather/micro-climate` - High-frequency pressure and wind vector telemetry.
* `/api/v1/logistics/cross-border` - Manufacturing yard density and freight velocity.

### Wholesale Batch Feeds (Institutional Tier)
* `/api/v1/batch/hyperscaler-power` - Power load predictions for AI data centers.
* `/api/v1/batch/lng-supply-chain` - Global LNG carrier fleet tracking and ETAs.
* `/api/v1/batch/crop-moisture` - Soil moisture and precipitation matrices across agricultural belts.
* `/api/v1/batch/sts-anomalies` - Open-ocean Ship-to-Ship (STS) cargo transfer tracking.
* `/api/v1/batch/maritime-weather` - Wind, wave, and swell routing optimizations for shipping fleets.
* `/api/v1/batch/curtailment-risk` - Renewable energy curtailment predictions for wind/solar.
* `/api/v1/batch/dark-fleet-matrix` - Dark fleet AIS anomaly and vessel spoofing matrix.
* `/api/v1/batch/ercot-lmp` - ERCOT 4000-Node locational marginal pricing grid.
* `/api/v1/batch/port-congestion-index` - Global maritime port congestion index.
* `/api/v1/batch/carbon-credit-audit` - Satellite carbon credit verification matrix.
* `/api/v1/batch/spr-stockpile` - Strategic Petroleum Reserve stockpile estimates.
* `/api/v1/batch/critical-minerals` - Critical minerals & rare-earth supply chain tracker.
* `/api/v1/batch/naval-escalation` - Geopolitical naval escalation risk matrix.
* `/api/v1/batch/wildfire-carbon-offset` - Wildfire risk matrix for carbon offset forests.
* `/api/v1/batch/green-compute` - Zero-carbon data center compute routing matrix.
* `/api/v1/batch/agri-yield` - Global agricultural crop yield predictor.
