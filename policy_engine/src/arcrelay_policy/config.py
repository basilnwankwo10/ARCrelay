"""Configuration management for ArcRelay Policy Engine."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PolicyEngineConfig:
    """Type-safe configuration settings for the ArcRelay Policy Engine."""

    rpc_url: str = "https://rpc.testnet.arc.network"
    chain_id: int = 5042002
    paymaster_address: str = "0x600c83F91464440A1Fc2c4C723C78e2f51F43096"
    entry_point_address: str = "0x0000000071727De22E5E9d8BAf0edAc6f37da032"
    verifying_signer_private_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8080
    default_daily_limit_usd: float = 1.00
    validity_window_seconds: int = 3600  # 1 hour validity

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> PolicyEngineConfig:
        """Loads configuration from environment variables or .env file."""
        if env_path and env_path.is_file():
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k.strip(), v)

        rpc = os.getenv("ARC_TESTNET_RPC", "https://rpc.testnet.arc.network")
        chain_id = int(os.getenv("ARC_TESTNET_CHAIN_ID", "5042002"))
        paymaster = os.getenv(
            "PAYMASTER_CONTRACT_ADDRESS",
            "0x600c83F91464440A1Fc2c4C723C78e2f51F43096",
        )
        entry_point = os.getenv(
            "ENTRY_POINT_ADDRESS",
            "0x0000000071727De22E5E9d8BAf0edAc6f37da032",
        )
        priv_key = os.getenv("DEPLOYER_PRIVATE_KEY", "")
        host = os.getenv("POLICY_HOST", "127.0.0.1")
        port = int(os.getenv("POLICY_PORT", "8080"))
        limit = float(os.getenv("DEFAULT_DAILY_LIMIT_USD", "1.00"))

        return cls(
            rpc_url=rpc,
            chain_id=chain_id,
            paymaster_address=paymaster,
            entry_point_address=entry_point,
            verifying_signer_private_key=priv_key,
            host=host,
            port=port,
            default_daily_limit_usd=limit,
        )
