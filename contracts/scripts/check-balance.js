import hre from "hardhat";
const { ethers } = hre;

async function main() {
  const [deployer] = await ethers.getSigners();
  const balanceWei = await ethers.provider.getBalance(deployer.address);
  const balanceUsdc = ethers.formatEther(balanceWei); // Or formatUnits depending on decimals

  console.log("--------------------------------------------------");
  console.log("🌐 Network:", hre.network.name);
  console.log("📍 Deployer Address:", deployer.address);
  console.log("💰 Native Balance (USDC):", balanceUsdc, "USDC");
  console.log("--------------------------------------------------");

  if (balanceWei === 0n) {
    console.log("⚠️ Balance is 0. Claim testnet USDC from Circle Faucet:");
    console.log("👉 https://faucet.circle.com (Select 'Arc Testnet')");
  } else {
    console.log("✅ Wallet funded! Ready to deploy: npm run deploy:testnet");
  }
}

main().catch(console.error);
