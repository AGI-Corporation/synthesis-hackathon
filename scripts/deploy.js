/**
 * deploy.js - Deploy AgentPassVerifier to Base Mainnet
 *
 * Usage:
 *   npx hardhat run scripts/deploy.js --network base
 *
 * Prerequisites:
 *   cp .env.example .env
 *   # Fill in BASE_RPC_URL and DEPLOYER_PRIVATE_KEY
 *   npm install
 */

const hre = require("hardhat");
const fs  = require("fs");
const path = require("path");

// ERC-8004 registry on Base Mainnet
// Replace with the canonical address once published by EF
const ERC8004_REGISTRY = process.env.ERC8004_REGISTRY_ADDRESS ||
  "0x0000000000000000000000000000000000000000"; // placeholder

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("\n======================================================");
  console.log("  AgentPass Deployment | The Synthesis 2026");
  console.log("======================================================");
  console.log(`  Network   : ${hre.network.name}`);
  console.log(`  Deployer  : ${deployer.address}`);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`  Balance   : ${hre.ethers.formatEther(balance)} ETH`);
  console.log("------------------------------------------------------\n");

  // Deploy AgentPassVerifier
  console.log("[1/2] Deploying AgentPassVerifier...");
  const Verifier = await hre.ethers.getContractFactory("AgentPassVerifier");
  const verifier = await Verifier.deploy(ERC8004_REGISTRY);
  await verifier.waitForDeployment();

  const verifierAddress = await verifier.getAddress();
  console.log(`      Deployed at: ${verifierAddress}`);

  // Register two default credential types
  console.log("\n[2/2] Registering default credential types...");
  const credTypes = [
    { name: "CMMC-Level2",  vkHash: hre.ethers.keccak256(hre.ethers.toUtf8Bytes("vk:CMMC-Level2"))  },
    { name: "FHIR-R4",      vkHash: hre.ethers.keccak256(hre.ethers.toUtf8Bytes("vk:FHIR-R4"))      },
    { name: "KYC-Basic",    vkHash: hre.ethers.keccak256(hre.ethers.toUtf8Bytes("vk:KYC-Basic"))    },
  ];

  for (const cred of credTypes) {
    const credKey = hre.ethers.keccak256(hre.ethers.toUtf8Bytes(cred.name));
    const tx = await verifier.setVerificationKey(credKey, cred.vkHash);
    await tx.wait();
    console.log(`      Registered: ${cred.name} (${credKey.slice(0, 10)}...)`);
  }

  // Save deployment info
  const deployment = {
    network:           hre.network.name,
    deployer:          deployer.address,
    AgentPassVerifier: verifierAddress,
    erc8004Registry:   ERC8004_REGISTRY,
    credentialTypes:   credTypes.map(c => c.name),
    deployedAt:        new Date().toISOString(),
    blockNumber:       await hre.ethers.provider.getBlockNumber(),
  };

  const outPath = path.join(__dirname, "../deployments.json");
  fs.writeFileSync(outPath, JSON.stringify(deployment, null, 2));

  console.log("\n======================================================");
  console.log("  Deployment complete!");
  console.log("======================================================");
  console.log(`  AgentPassVerifier : ${verifierAddress}`);
  console.log(`  Saved to          : deployments.json`);
  console.log("\nNext steps:");
  console.log("  1. Copy AgentPassVerifier address to .env:");
  console.log(`     AGENT_PASS_VERIFIER_ADDRESS=${verifierAddress}`);
  console.log("  2. Verify on BaseScan:");
  console.log(`     npx hardhat verify --network base ${verifierAddress} ${ERC8004_REGISTRY}`);
  console.log("  3. python agent.py  (now with live on-chain verification)");
  console.log();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
