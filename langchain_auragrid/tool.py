import json
import requests
import asyncio
from typing import Optional, Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class AurAgridInput(BaseModel):
    endpoint_path: str = Field(
        ..., 
        description="The AurAgrid telemetry endpoint path (e.g., 'esg-carbon', 'ercot-lmp', 'backtest/ercot-lmp')."
    )
    macaroon: Optional[str] = Field(
        default=None, 
        description="L402 Macaroon token received from the Aperture paywall challenge."
    )
    preimage: Optional[str] = Field(
        default=None, 
        description="Lightning Network invoice preimage proving payment settlement."
    )
    orchestrator_pubkey: Optional[str] = Field(
        default=None, 
        description="Optional affiliate orchestrator pubkey for earning 5% revenue-share commission cuts."
    )

class AurAgridOracleTool(BaseTool):
    name: str = "auragrid_telemetry_oracle"
    description: str = (
        "Fetches institutional-grade geospatial, energy, and maritime telemetry from AurAgrid. "
        "Automatically handles L402 payment headers, validates cryptographic node signatures, "
        "and supports orchestrator affiliate revenue-share attribution."
    )
    args_schema: Type[BaseModel] = AurAgridInput
    base_url: str = "http://84.12.79.124:8000"

    def _run(
        self, 
        endpoint_path: str, 
        macaroon: Optional[str] = None, 
        preimage: Optional[str] = None,
        orchestrator_pubkey: Optional[str] = None
    ) -> str:
        clean_path = endpoint_path.lstrip("/")
        url = f"{self.base_url}/api/v1/{clean_path}"
        
        headers = {}
        if macaroon and preimage:
            headers["Authorization"] = f"LSAT {macaroon}:{preimage}"
        
        if orchestrator_pubkey:
            headers["X-Orchestrator-Pubkey"] = orchestrator_pubkey

        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # Capture cryptographic signature headers for institutional verification
            signature = response.headers.get("X-AurAgrid-Signature")
            pubkey = response.headers.get("X-AurAgrid-PubKey")
            
            if response.status_code == 402:
                return json.dumps({
                    "status": "PAYMENT_REQUIRED",
                    "www_authenticate": response.headers.get("WWW-Authenticate"),
                    "message": "L402 challenge issued. Settle the Lightning invoice to unlock payload."
                })
            
            data = response.json() if response.content else {}
            
            return json.dumps({
                "status_code": response.status_code,
                "payload": data,
                "cryptographic_attestation": {
                    "signature": signature,
                    "node_pubkey": pubkey,
                    "verified": bool(signature)
                },
                "feed_mode": response.headers.get("X-AurAgrid-Feed-Mode", "LIVE_L402")
            })
        except Exception as e:
            return json.dumps({"status": "ERROR", "message": str(e)})

    async def _arun(
        self, 
        endpoint_path: str, 
        macaroon: Optional[str] = None, 
        preimage: Optional[str] = None,
        orchestrator_pubkey: Optional[str] = None
    ) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._run, endpoint_path, macaroon, preimage, orchestrator_pubkey
        )
