#!/usr/bin/env python3
"""
self_protocol.py - Self Protocol ZK Proof Integration
Generate and verify zero-knowledge proofs for credential authorization.

Self Protocol: https://self.xyz
Docs: https://docs.self.xyz/
"""

import os
import json
import httpx
from typing import Dict, Optional

SELF_API_BASE = "https://api.self.xyz/v1"
SELF_API_KEY  = os.environ.get("SELF_PROTOCOL_API_KEY", "")
SELF_APP_ID   = os.environ.get("SELF_PROTOCOL_APP_ID", "")


class SelfProtocolClient:
    """
    Client for Self Protocol ZK proof generation and verification.
    Wraps Self Protocol's prover API.
    """

    def __init__(self, api_key: str = SELF_API_KEY, app_id: str = SELF_APP_ID):
        self.api_key = api_key
        self.app_id  = app_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }

    # ── Credential Issuance ──────────────────────────────────────────────────────

    def issue_credential(self, user_id: str, credential_type: str, claims: Dict) -> Dict:
        """
        Issue a credential to a user.
        In production: called by the credential issuer (e.g. compliance authority).
        Returns credential_id and signature.
        """
        payload = {
            "app_id":     self.app_id,
            "user_id":    user_id,
            "cred_type":  credential_type,
            "claims":     claims,
            "expires_at": None,  # optional
        }
        resp = httpx.post(
            f"{SELF_API_BASE}/credentials",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ── ZK Proof Generation ──────────────────────────────────────────────────────

    def generate_proof(
        self,
        credential_id: str,
        service_endpoint: str,
        challenge: Optional[str] = None,
    ) -> Dict:
        """
        Generate a ZK proof (Groth16/PLONK) for a credential.
        Proves: "I hold credential_id without revealing my identity."

        Returns:
          {
            "type": "zk-snark",
            "nullifier": "0x...",       # prevents double-use
            "commitment": "0x...",      # credential commitment
            "proof": { "pi_a": [...], "pi_b": [...], "pi_c": [...] },
            "public_inputs": [...],
            "verified": false,
          }
        """
        payload = {
            "credential_id":    credential_id,
            "service_endpoint": service_endpoint,
            "challenge":        challenge or "",
        }
        resp = httpx.post(
            f"{SELF_API_BASE}/proofs/generate",
            headers=self.headers,
            json=payload,
            timeout=60,  # proof generation can take time
        )
        resp.raise_for_status()
        return resp.json()

    # ── Verification (off-chain, for testing) ────────────────────────────────────

    def verify_proof_offchain(self, proof: Dict) -> bool:
        """
        Verify a proof off-chain via Self Protocol's verifier.
        On-chain verification happens via AgentPassVerifier.sol on Base.
        """
        resp = httpx.post(
            f"{SELF_API_BASE}/proofs/verify",
            headers=self.headers,
            json=proof,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("verified", False)


# ── Mock Mode (if no API key) ────────────────────────────────────────────────────

class MockSelfProtocol:
    """
    Mock Self Protocol client for local dev/testing.
    Returns fake ZK proofs with same structure.
    """

    def issue_credential(self, user_id: str, credential_type: str, claims: Dict) -> Dict:
        import hashlib
        cred_id = hashlib.sha256(f"{user_id}{credential_type}".encode()).hexdigest()
        return {
            "credential_id": cred_id,
            "user_id":       user_id,
            "cred_type":     credential_type,
            "claims":        claims,
            "signature":     "0x" + "mock" * 16,
        }

    def generate_proof(self, credential_id: str, service_endpoint: str, challenge: Optional[str] = None) -> Dict:
        import hashlib
        nullifier  = "0x" + hashlib.sha256(f"{credential_id}{service_endpoint}".encode()).hexdigest()
        commitment = "0x" + hashlib.sha256(credential_id.encode()).hexdigest()

        return {
            "type":        "zk-snark",
            "nullifier":   nullifier,
            "commitment":  commitment,
            "proof": {
                "pi_a": ["0x1...", "0x2..."],
                "pi_b": [["0x3...", "0x4..."], ["0x5...", "0x6..."]],
                "pi_c": ["0x7...", "0x8..."],
            },
            "public_inputs": [credential_id, service_endpoint],
            "verified":      False,  # not yet verified on-chain
        }

    def verify_proof_offchain(self, proof: Dict) -> bool:
        # Mock: always returns true
        return True


# ── Factory ──────────────────────────────────────────────────────────────────────

def get_client() -> SelfProtocolClient:
    """
    Return SelfProtocolClient if API key is set, otherwise MockSelfProtocol.
    """
    if SELF_API_KEY and SELF_APP_ID:
        print("[Self Protocol] Using live API")
        return SelfProtocolClient()
    else:
        print("[Self Protocol] Using mock mode (no API key set)")
        return MockSelfProtocol()


if __name__ == "__main__":
    # Demo usage
    client = get_client()

    # 1. Issue a credential
    cred = client.issue_credential(
        user_id="agent-123",
        credential_type="CMMC-Level2",
        claims={"org": "AGI Corporation", "level": 2, "expires": "2027-01-01"},
    )
    print(f"Credential issued: {cred['credential_id']}")

    # 2. Generate ZK proof
    proof = client.generate_proof(
        credential_id=cred["credential_id"],
        service_endpoint="https://api.example.com/verify",
    )
    print(f"ZK Proof generated: nullifier={proof['nullifier'][:18]}...")

    # 3. Verify off-chain
    verified = client.verify_proof_offchain(proof)
    print(f"Off-chain verification: {verified}")
