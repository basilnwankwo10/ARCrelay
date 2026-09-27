"""Data models for ArcRelay ERC-4337 v0.7 UserOperations and Sponsorship."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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
        """Returns (verificationGasLimit, callGasLimit) from accountGasLimits."""
        raw = bytes.fromhex(self.accountGasLimits.removeprefix("0x").zfill(64))
        verif = int.from_bytes(raw[0:16], "big")
        call = int.from_bytes(raw[16:32], "big")
        return verif, call

    def unpack_gas_fees(self) -> tuple[int, int]:
        """Returns (maxPriorityFeePerGas, maxFeePerGas) from gasFees."""
        raw = bytes.fromhex(self.gasFees.removeprefix("0x").zfill(64))
        priority = int.from_bytes(raw[0:16], "big")
        max_fee = int.from_bytes(raw[16:32], "big")
        return priority, max_fee

    def calculate_max_cost(
        self, paymaster_verification_gas: int = 100_000, post_op_gas: int = 50_000
    ) -> int:
        """Calculates maximum gas cost in native units (wei)."""
        verif, call = self.unpack_gas_limits()
        _, max_fee = self.unpack_gas_fees()

        # Fallback to standard gas fee if unset
        if max_fee == 0:
            max_fee = 1_000_000_000  # 1 gwei fallback

        total_gas = self.preVerificationGas + verif + call + paymaster_verification_gas + post_op_gas
        return total_gas * max_fee


class SponsorshipRequest(BaseModel):
    """Request payload for sponsoring a UserOperation."""

    user_op: PackedUserOperation
    policy_id: str = Field(description="Hex bytes32 policy or app identifier")
    valid_until: int | None = None
    valid_after: int | None = None


class SponsorshipResponse(BaseModel):
    """Response payload containing signed paymasterAndData."""

    paymaster_and_data: str
    valid_until: int
    valid_after: int
    max_cost: int
    signature: str


class RateLimitStatus(BaseModel):
    """Rate limit validation status."""

    allowed: bool
    consumed_today_usd: float
    daily_limit_usd: float
    remaining_today_usd: float
    reason: str = ""
