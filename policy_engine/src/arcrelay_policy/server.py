"""High-throughput Asynchronous JSON-RPC & REST Server for ArcRelay Policy Engine."""

from __future__ import annotations

import logging
from typing import Any

import orjson
from aiohttp import web

from arcrelay_policy.config import PolicyEngineConfig
from arcrelay_policy.models import PackedUserOperation
from arcrelay_policy.rate_limiter import PolicyRateLimiter
from arcrelay_policy.signer import EIP712SponsorshipSigner

logger = logging.getLogger("arcrelay.policy_engine")


class PolicyEngineServer:
    """Async server exposing JSON-RPC 2.0 and REST endpoints for Paymaster sponsorship."""

    def __init__(
        self,
        config: PolicyEngineConfig,
        signer: EIP712SponsorshipSigner,
        rate_limiter: PolicyRateLimiter,
    ) -> None:
        self.config = config
        self.signer = signer
        self.rate_limiter = rate_limiter
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_post("/rpc", self.handle_rpc)
        self.app.router.add_post("/v1/sponsor", self.handle_rest_sponsor)

    def _json_response(self, data: Any, status: int = 200) -> web.Response:
        """Fast JSON response serialization via orjson."""
        return web.Response(
            body=orjson.dumps(data),
            status=status,
            content_type="application/json",
        )

    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return self._json_response(
            {
                "status": "ok",
                "service": "arcrelay-policy-engine",
                "chain_id": self.config.chain_id,
                "paymaster": self.config.paymaster_address,
                "signer": self.signer.signer_address,
            }
        )

    async def handle_rpc(self, request: web.Request) -> web.Response:
        """Standard JSON-RPC 2.0 handler."""
        try:
            body = await request.read()
            payload = orjson.loads(body)
        except (orjson.JSONDecodeError, ValueError, KeyError) as e:
            return self._json_response(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}, "id": None}
            )

        rpc_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params", [])

        if method == "pm_sponsorUserOperation":
            return await self._rpc_sponsor(params, rpc_id)
        elif method == "pm_getPolicyLimits":
            return await self._rpc_get_limits(params, rpc_id)
        else:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": rpc_id,
                }
            )

    async def _rpc_sponsor(self, params: list[Any], rpc_id: Any) -> web.Response:
        """Handles pm_sponsorUserOperation RPC method."""
        if not params or len(params) < 2:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: expected [userOp, policyId]",
                    },
                    "id": rpc_id,
                }
            )

        try:
            user_op_raw, policy_id = params[0], str(params[1])
            user_op = PackedUserOperation.model_validate(user_op_raw)
        except (ValueError, TypeError, KeyError) as e:
            return self._json_response(
                {"jsonrpc": "2.0", "error": {"code": -32602, "message": f"Validation error: {e}"}, "id": rpc_id}
            )

        # Calculate estimated cost in USD (assuming 1 USDC = $1.00 on Arc)
        max_cost_wei = user_op.calculate_max_cost()
        est_cost_usd = max_cost_wei / 1e18

        # Enforce rate limit
        rate_status = await self.rate_limiter.check_and_consume(
            policy_id=policy_id,
            sender=user_op.sender,
            cost_usd=est_cost_usd,
        )

        if not rate_status.allowed:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": f"Rate limit exceeded: {rate_status.reason}",
                        "data": rate_status.model_dump(),
                    },
                    "id": rpc_id,
                }
            )

        # Cryptographically sign sponsorship
        resp = self.signer.sign_sponsorship(user_op=user_op, policy_id=policy_id)

        return self._json_response(
            {
                "jsonrpc": "2.0",
                "result": {
                    "paymasterAndData": resp.paymaster_and_data,
                    "validUntil": resp.valid_until,
                    "validAfter": resp.valid_after,
                    "maxCost": hex(resp.max_cost),
                },
                "id": rpc_id,
            }
        )

    async def _rpc_get_limits(self, params: list[Any], rpc_id: Any) -> web.Response:
        """Handles pm_getPolicyLimits RPC method."""
        if not params or len(params) < 2:
            return self._json_response(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Expected [policyId, senderAddress]"},
                    "id": rpc_id,
                }
            )

        policy_id, sender = str(params[0]), str(params[1])
        status = await self.rate_limiter.get_user_status(policy_id, sender)

        return self._json_response(
            {"jsonrpc": "2.0", "result": status.model_dump(), "id": rpc_id}
        )

    async def handle_rest_sponsor(self, request: web.Request) -> web.Response:
        """REST endpoint for sponsorship."""
        try:
            body = await request.read()
            data = orjson.loads(body)
            user_op = PackedUserOperation.model_validate(data["user_op"])
            policy_id = str(data["policy_id"])
        except (orjson.JSONDecodeError, ValueError, TypeError, KeyError) as e:
            return self._json_response({"error": f"Invalid request body: {e}"}, status=400)

        # Rate check
        max_cost_wei = user_op.calculate_max_cost()
        est_cost_usd = max_cost_wei / 1e18
        rate_status = await self.rate_limiter.check_and_consume(policy_id, user_op.sender, est_cost_usd)
        if not rate_status.allowed:
            return self._json_response({"error": rate_status.reason, "rate_status": rate_status.model_dump()}, status=429)

        resp = self.signer.sign_sponsorship(user_op, policy_id)
        return self._json_response(
            {
                "paymaster_and_data": resp.paymaster_and_data,
                "valid_until": resp.valid_until,
                "valid_after": resp.valid_after,
                "max_cost": hex(resp.max_cost),
            }
        )
