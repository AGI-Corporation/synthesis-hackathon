#!/usr/bin/env python3
"""
AgentPass - Privacy-Preserving Agent Identity Layer
The Synthesis Hackathon 2026 | AGI Corporation

Theme: Agents that Keep Secrets
Problem: Every API call, payment, and service interaction leaks user metadata.
Solution: ZK-credential layer so agents prove authorization without revealing identity.

Stack:
- Nanobot agent framework (HKUDS)
- Self Protocol for ZK identity proofs
- ERC-8004 on-chain agent identity (Base Mainnet)
- Anthropic Claude as the reasoning backbone
"""

import os
import json
import httpx
from typing import Optional
from anthropic import Anthropic

# ─── Config ────────────────────────────────────────────────────────────────────
SYNTHESIS_BASE_URL = "https://synthesis.devfolio.co"
SYNTHESIS_API_KEY  = os.environ.get("SYNTHESIS_API_KEY", "")  # sk-synth-...
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
AGENT_NAME         = "AgentPass"
AGENT_MODEL        = "claude-sonnet-4-6"

SYSTEM_PROMPT = """
You are AgentPass, an AI agent participating in The Synthesis 2026 hackathon.
You are building privacy-preserving agentic infrastructure on Ethereum.

Your mission:
  Build a ZK-credential layer that lets AI agents prove authorization to
  third-party services without leaking the user's identity or metadata.

Capabilities:
  - Register and manage on-chain ERC-8004 agent identity on Base Mainnet
  - Generate ZK proofs via Self Protocol to authorize actions
  - Interact with the Synthesis hackathon API
  - Write smart contracts (Solidity) for credential verification
  - Log human-agent collaboration to the conversationLog field

Behavior:
  - Always keep the human in control — never act outside defined scopes
  - Prefer on-chain verification over centralized checks
  - Document every design decision in the conversation log
  - Be transparent about what data you share with external services
"""

# ─── Synthesis API Client ──────────────────────────────────────────────────────
class SynthesisClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_skill(self) -> str:
        """Fetch the hackathon skill file."""
        resp = httpx.get("https://synthesis.md/skill.md")
        resp.raise_for_status()
        return resp.text

    def register(self, payload: dict) -> dict:
        """Register the agent on-chain via ERC-8004."""
        resp = httpx.post(
            f"{SYNTHESIS_BASE_URL}/register",
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    def create_project(self, team_id: str, project: dict) -> dict:
        """Create a hackathon project under a team."""
        resp = httpx.post(
            f"{SYNTHESIS_BASE_URL}/teams/{team_id}/projects",
            headers=self.headers,
            json=project,
        )
        resp.raise_for_status()
        return resp.json()

    def update_project(self, team_id: str, project_id: str, updates: dict) -> dict:
        """Update project details (description, links, conversationLog, etc.)."""
        resp = httpx.patch(
            f"{SYNTHESIS_BASE_URL}/teams/{team_id}/projects/{project_id}",
            headers=self.headers,
            json=updates,
        )
        resp.raise_for_status()
        return resp.json()

    def submit_project(self, team_id: str, project_id: str) -> dict:
        """Publish/submit the project for judging."""
        resp = httpx.post(
            f"{SYNTHESIS_BASE_URL}/teams/{team_id}/projects/{project_id}/submit",
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()


# ─── AgentPass Core ────────────────────────────────────────────────────────────
class AgentPass:
    """
    AgentPass: ZK-Credential Layer for AI Agents.

    Allows an AI agent to prove authorization to a service by presenting
    a zero-knowledge proof of credential membership — no PII leaked.
    """

    def __init__(self):
        self.client     = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.synthesis  = SynthesisClient(SYNTHESIS_API_KEY)
        self.history    = []  # conversation history for Claude
        self.log        = []  # collaboration log for conversationLog field
        self.team_id    = os.environ.get("SYNTHESIS_TEAM_ID", "")
        self.project_id = os.environ.get("SYNTHESIS_PROJECT_ID", "")

    # ── Conversation ────────────────────────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        """Send a message to Claude and get a response."""
        self.history.append({"role": "user", "content": user_message})
        self.log.append({"role": "human", "message": user_message})

        response = self.client.messages.create(
            model=AGENT_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=self.history,
        )
        reply = response.content[0].text
        self.history.append({"role": "assistant", "content": reply})
        self.log.append({"role": "agent", "message": reply})
        return reply

    # ── ZK Credential Flow ──────────────────────────────────────────────────────
    def request_zk_proof(self, credential_type: str, service_endpoint: str) -> dict:
        """
        Request a ZK proof from Self Protocol.
        The agent proves it holds a valid credential without revealing identity.

        In production: calls Self Protocol's prover API.
        For demo: returns a mock proof structure.
        """
        print(f"[AgentPass] Requesting ZK proof for credential: {credential_type}")
        print(f"[AgentPass] Target service: {service_endpoint}")

        # Mock ZK proof structure (replace with real Self Protocol call)
        proof = {
            "type": "zk-snark",
            "credential_type": credential_type,
            "service": service_endpoint,
            "nullifier": "0x" + "ab12" * 16,      # prevents double-use
            "commitment": "0x" + "cd34" * 16,     # credential commitment
            "proof": {
                "pi_a": ["0x1...", "0x2..."],
                "pi_b": [["0x3...", "0x4..."], ["0x5...", "0x6..."]],
                "pi_c": ["0x7...", "0x8..."],
            },
            "public_inputs": [credential_type, service_endpoint],
            "verified": True,
        }
        return proof

    def verify_proof_onchain(self, proof: dict) -> dict:
        """
        Submit ZK proof to the on-chain verifier contract.
        Returns tx hash on Base Mainnet.
        """
        print("[AgentPass] Verifying proof on-chain (Base Mainnet)...")
        # In production: call the deployed AgentPassVerifier.sol contract
        return {
            "verified": True,
            "tx_hash": "0x" + "deadbeef" * 8,
            "block": 12345678,
            "network": "base-mainnet",
        }

    # ── Hackathon Integration ───────────────────────────────────────────────────
    def push_conversation_log(self):
        """Push the collaboration log to the Synthesis project."""
        if not self.team_id or not self.project_id:
            print("[AgentPass] No team/project ID set — skipping log push.")
            return
        self.synthesis.update_project(
            self.team_id,
            self.project_id,
            {"conversationLog": json.dumps(self.log, indent=2)},
        )
        print("[AgentPass] Conversation log pushed to Synthesis.")


# ─── CLI Entry Point ───────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("  AgentPass | The Synthesis 2026 | AGI Corporation")
    print("  Theme: Agents that Keep Secrets")
    print("="*60)
    print("Type 'quit' to exit. Type 'proof' to demo a ZK credential flow.")
    print()

    agent = AgentPass()

    # Prime agent with the skill file
    try:
        skill = agent.synthesis.get_skill()
        primer = f"Here is the Synthesis hackathon skill file — read it carefully:\n\n{skill}"
        reply  = agent.chat(primer)
        print(f"AgentPass: {reply}\n")
    except Exception as e:
        print(f"[Warning] Could not load skill file: {e}\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            agent.push_conversation_log()
            print("[AgentPass] Session ended. Log saved.")
            break
        if user_input.lower() == "proof":
            proof  = agent.request_zk_proof("CMMC-Level2", "https://api.example.com/verify")
            result = agent.verify_proof_onchain(proof)
            print(f"[ZK Proof Result]: {json.dumps(result, indent=2)}")
            continue

        reply = agent.chat(user_input)
        print(f"\nAgentPass: {reply}\n")


if __name__ == "__main__":
    main()
