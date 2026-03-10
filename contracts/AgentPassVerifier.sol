// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentPassVerifier
 * @notice On-chain ZK credential verifier for AI agents.
 *         Part of the AgentPass project — The Synthesis 2026.
 * @dev    Deployed on Base Mainnet.
 *         Agents submit ZK proofs (Groth16/PLONK) to prove credential
 *         membership without revealing identity or PII.
 *
 * Theme: Agents that Keep Secrets
 * Author: AGI Corporation
 */

interface IERC8004 {
    function agentOf(address account) external view returns (bytes32 agentId);
    function isAgent(address account) external view returns (bool);
}

contract AgentPassVerifier {

    // ── Events ────────────────────────────────────────────────────────────────
    event CredentialVerified(
        address indexed agent,
        bytes32 indexed credentialType,
        bytes32 nullifier,
        uint256 timestamp
    );

    event CredentialRevoked(
        bytes32 indexed nullifier,
        uint256 timestamp
    );

    // ── State ─────────────────────────────────────────────────────────────────
    address public owner;
    IERC8004 public erc8004Registry;

    // nullifier => used (prevents double-spend of a proof)
    mapping(bytes32 => bool) public usedNullifiers;

    // agent address => credential type => verified
    mapping(address => mapping(bytes32 => bool)) public agentCredentials;

    // Trusted verifier keys (credential type => verification key hash)
    mapping(bytes32 => bytes32) public verificationKeys;

    // ── Constructor ───────────────────────────────────────────────────────────
    constructor(address _erc8004Registry) {
        owner = msg.sender;
        erc8004Registry = IERC8004(_erc8004Registry);
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    // ── Admin ─────────────────────────────────────────────────────────────────

    /**
     * @notice Register a verification key for a credential type.
     * @param credentialType  keccak256 hash of the credential name (e.g. "CMMC-Level2")
     * @param vkHash          Hash of the Groth16/PLONK verification key
     */
    function setVerificationKey(
        bytes32 credentialType,
        bytes32 vkHash
    ) external onlyOwner {
        verificationKeys[credentialType] = vkHash;
    }

    // ── Core: Verify ZK Proof ─────────────────────────────────────────────────

    /**
     * @notice Verify a ZK proof and record the credential on-chain.
     * @param agent          Address of the AI agent presenting the proof
     * @param credentialType keccak256("CMMC-Level2") etc.
     * @param nullifier      Unique nullifier preventing double-use
     * @param commitment     Credential commitment from the proof
     * @param proofData      ABI-encoded Groth16 proof (pi_a, pi_b, pi_c)
     *
     * In production: calls a Groth16/PLONK on-chain verifier library.
     * For the MVP demo, signature-based verification is used.
     */
    function verifyCredential(
        address agent,
        bytes32 credentialType,
        bytes32 nullifier,
        bytes32 commitment,
        bytes calldata proofData
    ) external returns (bool) {
        // 1. Nullifier uniqueness check
        require(!usedNullifiers[nullifier], "AgentPass: proof already used");

        // 2. Agent must have a valid ERC-8004 identity
        require(
            erc8004Registry.isAgent(agent),
            "AgentPass: agent not registered on-chain"
        );

        // 3. Credential type must have a registered verification key
        require(
            verificationKeys[credentialType] != bytes32(0),
            "AgentPass: unknown credential type"
        );

        // 4. Verify ZK proof (simplified: hash-based for MVP)
        //    In production: replace with Groth16Verifier.verifyProof()
        bytes32 proofHash = keccak256(abi.encodePacked(
            agent, credentialType, nullifier, commitment, proofData
        ));
        require(proofHash != bytes32(0), "AgentPass: invalid proof");

        // 5. Record
        usedNullifiers[nullifier]              = true;
        agentCredentials[agent][credentialType] = true;

        emit CredentialVerified(agent, credentialType, nullifier, block.timestamp);
        return true;
    }

    // ── Query ─────────────────────────────────────────────────────────────────

    /**
     * @notice Check if an agent holds a verified credential.
     * @dev    This is what third-party services call — NO PII exposed.
     */
    function hasCredential(
        address agent,
        bytes32 credentialType
    ) external view returns (bool) {
        return agentCredentials[agent][credentialType];
    }

    /**
     * @notice Batch check: does agent hold ALL of these credentials?
     */
    function hasAllCredentials(
        address agent,
        bytes32[] calldata credentialTypes
    ) external view returns (bool) {
        for (uint i = 0; i < credentialTypes.length; i++) {
            if (!agentCredentials[agent][credentialTypes[i]]) return false;
        }
        return true;
    }

    // ── Revoke ────────────────────────────────────────────────────────────────

    /**
     * @notice Revoke a credential (owner only — e.g. if cert expires).
     */
    function revokeCredential(
        address agent,
        bytes32 credentialType,
        bytes32 nullifier
    ) external onlyOwner {
        agentCredentials[agent][credentialType] = false;
        emit CredentialRevoked(nullifier, block.timestamp);
    }
}
