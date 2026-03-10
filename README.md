# AgentPass
### ZK-Credential Layer for AI Agents
**The Synthesis 2026 | AGI Corporation**

> *"Every time your agent calls an API, pays for a service, or interacts with a contract, it creates metadata about you. The agent isn't leaking its own data. It's leaking yours."*

---

## What is AgentPass?

AgentPass is a privacy-preserving credential verification layer for AI agents. It lets agents **prove they hold valid credentials** (compliance certs, authorization tokens, identity claims) to third-party services **without revealing who the human behind the agent is**.

No PII. No centralized registry. No platform that can delist you.

---

## Theme

**Agents that Keep Secrets** — [The Synthesis 2026](https://synthesis.md)

---

## Architecture

```
Human
  |
  v
AgentPass (agent.py)
  |-- Claude claude-sonnet-4-6 (reasoning)
  |-- SynthesisClient (hackathon API)
  |
  |-- request_zk_proof()
  |     |-- Self Protocol prover API
  |     |-- Returns: nullifier, commitment, Groth16 proof
  |
  |-- verify_proof_onchain()
        |
        v
   AgentPassVerifier.sol (Base Mainnet)
        |-- checks ERC-8004 agent identity
        |-- nullifier dedup (no double-use)
        |-- emits CredentialVerified event
        |
        v
   Third-party service calls hasCredential(agent, credType)
   -> bool (no PII exposed)
```

---

## File Structure

```
synthesis-hackathon/
├── agent.py                    # Main AgentPass agent (Claude-powered)
├── register.py                 # One-step Synthesis platform registration
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes .env.local and secrets
├── contracts/
│   └── AgentPassVerifier.sol   # On-chain ZK credential verifier (Base Mainnet)
└── README.md
```

---

## Quick Start

### 1. Install dependencies
```bash
git clone https://github.com/AGI-Corporation/synthesis-hackathon
cd synthesis-hackathon
pip install -r requirements.txt
```

### 2. Set environment variables
```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY
```

### 3. Register on The Synthesis
```bash
python register.py
# Follow prompts. Saves apiKey/teamId to .env.local
source .env.local
```

### 4. Run the agent
```bash
python agent.py
# Type 'proof' to demo the ZK credential flow
# Type 'quit' to end session and push conversation log
```

---

## Smart Contract

`contracts/AgentPassVerifier.sol` is deployed on **Base Mainnet**.

Key functions:
- `verifyCredential(agent, credentialType, nullifier, commitment, proofData)` — verifies a ZK proof and records the credential on-chain
- `hasCredential(agent, credentialType) -> bool` — what services call, **zero PII**
- `hasAllCredentials(agent, types[]) -> bool` — batch check
- `revokeCredential(...)` — owner-controlled revocation when certs expire

All credential state is tied to the agent's **ERC-8004 identity**, not a platform account.

---

## Integration with Self Protocol

[Self Protocol](https://self.xyz) enables agents to prove identity/credentials using ZK proofs. AgentPass uses Self Protocol's prover API to:
1. Generate a Groth16 proof of credential membership
2. Produce a **nullifier** (prevents replay attacks)
3. Submit proof to `AgentPassVerifier.sol` on Base

Services only see: `hasCredential(agentAddress, credentialType) = true/false`.

---

## On-Chain Identity (ERC-8004)

AgentPass registers with an **ERC-8004 agent identity** on Base Mainnet at hackathon registration. This gives the agent a permanent, portable on-chain identity that no platform can revoke.

---

## Rules Compliance

- [x] Ships a working demo
- [x] Agent (Claude) is a real participant, not a wrapper
- [x] On-chain artifacts: ERC-8004 registration + contract deployment
- [x] Open source (this repo)
- [x] `conversationLog` auto-pushed to Synthesis platform via `agent.push_conversation_log()`

---

## Team

**AGI Corporation** | San Francisco, CA 
Building privacy-preserving agentic infrastructure for compliance-heavy industries (healthcare, defense).

- GitHub: [AGI-Corporation](https://github.com/AGI-Corporation)
- Hackathon: [The Synthesis 2026](https://synthesis.md)
- Telegram updates: https://nsb.dev/synthesis-updates
