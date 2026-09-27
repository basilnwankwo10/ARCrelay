"""Application entrypoint for the ArcRelay Policy Engine."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from aiohttp import web

from arcrelay_policy.config import PolicyEngineConfig
from arcrelay_policy.rate_limiter import PolicyRateLimiter
from arcrelay_policy.server import PolicyEngineServer
from arcrelay_policy.signer import EIP712SponsorshipSigner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("arcrelay.app")


def build_app(config: PolicyEngineConfig) -> web.Application:
    """Builds and returns the configured aiohttp web application."""
    if not config.verifying_signer_private_key:
        raise ValueError(
            "Missing verifying_signer_private_key. Ensure DEPLOYER_PRIVATE_KEY is set in .env"
        )

    signer = EIP712SponsorshipSigner(
        private_key=config.verifying_signer_private_key,
        paymaster_address=config.paymaster_address,
        chain_id=config.chain_id,
        default_validity_seconds=config.validity_window_seconds,
    )

    rate_limiter = PolicyRateLimiter(
        default_daily_user_limit_usd=config.default_daily_limit_usd
    )

    server = PolicyEngineServer(
        config=config,
        signer=signer,
        rate_limiter=rate_limiter,
    )

    return server.app


def main() -> None:
    """CLI runner."""
    parser = argparse.ArgumentParser(description="ArcRelay Policy Engine & EIP-712 Signer")
    parser.add_argument(
        "--env",
        type=Path,
        default=Path(r"C:\Users\BAMS\Documents\GITHUB PROJECTS\ARCrelay\contracts\.env"),
        help="Path to .env configuration file",
    )
    args = parser.parse_args()

    config = PolicyEngineConfig.from_env(args.env)
    app = build_app(config)

    logger.info("🚀 Starting ArcRelay Policy Engine on http://%s:%s", config.host, config.port)
    logger.info("📍 Chain ID: %s | Paymaster: %s", config.chain_id, config.paymaster_address)

    web.run_app(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
