#!/usr/bin/env python3
"""
register.py - Register AgentPass on The Synthesis platform

Usage:
    python register.py

This script:
  1. Collects human info (or reads from .env)
  2. Calls POST /register on synthesis.devfolio.co
  3. Saves apiKey, participantId, teamId to .env.local
  4. Prints the on-chain ERC-8004 transaction link
"""

import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

SYNTHESIS_BASE_URL = "https://synthesis.devfolio.co"


def register():
    print("\n" + "="*60)
    print("  AgentPass x The Synthesis 2026 — Registration")
    print("="*60 + "\n")

    # Read from env if available, otherwise prompt
    human_name   = os.environ.get("HUMAN_NAME")   or input("Your full name: ").strip()
    human_email  = os.environ.get("HUMAN_EMAIL")  or input("Your email: ").strip()
    human_handle = os.environ.get("HUMAN_HANDLE") or input("Twitter/Farcaster handle (optional): ").strip()
    problem      = os.environ.get("HUMAN_PROBLEM") or input(
        "What problem are you solving with this project?\n> "
    ).strip()

    payload = {
        "name": "AgentPass",
        "description": (
            "A ZK-credential layer for AI agents. Agents prove authorization "
            "to services without leaking user identity or metadata. "
            "Built on ERC-8004 (Base Mainnet) + Self Protocol."
        ),
        "image": "https://raw.githubusercontent.com/AGI-Corporation/synthesis-hackathon/main/assets/agentpass-logo.png",
        "agentHarness": "claude-code",
        "model": "claude-sonnet-4-6",
        "humanInfo": {
            "name": human_name,
            "email": human_email,
            "socialMediaHandle": human_handle,
            "background": "Founder",
            "cryptoExperience": "a little",
            "aiAgentExperience": "yes",
            "codingComfort": 9,
            "problemToSolve": problem,
        },
    }

    print("\n[AgentPass] Registering on The Synthesis (ERC-8004 on Base)...")

    try:
        resp = httpx.post(
            f"{SYNTHESIS_BASE_URL}/register",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] Registration failed: {e.response.status_code}")
        print(e.response.text)
        return
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    api_key        = data.get("apiKey", "")
    participant_id = data.get("participantId", "")
    team_id        = data.get("teamId", "")
    tx_link        = data.get("registrationTxn", "")

    print("\n" + "="*60)
    print("  Registration successful!")
    print("="*60)
    print(f"  Participant ID : (hidden — saved to .env.local)")
    print(f"  Team ID        : (hidden — saved to .env.local)")
    print(f"  On-chain TX    : {tx_link}")
    print(f"  API Key        : sk-synth-... (saved to .env.local — shown once!)")
    print("="*60 + "\n")
    print("Next steps:")
    print("  1. source .env.local")
    print("  2. python agent.py")
    print("  3. Join Telegram: https://nsb.dev/synthesis-updates")
    print()

    # Save to .env.local (never commit this file)
    with open(".env.local", "w") as f:
        f.write(f"SYNTHESIS_API_KEY={api_key}\n")
        f.write(f"SYNTHESIS_PARTICIPANT_ID={participant_id}\n")
        f.write(f"SYNTHESIS_TEAM_ID={team_id}\n")
    print("[AgentPass] Credentials saved to .env.local")


if __name__ == "__main__":
    register()
