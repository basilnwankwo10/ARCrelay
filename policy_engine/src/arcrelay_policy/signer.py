"""EIP-712 Sponsorship Signer for ArcRelayPaymaster."""

from __future__ import annotations

import time

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils.address import to_checksum_address

from arcrelay_policy.models import PackedUserOperation, SponsorshipResponse


class EIP712SponsorshipSigner:
    """Signs off-chain EIP-712 sponsorship authorizations matching ArcRelayPaymaster.sol."""

    def __init__(
        self,
        private_key: str,
        paymaster_address: str,
        chain_id: int,
        default_validity_seconds: int = 3600,
    ) -> None:
        self.private_key = private_key
        self.paymaster_address = to_checksum_address(paymaster_address)
        self.chain_id = chain_id
        self.default_validity_seconds = default_validity_seconds
        self.account = Account.from_key(private_key)

    @property
    def signer_address(self) -> str:
        """The public address of the authorization signer."""
        return str(self.account.address)

    def build_domain(self) -> dict[str, object]:
        """Constructs EIP-712 domain data."""
        return {
            "name": "ArcRelayPaymaster",
            "version": "1",
            "chainId": self.chain_id,
            "verifyingContract": self.paymaster_address,
        }

    def sign_sponsorship(
        self,
        user_op: PackedUserOperation,
        policy_id: str,
        valid_until: int | None = None,
        valid_after: int | None = None,
        paymaster_verification_gas: int = 100_000,
        post_op_gas: int = 50_000,
    ) -> SponsorshipResponse:
        """Signs an EIP-712 sponsorship payload and encodes paymasterAndData bytes."""
        now = int(time.time())
        if valid_after is None:
            valid_after = now - 60  # 60s in the past to prevent clock skew
        if valid_until is None:
            valid_until = now + self.default_validity_seconds

        max_cost = user_op.calculate_max_cost(paymaster_verification_gas, post_op_gas)

        # Ensure policy_id is bytes32
        clean_policy_id = policy_id.removeprefix("0x").zfill(64)
        policy_id_bytes = bytes.fromhex(clean_policy_id)

        # 1. Structure EIP-712 Typed Data
        domain = self.build_domain()
        types = {
            "Sponsorship": [
                {"name": "sender", "type": "address"},
                {"name": "nonce", "type": "uint256"},
                {"name": "validUntil", "type": "uint48"},
                {"name": "validAfter", "type": "uint48"},
                {"name": "maxCost", "type": "uint256"},
                {"name": "policyId", "type": "bytes32"},
            ]
        }
        message = {
            "sender": to_checksum_address(user_op.sender),
            "nonce": user_op.nonce,
            "validUntil": valid_until,
            "validAfter": valid_after,
            "maxCost": max_cost,
            "policyId": policy_id_bytes,
        }

        signable = encode_typed_data(
            domain_data=domain,
            message_types=types,
            message_data=message,
        )

        # 2. Cryptographic ECDSA Signature (r, s, v)
        signed = Account.sign_message(signable, private_key=self.private_key)
        signature_bytes = signed.signature

        # 3. Format ERC-4337 v0.7 paymasterAndData:
        # [20 bytes paymaster][16 bytes verifGas][16 bytes postOpGas]
        # [6 bytes validUntil][6 bytes validAfter][32 bytes policyId][65 bytes signature]
        prefix = (
            bytes.fromhex(self.paymaster_address.removeprefix("0x"))
            + paymaster_verification_gas.to_bytes(16, "big")
            + post_op_gas.to_bytes(16, "big")
        )
        payload = (
            valid_until.to_bytes(6, "big")
            + valid_after.to_bytes(6, "big")
            + policy_id_bytes
            + signature_bytes
        )

        paymaster_and_data_hex = "0x" + (prefix + payload).hex()

        return SponsorshipResponse(
            paymaster_and_data=paymaster_and_data_hex,
            valid_until=valid_until,
            valid_after=valid_after,
            max_cost=max_cost,
            signature="0x" + signature_bytes.hex(),
        )
