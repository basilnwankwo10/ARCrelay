"""Unit tests for the ArcRelay Python Client SDK."""

from __future__ import annotations

import httpx
import orjson
import pytest

from arcrelay_policy.client import (
    ArcRelayClient,
    ArcRelayClientError,
    NetworkTimeoutError,
    PolicyValidationError,
    RateLimitExceededError,
)
from arcrelay_policy.models import PackedUserOperation


def _make_dummy_user_op() -> PackedUserOperation:
    return PackedUserOperation(
        sender="0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD",
        nonce=0,
        initCode="0x",
        callData="0x1234",
        accountGasLimits="0x" + "00" * 15 + "01" + "00" * 15 + "02",
        preVerificationGas=50000,
        gasFees="0x" + "00" * 15 + "03" + "00" * 15 + "04",
    )


def test_client_init_validation() -> None:
    with pytest.raises(PolicyValidationError):
        ArcRelayClient(rpc_url="", policy_id="0x1")

    with pytest.raises(PolicyValidationError):
        ArcRelayClient(rpc_url="http://localhost:8545", policy_id="")

    client = ArcRelayClient(
        rpc_url="http://localhost:8545/",
        policy_id="0x1",
        api_key="secret-key",
    )
    assert client.rpc_url == "http://localhost:8545"
    assert client.policy_id == "0x" + "0" * 63 + "1"
    assert client.api_key == "secret-key"


def test_estimate_gas_cost() -> None:
    client = ArcRelayClient(rpc_url="http://localhost:8545", policy_id="0x1")
    user_op = _make_dummy_user_op()
    wei, usdc = client.estimate_gas_cost(user_op)
    assert wei > 0
    assert usdc > 0.0


@pytest.mark.asyncio
async def test_sponsor_happy_path() -> None:
    mock_signed_data = "0x600c83f91464440a1fc2c4c723c78e2f51f43096" + "aa" * 141

    def handle_request(request: httpx.Request) -> httpx.Response:
        data = orjson.loads(request.content)
        assert data["method"] == "pm_sponsorUserOperation"
        assert data["params"][1] == "0x" + "0" * 63 + "1"

        resp_payload = {
            "jsonrpc": "2.0",
            "id": data["id"],
            "result": {
                "paymasterAndData": mock_signed_data,
                "validUntil": 1790400000,
                "validAfter": 1790300000,
                "maxCost": "0x123456",
            },
        }
        return httpx.Response(200, content=orjson.dumps(resp_payload))

    transport = httpx.MockTransport(handle_request)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = ArcRelayClient(
            rpc_url="http://localhost:8545",
            policy_id="0x1",
            http_client=http_client,
        )

        user_op = _make_dummy_user_op()
        sponsored = await client.sponsor(user_op)

        assert sponsored.paymasterAndData == mock_signed_data
        assert sponsored.sender == user_op.sender


@pytest.mark.asyncio
async def test_sponsor_rate_limit_exceeded() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        data = orjson.loads(request.content)
        resp_payload = {
            "jsonrpc": "2.0",
            "id": data["id"],
            "error": {
                "code": -32001,
                "message": "Rate limit exceeded: Daily cap reached",
                "data": {
                    "allowed": False,
                    "consumed_today_usd": 1.25,
                    "daily_limit_usd": 1.00,
                    "remaining_today_usd": 0.0,
                },
            },
        }
        return httpx.Response(200, content=orjson.dumps(resp_payload))

    transport = httpx.MockTransport(handle_request)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = ArcRelayClient(
            rpc_url="http://localhost:8545",
            policy_id="0x1",
            http_client=http_client,
        )

        user_op = _make_dummy_user_op()
        with pytest.raises(RateLimitExceededError) as exc_info:
            await client.sponsor(user_op)

        assert exc_info.value.consumed_today_usd == 1.25
        assert exc_info.value.daily_limit_usd == 1.00
        assert exc_info.value.remaining_today_usd == 0.0


@pytest.mark.asyncio
async def test_get_policy_limits() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        data = orjson.loads(request.content)
        assert data["method"] == "pm_getPolicyLimits"
        resp_payload = {
            "jsonrpc": "2.0",
            "id": data["id"],
            "result": {
                "allowed": True,
                "consumed_today_usd": 0.15,
                "daily_limit_usd": 1.00,
                "remaining_today_usd": 0.85,
                "reason": "OK",
            },
        }
        return httpx.Response(200, content=orjson.dumps(resp_payload))

    transport = httpx.MockTransport(handle_request)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = ArcRelayClient(
            rpc_url="http://localhost:8545",
            policy_id="0x1",
            http_client=http_client,
        )

        limits = await client.get_policy_limits("0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD")
        assert limits.allowed is True
        assert limits.consumed_today_usd == 0.15
        assert limits.remaining_today_usd == 0.85


@pytest.mark.asyncio
async def test_network_timeout() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    transport = httpx.MockTransport(handle_request)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = ArcRelayClient(
            rpc_url="http://localhost:8545",
            policy_id="0x1",
            http_client=http_client,
            timeout=1.0,
        )

        user_op = _make_dummy_user_op()
        with pytest.raises(NetworkTimeoutError):
            await client.sponsor(user_op)
