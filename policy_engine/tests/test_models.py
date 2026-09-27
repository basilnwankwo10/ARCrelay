"""Tests for ERC-4337 v0.7 Pydantic models."""

import pytest

from arcrelay_policy.models import PackedUserOperation


def test_packed_user_operation_validation():
    # Valid checksum/lowercase address
    op = PackedUserOperation(
        sender="0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
        nonce=5,
    )
    assert op.sender == "0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7"
    assert op.nonce == 5


def test_invalid_sender_rejection():
    with pytest.raises(ValueError, match="Invalid Ethereum address"):
        PackedUserOperation(sender="0xinvalid")


def test_gas_limit_unpacking():
    # 100,000 verif (0x186a0) and 200,000 call (0x30d40)
    verif_bytes = (100_000).to_bytes(16, "big")
    call_bytes = (200_000).to_bytes(16, "big")
    limits_hex = "0x" + (verif_bytes + call_bytes).hex()

    op = PackedUserOperation(
        sender="0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
        accountGasLimits=limits_hex,
    )
    verif, call = op.unpack_gas_limits()
    assert verif == 100_000
    assert call == 200_000


def test_gas_fee_unpacking():
    # 2 gwei priority, 10 gwei maxFee
    prio_bytes = (2_000_000_000).to_bytes(16, "big")
    max_bytes = (10_000_000_000).to_bytes(16, "big")
    fees_hex = "0x" + (prio_bytes + max_bytes).hex()

    op = PackedUserOperation(
        sender="0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
        gasFees=fees_hex,
    )
    prio, max_fee = op.unpack_gas_fees()
    assert prio == 2_000_000_000
    assert max_fee == 10_000_000_000


def test_calculate_max_cost():
    verif_bytes = (100_000).to_bytes(16, "big")
    call_bytes = (100_000).to_bytes(16, "big")
    limits_hex = "0x" + (verif_bytes + call_bytes).hex()

    prio_bytes = (1_000_000_000).to_bytes(16, "big")
    max_bytes = (2_000_000_000).to_bytes(16, "big")  # 2 gwei
    fees_hex = "0x" + (prio_bytes + max_bytes).hex()

    op = PackedUserOperation(
        sender="0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
        preVerificationGas=20_000,
        accountGasLimits=limits_hex,
        gasFees=fees_hex,
    )

    # total_gas = preVerificationGas(20k) + verif(100k) + call(100k) + pm_verif(100k) + post_op(50k) = 370k
    # max_cost = 370,000 * 2,000,000,000 = 740,000,000,000,000 wei
    cost = op.calculate_max_cost(paymaster_verification_gas=100_000, post_op_gas=50_000)
    assert cost == 370_000 * 2_000_000_000
