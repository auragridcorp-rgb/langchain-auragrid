"""Verification half of AurAgrid's attestation.py (pure Python, no dependencies).

Copied verbatim from https://github.com/auragridcorp-rgb/auragrid (attestation.py,
everything above "Server side: v2 signing"); keep them in sync. It recovers the
public key from an LND `signmessage` signature and compares it to a key pinned
out-of-band. See the upstream module docstring for the v1/v2 schemes.
"""
import asyncio
import base64
import hashlib
import hmac
import logging
import re
import secrets
import sys
import time
from typing import Callable, Optional

log = logging.getLogger("auragrid.attestation")

LND_MESSAGE_PREFIX = b"Lightning Signed Message:"
V1_PREFIX = "auragrid_attest_"
V2_TAG = "auragrid_attest_v2"
SIG_HEADER_V1 = "X-AurAgrid-Signature"
SIG_HEADER_V2 = "X-AurAgrid-Signature-V2"
TIMESTAMP_HEADER = "X-AurAgrid-Timestamp"
NONCE_HEADER = "X-AurAgrid-Nonce"
PUBKEY_HEADER = "X-AurAgrid-PubKey"
_NONCE_OK = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

# ---------------------------------------------------------------------------
# secp256k1 (verification only; no secrets are handled here)
# ---------------------------------------------------------------------------
P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)
_INF = (0, 1, 0)  # Jacobian point at infinity (Z == 0)


def _double(pt):
    x, y, z = pt
    if z == 0 or y == 0:
        return _INF
    s = 4 * x * y * y % P
    m = 3 * x * x % P
    x3 = (m * m - 2 * s) % P
    y3 = (m * (s - x3) - 8 * pow(y, 4, P)) % P
    return (x3, y3, 2 * y * z % P)


def _add(p1, p2):
    if p1[2] == 0:
        return p2
    if p2[2] == 0:
        return p1
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    z1z1, z2z2 = z1 * z1 % P, z2 * z2 % P
    u1, u2 = x1 * z2z2 % P, x2 * z1z1 % P
    s1, s2 = y1 * z2 * z2z2 % P, y2 * z1 * z1z1 % P
    if u1 == u2:
        return _double(p1) if s1 == s2 else _INF
    h, r = (u2 - u1) % P, (s2 - s1) % P
    h2 = h * h % P
    h3 = h * h2 % P
    v = u1 * h2 % P
    x3 = (r * r - h3 - 2 * v) % P
    y3 = (r * (v - x3) - s1 * h3) % P
    return (x3, y3, h * z1 * z2 % P)


def _mul(k: int, pt):
    acc = _INF
    for bit in bin(k % N)[2:]:
        acc = _double(acc)
        if bit == "1":
            acc = _add(acc, pt)
    return acc


def _affine(pt):
    x, y, z = pt
    if z == 0:
        return None
    zi = pow(z, -1, P)
    return (x * zi * zi % P, y * zi * zi * zi % P)


def _recover(e: int, r: int, s: int, recid: int):
    """Recover the public key point from an ECDSA signature, or None."""
    if not (1 <= r < N and 1 <= s < N and 0 <= recid <= 3):
        return None
    x = r + (recid >> 1) * N
    if x >= P:
        return None
    rhs = (pow(x, 3, P) + 7) % P
    y = pow(rhs, (P + 1) // 4, P)
    if y * y % P != rhs:
        return None
    if (y & 1) != (recid & 1):
        y = P - y
    r_inv = pow(r, -1, N)
    q = _add(_mul(s * r_inv % N, (x, y, 1)), _mul((-e * r_inv) % N, (G[0], G[1], 1)))
    return _affine(q)


def _compress(point) -> bytes:
    x, y = point
    return bytes([2 + (y & 1)]) + x.to_bytes(32, "big")


# ---------------------------------------------------------------------------
# LND signmessage format
# ---------------------------------------------------------------------------
_ZB32 = "ybndrfg8ejkmcpqxot1uwisza345h769"


def zbase32_decode(text: str) -> bytes:
    bits = 0
    nbits = 0
    out = bytearray()
    for ch in text.strip().lower():
        idx = _ZB32.find(ch)
        if idx < 0:
            raise ValueError("invalid zbase32 character")
        bits = (bits << 5) | idx
        nbits += 5
        if nbits >= 8:
            nbits -= 8
            out.append((bits >> nbits) & 0xFF)
            bits &= (1 << nbits) - 1
    return bytes(out)


def zbase32_encode(data: bytes) -> str:
    bits = 0
    nbits = 0
    out = []
    for byte in data:
        bits = (bits << 8) | byte
        nbits += 8
        while nbits >= 5:
            nbits -= 5
            out.append(_ZB32[(bits >> nbits) & 31])
            bits &= (1 << nbits) - 1
    if nbits:
        out.append(_ZB32[(bits << (5 - nbits)) & 31])
    return "".join(out)


def message_digest(message) -> bytes:
    data = message.encode("utf-8") if isinstance(message, str) else bytes(message)
    return hashlib.sha256(hashlib.sha256(LND_MESSAGE_PREFIX + data).digest()).digest()


def recover_pubkey(message, signature_zbase32: str) -> Optional[bytes]:
    """33-byte compressed public key that signed `message`, or None if malformed."""
    try:
        raw = zbase32_decode(signature_zbase32)
    except ValueError:
        return None
    if len(raw) != 65 or not 31 <= raw[0] <= 34:      # LND signs with compressed keys
        return None
    recid = raw[0] - 31
    r, s = int.from_bytes(raw[1:33], "big"), int.from_bytes(raw[33:], "big")
    point = _recover(int.from_bytes(message_digest(message), "big"), r, s, recid)
    return _compress(point) if point else None


def verify_message(message, signature_zbase32: str, pubkey_hex: str) -> bool:
    try:
        expected = bytes.fromhex(pubkey_hex.strip())
    except ValueError:
        return False
    recovered = recover_pubkey(message, signature_zbase32 or "")
    return recovered is not None and hmac.compare_digest(recovered, expected)


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------
def v1_message(path: str) -> str:
    return V1_PREFIX + path


def v2_message(method: str, target: str, body: bytes, timestamp: int, nonce: Optional[str]) -> str:
    return "\n".join([V2_TAG, method.upper(), target, hashlib.sha256(body).hexdigest(),
                      str(int(timestamp)), nonce or "-"])


# ---------------------------------------------------------------------------
# Client side: verifier for AurAgridClient(verify_signature=...)
# ---------------------------------------------------------------------------
def make_verifier(pubkey_hex: str, scheme: str = "v2", *, max_skew_seconds: int = 120,
                  allow_weak_v1: bool = False, clock: Callable[[], float] = time.time):
    """Build verify_signature(body, headers, context) -> bool for the client.

    pubkey_hex must be pinned out-of-band. context = {"method", "target",
    "path", "nonce"} describes the request the client actually sent.
    """
    pinned = pubkey_hex.strip().lower()
    if len(pinned) != 66 or pinned[:2] not in ("02", "03"):
        raise ValueError("pubkey_hex must be a 33-byte compressed public key in hex")
    if scheme not in ("v1", "v2"):
        raise ValueError("scheme must be 'v1' or 'v2'")
    if scheme == "v1" and not allow_weak_v1:
        raise ValueError("v1 signs only the path and does not authenticate the response body; "
                         "pass allow_weak_v1=True to use it anyway, or move to v2")

    def verify(body: bytes, headers, context: dict) -> bool:
        advertised = headers.get(PUBKEY_HEADER)
        if advertised and advertised.strip().lower() != pinned:
            log.warning("Response advertises a different signing key than the pinned one")
            return False
        if scheme == "v1":
            signature = headers.get(SIG_HEADER_V1)
            return bool(signature) and verify_message(v1_message(context["path"]), signature, pinned)

        signature, stamp = headers.get(SIG_HEADER_V2), headers.get(TIMESTAMP_HEADER)
        if not signature or not stamp:
            return False
        try:
            timestamp = int(stamp)
        except ValueError:
            return False
        if abs(clock() - timestamp) > max_skew_seconds:
            log.warning("Attestation timestamp outside the allowed %ss window", max_skew_seconds)
            return False
        message = v2_message(context["method"], context["target"], body, timestamp, context["nonce"])
        return verify_message(message, signature, pinned)

    return verify
