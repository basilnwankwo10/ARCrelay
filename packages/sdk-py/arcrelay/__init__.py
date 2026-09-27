"""ArcRelay Python Client SDK.

Official 3-line developer library for ArcRelay Paymaster-as-a-Service on Arc.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Self

import httpx
import orjson
from pydantic import BaseModel, field_validator

__version__ = "0.1.0"
logger = logging.getLogger("arcrelay.client")


class PackedUserOperation(BaseModel):
    """ERC-4337 v0.7 PackedUserOperation payload."""

    sender: str
    nonce: int = 0
    initCode: str = "0x"
    callData: str = "0x"
    accountGasLimits: str = "0x" + "00" * 32
    preVerificationGas: int = 21000
    gasFees: str = "0x" + "00" * 32
    paymasterAndData: str = "0x"
    signature: str = "0x"

    @field_validator("sender")
    @classmethod
    def validate_sender(cls, v: str) -> str:
        v = v.strip().lower()
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError(f"Invalid Ethereum address: {v}")
        return v

    def unpack_gas_limits(self) -> tuple[int, int]:
        raw = bytes.fromhex(self.accountGasLimits.removeprefix("0x").zfill(64))
        return int.from_bytes(raw[0:16], "big"), int.from_bytes(raw[16:32], "big")

    def unpack_gas_fees(self) -> tuple[int, int]:
        raw = bytes.fromhex(self.gasFees.removeprefix("0x").zfill(64))
        return int.from_bytes(raw[0:16], "big"), int.from_bytes(raw[16:32], "big")

    def calculate_max_cost(
        self, paymaster_verification_gas: int = 100_000, post_op_gas: int = 50_000
    ) -> int:
        verif, call = self.unpack_gas_limits()
        _, max_fee = self.unpack_gas_fees()
        if max_fee == 0:
            max_fee = 1_000_000_000
        total_gas = self.preVerificationGas + verif + call + paymaster_verification_gas + post_op_gas
        return total_gas * max_fee


class RateLimitStatus(BaseModel):
    allowed: bool
    consumed_today_usd: float
    daily_limit_usd: float
    remaining_today_usd: float
    reason: str = ""


class SponsorshipResponse(BaseModel):
    paymaster_and_data: str
    valid_until: int
    valid_after: int
    max_cost: int
    signature: str = "0x"


class ArcRelayClientError(Exception):
    def __init__(self, message: str, code: int | str | None = None, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details


class RateLimitExceededError(ArcRelayClientError):
    def __init__(
        self,
        message: str,
        consumed_today_usd: float | None = None,
        daily_limit_usd: float | None = None,
        remaining_today_usd: float | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", details=details)
        self.consumed_today_usd = consumed_today_usd
        self.daily_limit_usd = daily_limit_usd
        self.remaining_today_usd = remaining_today_usd


class PolicyValidationError(ArcRelayClientError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class NetworkTimeoutError(ArcRelayClientError):
    def __init__(self, message: str, timeout_seconds: float) -> None:
        super().__init__(message, code="NETWORK_TIMEOUT", details={"timeout_seconds": timeout_seconds})
        self.timeout_seconds = timeout_seconds


class ArcRelayClient:
    """Async client for sponsoring ERC-4337 v0.7 UserOperations on Arc."""

    def __init__(
        self,
        rpc_url: str,
        policy_id: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not rpc_url:
            raise PolicyValidationError("ArcRelayClient requires a valid rpc_url")
        if not policy_id:
            raise PolicyValidationError("ArcRelayClient requires a valid policy_id")

        self.rpc_url = rpc_url.rstrip("/")
        clean_policy = policy_id.removeprefix("0x")
        if len(clean_policy) > 64:
            raise PolicyValidationError(f"policy_id exceeds 32 bytes (64 hex characters): {policy_id}")
        self.policy_id = "0x" + clean_policy.zfill(64)

        self.api_key = api_key
        self.timeout = timeout
        is_local = "127.0.0.1" in self.rpc_url or "localhost" in self.rpc_url
        self._own_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            trust_env=not is_local,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **({"Authorization": f"Bearer {api_key}"} if api_key else {}),
            },
        )
        self._request_id = 1

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._own_client and not self._client.is_closed:
            await self._client.aclose()

    async def sponsor(self, user_op: PackedUserOperation) -> PackedUserOperation:
        """Sponsors a UserOperation in a single call.

        Updates user_op with signed paymasterAndData and returns it ready for execution.
        """
        sponsorship = await self.get_sponsorship(user_op)
        updated_dict = user_op.model_dump()
        updated_dict["paymasterAndData"] = sponsorship.paymaster_and_data
        return PackedUserOperation.model_validate(updated_dict)

    async def get_sponsorship(self, user_op: PackedUserOperation) -> SponsorshipResponse:
        user_op_dict = user_op.model_dump()
        result = await self._send_rpc(
            method="pm_sponsorUserOperation",
            params=[user_op_dict, self.policy_id],
        )

        try:
            return SponsorshipResponse(
                paymaster_and_data=result["paymasterAndData"],
                valid_until=result["validUntil"],
                valid_after=result["validAfter"],
                max_cost=int(result["maxCost"], 16) if isinstance(result["maxCost"], str) else int(result["maxCost"]),
                signature=result.get("signature", "0x"),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ArcRelayClientError(f"Malformed sponsorship result from server: {e}", details=result) from e

    async def get_policy_limits(self, sender: str) -> RateLimitStatus:
        clean_sender = sender.strip().lower()
        result = await self._send_rpc(
            method="pm_getPolicyLimits",
            params=[self.policy_id, clean_sender],
        )
        try:
            return RateLimitStatus.model_validate(result)
        except Exception as e:
            raise ArcRelayClientError(f"Malformed policy limits result: {e}", details=result) from e

    def estimate_gas_cost(self, user_op: PackedUserOperation) -> tuple[int, float]:
        max_cost_wei = user_op.calculate_max_cost()
        max_cost_usdc = max_cost_wei / 1e18
        return max_cost_wei, max_cost_usdc

    async def _send_rpc(self, method: str, params: list[Any]) -> dict[str, Any]:
        req_id = self._request_id
        self._request_id += 1

        payload_bytes = orjson.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        })

        target_url = self.rpc_url if self.rpc_url.endswith("/rpc") else f"{self.rpc_url}/rpc"

        try:
            response = await self._client.post(
                target_url,
                content=payload_bytes,
            )
        except httpx.TimeoutException as e:
            raise NetworkTimeoutError(
                f"ArcRelay policy engine request timed out after {self.timeout}s",
                timeout_seconds=self.timeout,
            ) from e
        except httpx.RequestError as e:
            raise ArcRelayClientError(f"Connection failure to ArcRelay policy engine: {e}") from e

        if response.status_code != 200:
            raise ArcRelayClientError(
                f"ArcRelay server returned HTTP {response.status_code}: {response.text}",
                code=response.status_code,
            )

        try:
            data: dict[str, Any] = orjson.loads(response.content)
        except orjson.JSONDecodeError as e:
            raise ArcRelayClientError(f"Failed to decode JSON-RPC response: {e}") from e

        if "error" in data and data["error"] is not None:
            err = data["error"]
            code = err.get("code")
            msg = err.get("message", "Unknown error")
            err_data = err.get("data")

            if code == -32001:
                consumed = err_data.get("consumed_today_usd") if isinstance(err_data, dict) else None
                limit = err_data.get("daily_limit_usd") if isinstance(err_data, dict) else None
                rem = err_data.get("remaining_today_usd") if isinstance(err_data, dict) else None
                raise RateLimitExceededError(
                    msg,
                    consumed_today_usd=consumed,
                    daily_limit_usd=limit,
                    remaining_today_usd=rem,
                    details=err_data,
                )
            if code == -32602:
                raise PolicyValidationError(msg, details=err_data)

            raise ArcRelayClientError(msg, code=code, details=err_data)

        if "result" not in data:
            raise ArcRelayClientError("JSON-RPC response missing 'result' field", details=data)

        result: dict[str, Any] = data["result"]
        return result


# Convenience Alias
ArcRelay = ArcRelayClient

__all__ = [
    "ArcRelay",
    "ArcRelayClient",
    "ArcRelayClientError",
    "NetworkTimeoutError",
    "PackedUserOperation",
    "PolicyValidationError",
    "RateLimitExceededError",
    "RateLimitStatus",
    "SponsorshipResponse",
    "__version__",
]
