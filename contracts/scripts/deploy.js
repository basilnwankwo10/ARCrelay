import hre from "hardhat";
const { ethers } = hre;

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("--------------------------------------------------");
  console.log("🚀 Deploying ArcRelayPaymaster to:", hre.network.name);
  console.log("Deployer Address:", deployer.address);
  console.log("Account Balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)));

  // Official ERC-4337 v0.7 EntryPoint on EVM chains:
  // 0x0000000071727De22E5E9d8BAf0edAc6f37da032
  const entryPointAddress = process.env.ENTRY_POINT_ADDRESS || "0x0000000071727De22E5E9d8BAf0edAc6f37da032";
  const verifyingSigner = process.env.VERIFYING_SIGNER_ADDRESS || deployer.address;
  const ownerAddress = process.env.PAYMASTER_OWNER_ADDRESS || deployer.address;
  const feeMarkupBps = parseInt(process.env.FEE_MARKUP_BPS || "500"); // 5.00%

  console.log("EntryPoint Address:", entryPointAddress);
  console.log("Verifying Signer:", verifyingSigner);
  console.log("Owner Address:", ownerAddress);
  console.log("Fee Markup:", feeMarkupBps, "bps");

  const ArcRelayPaymaster = await ethers.getContractFactory("ArcRelayPaymaster");
  const paymaster = await ArcRelayPaymaster.deploy(
    entryPointAddress,
    verifyingSigner,
    ownerAddress,
    feeMarkupBps
  );

  await paymaster.waitForDeployment();
  const paymasterAddress = await paymaster.getAddress();

  console.log("--------------------------------------------------");
  console.log("✅ ArcRelayPaymaster deployed successfully!");
  console.log("Contract Address:", paymasterAddress);
  console.log("Transaction Hash:", paymaster.deploymentTransaction().hash);
  console.log("--------------------------------------------------");
}

main().catch((error) => {
  console.error("❌ Deployment failed:", error);
  process.exitCode = 1;
});
