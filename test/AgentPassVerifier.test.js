/**
 * AgentPassVerifier.test.js
 * Hardhat tests for the AgentPassVerifier smart contract
 *
 * Run: npx hardhat test
 */

const { expect }       = require("chai");
const { ethers }       = require("hardhat");
const { loadFixture }  = require("@nomicfoundation/hardhat-toolbox/network-helpers");

// ── Helpers ─────────────────────────────────────────────────────────────────

const credKey  = (name)   => ethers.keccak256(ethers.toUtf8Bytes(name));
const vkHash   = (name)   => ethers.keccak256(ethers.toUtf8Bytes(`vk:${name}`));
const randBytes32 = ()    => ethers.hexlify(ethers.randomBytes(32));

// ── Fixture ─────────────────────────────────────────────────────────────────

async function deployFixture() {
  const [owner, agent, stranger] = await ethers.getSigners();

  // Deploy a minimal mock ERC-8004 registry
  const MockRegistry = await ethers.getContractFactory("MockERC8004");
  const registry     = await MockRegistry.deploy();

  // Register the agent in the mock registry
  await registry.registerAgent(agent.address);

  // Deploy AgentPassVerifier
  const Verifier = await ethers.getContractFactory("AgentPassVerifier");
  const verifier = await Verifier.deploy(await registry.getAddress());

  // Register a credential type
  const CMMC = "CMMC-Level2";
  await verifier.setVerificationKey(credKey(CMMC), vkHash(CMMC));

  return { verifier, registry, owner, agent, stranger, CMMC };
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe("AgentPassVerifier", function () {

  describe("Deployment", function () {
    it("should set the correct owner", async function () {
      const { verifier, owner } = await loadFixture(deployFixture);
      expect(await verifier.owner()).to.equal(owner.address);
    });

    it("should set the ERC-8004 registry address", async function () {
      const { verifier, registry } = await loadFixture(deployFixture);
      expect(await verifier.erc8004Registry()).to.equal(await registry.getAddress());
    });
  });

  describe("Verification Keys", function () {
    it("should allow owner to set a verification key", async function () {
      const { verifier, CMMC } = await loadFixture(deployFixture);
      const stored = await verifier.verificationKeys(credKey(CMMC));
      expect(stored).to.equal(vkHash(CMMC));
    });

    it("should revert if non-owner tries to set a verification key", async function () {
      const { verifier, stranger, CMMC } = await loadFixture(deployFixture);
      await expect(
        verifier.connect(stranger).setVerificationKey(credKey(CMMC), vkHash(CMMC))
      ).to.be.revertedWith("Not owner");
    });
  });

  describe("verifyCredential", function () {
    it("should verify a valid credential proof", async function () {
      const { verifier, agent, CMMC } = await loadFixture(deployFixture);

      const nullifier  = randBytes32();
      const commitment = randBytes32();
      const proofData  = ethers.toUtf8Bytes("mock-proof-data");

      await expect(
        verifier.verifyCredential(
          agent.address,
          credKey(CMMC),
          nullifier,
          commitment,
          proofData
        )
      ).to.emit(verifier, "CredentialVerified")
        .withArgs(agent.address, credKey(CMMC), nullifier, await ethers.provider.getBlock("latest").then(b => b.timestamp + 1));
    });

    it("should record the credential after successful verification", async function () {
      const { verifier, agent, CMMC } = await loadFixture(deployFixture);

      const nullifier  = randBytes32();
      const commitment = randBytes32();
      const proofData  = ethers.toUtf8Bytes("mock-proof");

      await verifier.verifyCredential(
        agent.address, credKey(CMMC), nullifier, commitment, proofData
      );

      expect(await verifier.hasCredential(agent.address, credKey(CMMC))).to.be.true;
    });

    it("should reject a reused nullifier (replay attack)", async function () {
      const { verifier, agent, CMMC } = await loadFixture(deployFixture);

      const nullifier  = randBytes32();
      const commitment = randBytes32();
      const proofData  = ethers.toUtf8Bytes("mock-proof");

      // First use succeeds
      await verifier.verifyCredential(
        agent.address, credKey(CMMC), nullifier, commitment, proofData
      );

      // Second use with same nullifier should revert
      await expect(
        verifier.verifyCredential(
          agent.address, credKey(CMMC), nullifier, commitment, proofData
        )
      ).to.be.revertedWith("AgentPass: proof already used");
    });

    it("should reject an unregistered agent", async function () {
      const { verifier, stranger, CMMC } = await loadFixture(deployFixture);

      await expect(
        verifier.verifyCredential(
          stranger.address,
          credKey(CMMC),
          randBytes32(),
          randBytes32(),
          ethers.toUtf8Bytes("proof")
        )
      ).to.be.revertedWith("AgentPass: agent not registered on-chain");
    });

    it("should reject an unknown credential type", async function () {
      const { verifier, agent } = await loadFixture(deployFixture);

      await expect(
        verifier.verifyCredential(
          agent.address,
          credKey("UNKNOWN-CRED"),
          randBytes32(),
          randBytes32(),
          ethers.toUtf8Bytes("proof")
        )
      ).to.be.revertedWith("AgentPass: unknown credential type");
    });
  });

  describe("hasAllCredentials", function () {
    it("should return true when agent holds all requested credentials", async function () {
      const { verifier, owner, agent } = await loadFixture(deployFixture);

      // Register a second credential type
      await verifier.setVerificationKey(credKey("FHIR-R4"), vkHash("FHIR-R4"));

      // Verify both
      for (const cred of ["CMMC-Level2", "FHIR-R4"]) {
        await verifier.verifyCredential(
          agent.address, credKey(cred), randBytes32(), randBytes32(),
          ethers.toUtf8Bytes("proof")
        );
      }

      const result = await verifier.hasAllCredentials(
        agent.address,
        [credKey("CMMC-Level2"), credKey("FHIR-R4")]
      );
      expect(result).to.be.true;
    });
  });

  describe("revokeCredential", function () {
    it("should revoke a credential and emit CredentialRevoked", async function () {
      const { verifier, agent, CMMC } = await loadFixture(deployFixture);

      const nullifier = randBytes32();
      await verifier.verifyCredential(
        agent.address, credKey(CMMC), nullifier, randBytes32(),
        ethers.toUtf8Bytes("proof")
      );

      await expect(
        verifier.revokeCredential(agent.address, credKey(CMMC), nullifier)
      ).to.emit(verifier, "CredentialRevoked");

      expect(await verifier.hasCredential(agent.address, credKey(CMMC))).to.be.false;
    });
  });
});
