"""Tests for EIP-712 Sponsorship Signer."""

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import to_checksum_address

from arcrelay_policy.models import PackedUserOperation
from arcrelay_policy.signer import EIP712SponsorshipSigner


def test_signer_generates_valid_eip712_signature():
    # Test private key
    private_key = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f36031a"
    signer_acct = Account.from_key(private_key)
    paymaster_addr = "0x600c83F91464440A1Fc2c4C723C78e2f51F43096"
    chain_id = 5042002
    policy_id = "0x0000000000000000000000000000000000000000000000000000000000000001"

    signer = EIP712SponsorshipSigner(
        private_key=private_key,
        paymaster_address=paymaster_addr,
        chain_id=chain_id,
    )
    assert signer.signer_address == signer_acct.address

    user_op = PackedUserOperation(
        sender="0x65cb1ee2babb5f7950fb2e6554e77f6d6efff4e7",
        nonce=0,
    )

    resp = signer.sign_sponsorship(
        user_op=user_op,
        policy_id=policy_id,
        valid_until=2000000000,
        valid_after=1000000000,
    )

    # 1. Check response attributes
    assert resp.valid_until == 2000000000
    assert resp.valid_after == 1000000000
    assert resp.signature.startswith("0x")
    assert len(resp.signature) == 132  # 65 bytes * 2 + '0x'

    # 2. Check total paymasterAndData length
    # 20 bytes pm + 16 bytes verif + 16 bytes postOp + 6 bytes until + 6 bytes after + 32 bytes policy + 65 bytes sig = 161 bytes
    raw_bytes = bytes.fromhex(resp.paymaster_and_data.removeprefix("0x"))
    assert len(raw_bytes) == 161

    # 3. Check slices
    pm_slice = "0x" + raw_bytes[0:20].hex()
    assert pm_slice.lower() == paymaster_addr.lower()

    # 4. Cryptographically verify signature recovery matches signer_acct.address
    domain = signer.build_domain()
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
        "validUntil": resp.valid_until,
        "validAfter": resp.valid_after,
        "maxCost": resp.max_cost,
        "policyId": bytes.fromhex(policy_id.removeprefix("0x").zfill(64)),
    }
    signable = encode_typed_data(domain_data=domain, message_types=types, message_data=message)
    recovered = Account.recover_message(signable, signature=resp.signature)
    assert recovered == signer_acct.address
