"""Offline tests: a fake HTTP session stands in for the AurAgrid server."""
import asyncio
import json
import unittest

from langchain_auragrid import AurAgridOracleTool


class FakeResponse:
    def __init__(self, status, body=b"", headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}
        self.request = None

    def iter_content(self, _size):
        yield self._body

    def close(self):
        pass


class FakeSession:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, headers=None, **_kw):
        path = url.split("84.12.79.124", 1)[1]
        self.calls.append((path, headers or {}))
        status, body, hdrs = self.routes.get(path, (404, b"{}", {}))
        return FakeResponse(status, body, hdrs)


FEED = {"feed": "energy/grid", "stale": False, "degraded": False,
        "provenance": {"source": "U.S. EIA"}, "data": {"demand_mw": 1}}


def tool(routes, **kw):
    return AurAgridOracleTool(session=FakeSession(routes), **kw)


class ToolTests(unittest.TestCase):
    def test_free_feed_without_signature_check(self):
        t = tool({"/api/v1/energy/grid": (200, json.dumps(FEED).encode(), {})}, signing_pubkey=None)
        out = json.loads(t.invoke({"endpoint_path": "energy/grid"}))
        self.assertEqual(out["status"], "OK")
        self.assertEqual(out["data"], {"demand_mw": 1})
        self.assertFalse(out["signature_verified"])

    def test_unsigned_response_is_rejected_when_a_key_is_pinned(self):
        t = tool({"/api/v1/energy/grid": (200, json.dumps(FEED).encode(), {})})
        out = json.loads(t.invoke({"endpoint_path": "/api/v1/energy/grid"}))
        self.assertEqual(out["status"], "SIGNATURE_INVALID")
        self.assertNotIn("data", out)

    def test_paid_feed_without_wallet_returns_the_price_and_never_pays(self):
        challenge = 'L402 macaroon="AgEEbHNhdA", invoice="lnbc500n1test"'
        quote = {"price_sats": 50, "token_ttl_seconds": 3600, "tolerance_pct": 3}
        t = tool({"/api/v1/batch/btc-fees": (402, b"payment required", {"WWW-Authenticate": challenge}),
                  "/api/v1/price/batch/btc-fees": (200, json.dumps(quote).encode(), {})})
        out = json.loads(t.invoke({"endpoint_path": "batch/btc-fees"}))
        self.assertEqual((out["status"], out["price_sats"]), ("PAYMENT_REQUIRED", 50))

    def test_status_codes_are_reported(self):
        t = tool({"/api/v1/batch/ercot-lmp": (410, b"{}", {}),
                  "/api/v1/batch/earthquakes": (503, b"{}", {})}, signing_pubkey=None)
        self.assertEqual(json.loads(t.invoke({"endpoint_path": "batch/ercot-lmp"}))["status"], "RETIRED")
        self.assertEqual(json.loads(t.invoke({"endpoint_path": "batch/earthquakes"}))["status"], "UNAVAILABLE")

    def test_rejects_paths_that_leave_the_api(self):
        session = FakeSession({})
        t = AurAgridOracleTool(session=session, signing_pubkey=None)
        for bad in ("../admin", "https://evil.example/x", "batch/btc-fees?x=1", ""):
            self.assertEqual(json.loads(t.invoke({"endpoint_path": bad}))["status"], "ERROR", bad)
        self.assertEqual(session.calls, [])

    def test_wallet_requires_a_cap(self):
        t = tool({}, wallet=object())
        out = json.loads(t.invoke({"endpoint_path": "batch/btc-fees"}))
        self.assertEqual(out["status"], "ERROR")
        self.assertIn("max_sats_per_payment", out["message"])

    def test_async(self):
        t = tool({"/api/v1/energy/grid": (200, json.dumps(FEED).encode(), {})}, signing_pubkey=None)
        out = json.loads(asyncio.run(t.ainvoke({"endpoint_path": "energy/grid"})))
        self.assertEqual(out["status"], "OK")


if __name__ == "__main__":
    unittest.main()
