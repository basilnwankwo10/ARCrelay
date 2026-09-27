"""Integration tests for PolicyEngineServer."""

import pytest
from aiohttp.test_utils import TestClient, TestServer

from arcrelay_policy.config import PolicyEngineConfig
from arcrelay_policy.rate_limiter import PolicyRateLimiter
from arcrelay_policy.server import PolicyEngineServer
from arcrelay_policy.signer import EIP712SponsorshipSigner


@pytest.fixture
def test_server_app():
    private_key = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f36031a"
    config = PolicyEngineConfig(
        verifying_signer_private_key=private_key,
        default_daily_limit_usd=1.00,
    )
    signer = EIP712SponsorshipSigner(
        private_key=private_key,
        paymaster_address=config.paymaster_address,
        chain_id=config.chain_id,
    )
    limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    server = PolicyEngineServer(config=config, signer=signer, rate_limiter=limiter)
    return server.app


@pytest.mark.asyncio
async def test_health_endpoint(test_server_app):
    client = TestClient(TestServer(test_server_app))
    await client.start_server()
    try:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert data["chain_id"] == 5042002
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_rpc_sponsor_user_operation_success(test_server_app):
    client = TestClient(TestServer(test_server_app))
    await client.start_server()
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "pm_sponsorUserOperation",
            "params": [
                {
                    "sender": "0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
                    "nonce": 0,
                    "callData": "0x",
                    "preVerificationGas": 21000,
                },
                "0x0000000000000000000000000000000000000000000000000000000000000001",
            ],
            "id": 1,
        }
        resp = await client.post("/rpc", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert "result" in data
        assert "paymasterAndData" in data["result"]
        assert data["result"]["paymasterAndData"].startswith("0x")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_rpc_sponsor_rate_limit_exceeded(test_server_app):
    client = TestClient(TestServer(test_server_app))
    await client.start_server()
    try:
        # Pre-set high gas fees so cost > $1.00 limit
        high_fee_bytes = (10_000_000_000_000_000).to_bytes(16, "big")  # 0.01 ether per gas
        fees_hex = "0x" + (high_fee_bytes + high_fee_bytes).hex()

        payload = {
            "jsonrpc": "2.0",
            "method": "pm_sponsorUserOperation",
            "params": [
                {
                    "sender": "0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
                    "nonce": 0,
                    "preVerificationGas": 50000,
                    "gasFees": fees_hex,
                },
                "0x0000000000000000000000000000000000000000000000000000000000000001",
            ],
            "id": 2,
        }
        resp = await client.post("/rpc", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32001
        assert "Rate limit exceeded" in data["error"]["message"]
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_rpc_get_policy_limits(test_server_app):
    client = TestClient(TestServer(test_server_app))
    await client.start_server()
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "pm_getPolicyLimits",
            "params": [
                "0x0000000000000000000000000000000000000000000000000000000000000001",
                "0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
            ],
            "id": 3,
        }
        resp = await client.post("/rpc", json=payload)
        assert resp.status == 200
        data = await resp.json()
        assert data["result"]["allowed"] is True
        assert data["result"]["daily_limit_usd"] == 1.00
    finally:
        await client.close()
