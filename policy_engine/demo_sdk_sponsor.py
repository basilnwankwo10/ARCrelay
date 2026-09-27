"""End-to-End Live Proof of ArcRelay Client SDK Sponsorship."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from aiohttp import web
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from arcrelay_policy.client import ArcRelayClient
from arcrelay_policy.config import PolicyEngineConfig
from arcrelay_policy.models import PackedUserOperation
from arcrelay_policy.rate_limiter import PolicyRateLimiter
from arcrelay_policy.server import PolicyEngineServer
from arcrelay_policy.signer import EIP712SponsorshipSigner


async def main() -> None:
    print("=" * 65)
    print("ArcRelay SDK Task 2.2 End-to-End Verification Proof")
    print("=" * 65)

    # 1. Load testnet environment
    env_path = Path(__file__).resolve().parents[1] / "contracts" / ".env"
    env = dotenv_values(env_path)
    deployer_pk = env.get("DEPLOYER_PRIVATE_KEY")
    if not deployer_pk:
        raise ValueError("DEPLOYER_PRIVATE_KEY not found in contracts/.env")

    chain_id = int(env.get("ARC_TESTNET_CHAIN_ID", "5042002"))
    paymaster_addr = env.get("PAYMASTER_CONTRACT_ADDRESS", "0x600c83F91464440A1Fc2c4C723C78e2f51F43096")

    config = PolicyEngineConfig(
        verifying_signer_private_key=deployer_pk,
        paymaster_address=paymaster_addr,
        chain_id=chain_id,
        port=8599,
    )
    signer = EIP712SponsorshipSigner(
        private_key=config.verifying_signer_private_key,
        paymaster_address=config.paymaster_address,
        chain_id=config.chain_id,
    )
    rate_limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    server = PolicyEngineServer(config, signer, rate_limiter)

    # 2. Start local server runner
    runner = web.AppRunner(server.app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8599)
    await site.start()
    print("[OK] Policy Engine JSON-RPC running on http://127.0.0.1:8599")

    try:
        # 3. Use the SDK exactly as an external developer would
        policy_id = "0x0000000000000000000000000000000000000000000000000000000000000001"
        async with ArcRelayClient(rpc_url="http://127.0.0.1:8599", policy_id=policy_id) as arcrelay:
            print("\n1. Querying developer policy limits before sponsorship...")
            sender = "0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD"
            limits = await arcrelay.get_policy_limits(sender)
            print(f"   * Daily Quota: ${limits.daily_limit_usd:.2f}")
            print(f"   * Consumed:    ${limits.consumed_today_usd:.4f}")
            print(f"   * Remaining:   ${limits.remaining_today_usd:.4f}")

            # 4. Construct sample UserOperation
            user_op = PackedUserOperation(
                sender=sender,
                nonce=1,
                initCode="0x",
                callData="0x12345678",
                accountGasLimits="0x" + "00" * 15 + "01" + "00" * 15 + "02",
                preVerificationGas=50000,
                gasFees="0x" + "00" * 15 + "03" + "00" * 15 + "04",
            )

            print("\n2. Estimating gas cost via SDK...")
            wei, usdc = arcrelay.estimate_gas_cost(user_op)
            print(f"   * Estimated Max Cost: {wei} wei (~${usdc:.6f} USDC)")

            print("\n3. Executing 1-Line Sponsorship:")
            print("   -> await arcrelay.sponsor(user_op)")
            sponsored_op = await arcrelay.sponsor(user_op)

            print("\n4. Verification Results:")
            print(f"   * Sender:             {sponsored_op.sender}")
            print(f"   * Nonce:              {sponsored_op.nonce}")
            print(f"   * paymasterAndData:   {sponsored_op.paymasterAndData[:42]}... ({len(sponsored_op.paymasterAndData)} chars)")
            assert sponsored_op.paymasterAndData.startswith(paymaster_addr.lower()), "Paymaster address mismatch"
            assert len(sponsored_op.paymasterAndData) == 324, f"Invalid paymasterAndData length: {len(sponsored_op.paymasterAndData)}"

            print("\n5. Querying developer policy limits post-sponsorship...")
            updated_limits = await arcrelay.get_policy_limits(sender)
            print(f"   * Consumed Today:     ${updated_limits.consumed_today_usd:.4f}")
            print(f"   * Remaining Today:    ${updated_limits.remaining_today_usd:.4f}")

            print("\n" + "=" * 65)
            print("[SUCCESS] TASK 2.2 VERIFIED: Developer SDK Succeeded 100%!")
            print("=" * 65)

    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
