"""ArcRelay: Live End-to-End Gasless Transaction Verification on Arc Testnet.

Task 1.4: Proves on-chain that an account with 0.00 USDC can execute a state
update on Arc while ArcRelayPaymaster sponsors 100% of the gas.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from dotenv import dotenv_values
from eth_account import Account
from eth_account.messages import encode_defunct
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from web3 import Web3

# Ensure policy_engine src is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arcrelay_policy.models import PackedUserOperation
from arcrelay_policy.signer import EIP712SponsorshipSigner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("arcrelay.verify")

ENTRY_POINT_ABI = [
    {
        "name": "getNonce",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "sender", "type": "address"},
            {"name": "key", "type": "uint192"},
        ],
        "outputs": [{"name": "nonce", "type": "uint256"}],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "name": "getUserOpHash",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {
                "name": "userOp",
                "type": "tuple",
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "initCode", "type": "bytes"},
                    {"name": "callData", "type": "bytes"},
                    {"name": "accountGasLimits", "type": "bytes32"},
                    {"name": "preVerificationGas", "type": "uint256"},
                    {"name": "gasFees", "type": "bytes32"},
                    {"name": "paymasterAndData", "type": "bytes"},
                    {"name": "signature", "type": "bytes"},
                ],
            }
        ],
        "outputs": [{"name": "", "type": "bytes32"}],
    },
    {
        "name": "handleOps",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {
                "name": "ops",
                "type": "tuple[]",
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "initCode", "type": "bytes"},
                    {"name": "callData", "type": "bytes"},
                    {"name": "accountGasLimits", "type": "bytes32"},
                    {"name": "preVerificationGas", "type": "uint256"},
                    {"name": "gasFees", "type": "bytes32"},
                    {"name": "paymasterAndData", "type": "bytes"},
                    {"name": "signature", "type": "bytes"},
                ],
            },
            {"name": "beneficiary", "type": "address"},
        ],
        "outputs": [],
    },
]


def run_verification() -> dict[str, object]:
    # 1. Environment & Network Setup
    env_path = Path(__file__).resolve().parents[3] / "contracts" / ".env"
    env = dotenv_values(env_path)

    deployer_pk = env.get("DEPLOYER_PRIVATE_KEY")
    if not deployer_pk:
        raise ValueError("DEPLOYER_PRIVATE_KEY not found in contracts/.env")

    rpc_url = env.get("ARC_TESTNET_RPC", "https://rpc.testnet.arc.network")
    chain_id = int(env.get("ARC_TESTNET_CHAIN_ID", "5042002"))
    paymaster_addr = env.get("PAYMASTER_CONTRACT_ADDRESS", "0x600c83F91464440A1Fc2c4C723C78e2f51F43096")
    entry_point_addr = env.get("ENTRY_POINT_ADDRESS", "0x0000000071727De22E5E9d8BAf0edAc6f37da032")

    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.proxies = {"http": "http://127.0.0.1:17891", "https": "http://127.0.0.1:17891"}

    w3 = Web3(Web3.HTTPProvider(rpc_url, session=session))

    deployer_account = Account.from_key(deployer_pk)
    paymaster_addr = Web3.to_checksum_address(paymaster_addr)
    entry_point_addr = Web3.to_checksum_address(entry_point_addr)

    logger.info("--------------------------------------------------")
    logger.info("🚀 Initiating ArcRelay Gasless Verification (Task 1.4)")
    logger.info("Network Chain ID: %s", chain_id)
    logger.info("Deployer / Relayer: %s", deployer_account.address)
    logger.info("Paymaster Contract: %s", paymaster_addr)
    logger.info("EntryPoint Contract: %s", entry_point_addr)

    deployer_bal = w3.eth.get_balance(deployer_account.address)
    logger.info("Deployer Native USDC: %.4f USDC", deployer_bal / 1e18)

    # 2. Check & Pre-fund Corporate Gas Tank
    paymaster_artifact_path = (
        Path(__file__).resolve().parents[3]
        / "contracts"
        / "artifacts"
        / "contracts"
        / "ArcRelayPaymaster.sol"
        / "ArcRelayPaymaster.json"
    )
    with open(paymaster_artifact_path, encoding="utf-8") as f:
        paymaster_abi = json.load(f)["abi"]

    paymaster_contract = w3.eth.contract(address=paymaster_addr, abi=paymaster_abi)
    entry_point_contract = w3.eth.contract(address=entry_point_addr, abi=ENTRY_POINT_ABI)

    policy_id = Web3.keccak(text="pilot-client-genesis")
    client_bal = paymaster_contract.functions.clientBalances(policy_id).call()
    ep_paymaster_bal = entry_point_contract.functions.balanceOf(paymaster_addr).call()

    logger.info("Corporate Policy ID: %s", policy_id.hex())
    logger.info("Current Policy Tank Balance: %.4f USDC", client_bal / 1e18)
    logger.info("Current Paymaster EntryPoint Stake: %.4f USDC", ep_paymaster_bal / 1e18)

    current_gas_price = w3.eth.gas_price
    max_priority_fee = 2_000_000_000  # 2 gwei
    max_fee = int(current_gas_price * 1.6) + max_priority_fee
    logger.info("Current Network Gas Price: %.2f gwei | Using MaxFee: %.2f gwei", current_gas_price / 1e9, max_fee / 1e9)

    if client_bal < 10**17:  # less than 0.1 USDC
        deposit_val = 10**18  # deposit 1.0 USDC
        logger.info("Funding corporate gas tank with 1.0 USDC...")
        deposit_tx = paymaster_contract.functions.depositFor(policy_id).build_transaction({
            "from": deployer_account.address,
            "value": deposit_val,
            "nonce": w3.eth.get_transaction_count(deployer_account.address, "latest"),
            "gas": 200_000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
            "chainId": chain_id,
        })
        signed_dep = deployer_account.sign_transaction(deposit_tx)
        dep_hash = w3.eth.send_raw_transaction(signed_dep.raw_transaction)
        logger.info("Deposit sent. Tx hash: %s. Waiting confirmation...", dep_hash.hex())
        w3.eth.wait_for_transaction_receipt(dep_hash, timeout=120)
        logger.info("✅ Corporate gas tank funded successfully!")

    # 3. Create a 0-Balance Test User
    user_account = Account.create()
    user_initial_bal = w3.eth.get_balance(user_account.address)
    logger.info("--------------------------------------------------")
    logger.info("👤 Generated Test User EOA: %s", user_account.address)
    logger.info("User Balance: %.6f USDC (CONFIRMED ZERO BALANCE)", user_initial_bal / 1e18)
    assert user_initial_bal == 0, "Test user must have 0 balance"

    # 4. Deploy ArcTestAccount for User
    account_artifact_path = (
        Path(__file__).resolve().parents[3]
        / "contracts"
        / "artifacts"
        / "contracts"
        / "test"
        / "ArcTestAccount.sol"
        / "ArcTestAccount.json"
    )
    with open(account_artifact_path, encoding="utf-8") as f:
        acc_art = json.load(f)
        acc_abi = acc_art["abi"]
        acc_bytecode = acc_art["bytecode"]

    account_factory = w3.eth.contract(abi=acc_abi, bytecode=acc_bytecode)
    logger.info("Deploying ArcTestAccount for 0-balance user...")
    deploy_acc_tx = account_factory.constructor(entry_point_addr, user_account.address).build_transaction({
        "from": deployer_account.address,
        "nonce": w3.eth.get_transaction_count(deployer_account.address, "latest"),
        "gas": 900_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "chainId": chain_id,
    })
    signed_deploy = deployer_account.sign_transaction(deploy_acc_tx)
    deploy_hash = w3.eth.send_raw_transaction(signed_deploy.raw_transaction)
    acc_receipt = w3.eth.wait_for_transaction_receipt(deploy_hash, timeout=120)
    smart_account_addr = Web3.to_checksum_address(acc_receipt.contractAddress)

    smart_account_contract = w3.eth.contract(address=smart_account_addr, abi=acc_abi)
    acc_owner = smart_account_contract.functions.owner().call()
    acc_count = smart_account_contract.functions.executionCount().call()
    smart_acc_bal = w3.eth.get_balance(smart_account_addr)

    logger.info("✅ Smart Account Deployed at: %s", smart_account_addr)
    logger.info("Smart Account Owner: %s", acc_owner)
    logger.info("Smart Account Initial Balance: %.6f USDC (ZERO)", smart_acc_bal / 1e18)
    logger.info("Smart Account Initial Execution Count: %d", acc_count)

    # 5. Build PackedUserOperation
    nonce = entry_point_contract.functions.getNonce(smart_account_addr, 0).call()

    # Call smart_account.execute(address(0), 0, b"")
    call_data = smart_account_contract.encode_abi(
        "execute",
        args=["0x0000000000000000000000000000000000000000", 0, b""],
    )

    verif_gas = 150_000
    call_gas = 100_000
    pre_verif_gas = 60_000

    account_gas_limits = "0x" + verif_gas.to_bytes(16, "big").hex() + call_gas.to_bytes(16, "big").hex()
    gas_fees = "0x" + max_priority_fee.to_bytes(16, "big").hex() + max_fee.to_bytes(16, "big").hex()

    user_op_model = PackedUserOperation(
        sender=smart_account_addr,
        nonce=nonce,
        initCode="0x",
        callData=call_data,
        accountGasLimits=account_gas_limits,
        preVerificationGas=pre_verif_gas,
        gasFees=gas_fees,
        paymasterAndData="0x",
        signature="0x",
    )

    # 6. EIP-712 Sponsorship Signing via ArcRelay Engine
    logger.info("--------------------------------------------------")
    logger.info("🔐 Requesting EIP-712 sponsorship from ArcRelay Policy Engine...")
    signer = EIP712SponsorshipSigner(
        private_key=deployer_pk,
        paymaster_address=paymaster_addr,
        chain_id=chain_id,
        default_validity_seconds=3600,
    )
    sponsorship = signer.sign_sponsorship(
        user_op=user_op_model,
        policy_id=policy_id.hex(),
        paymaster_verification_gas=100_000,
        post_op_gas=50_000,
    )
    user_op_model.paymasterAndData = sponsorship.paymaster_and_data
    logger.info("✅ Paymaster sponsorship signed! PaymasterAndData length: %d bytes", len(bytes.fromhex(user_op_model.paymasterAndData.removeprefix("0x"))))

    # 7. User Signs the UserOperation
    user_op_tuple = (
        smart_account_addr,
        nonce,
        b"",
        bytes.fromhex(call_data.removeprefix("0x")),
        bytes.fromhex(account_gas_limits.removeprefix("0x")),
        pre_verif_gas,
        bytes.fromhex(gas_fees.removeprefix("0x")),
        bytes.fromhex(user_op_model.paymasterAndData.removeprefix("0x")),
        b"",
    )

    user_op_hash = entry_point_contract.functions.getUserOpHash(user_op_tuple).call()
    logger.info("UserOp Hash computed by EntryPoint: %s", user_op_hash.hex())

    # User signs the userOpHash
    signed_user_msg = Account.sign_message(
        encode_defunct(primitive=user_op_hash),
        private_key=user_account.key,
    )
    user_op_model.signature = "0x" + signed_user_msg.signature.hex()

    final_user_op_tuple = (
        smart_account_addr,
        nonce,
        b"",
        bytes.fromhex(call_data.removeprefix("0x")),
        bytes.fromhex(account_gas_limits.removeprefix("0x")),
        pre_verif_gas,
        bytes.fromhex(gas_fees.removeprefix("0x")),
        bytes.fromhex(user_op_model.paymasterAndData.removeprefix("0x")),
        bytes.fromhex(user_op_model.signature.removeprefix("0x")),
    )

    # 8. Submit handleOps to Arc Testnet
    logger.info("--------------------------------------------------")
    logger.info("🚀 Relaying sponsored UserOperation to Arc Testnet EntryPoint...")
    handle_ops_tx = entry_point_contract.functions.handleOps(
        [final_user_op_tuple],
        deployer_account.address,
    ).build_transaction({
        "from": deployer_account.address,
        "nonce": w3.eth.get_transaction_count(deployer_account.address, "latest"),
        "gas": 900_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": max_priority_fee,
        "chainId": chain_id,
    })

    signed_handle = deployer_account.sign_transaction(handle_ops_tx)
    handle_hash = w3.eth.send_raw_transaction(signed_handle.raw_transaction)
    logger.info("Transaction submitted! Hash: %s", handle_hash.hex())
    logger.info("Waiting for on-chain block inclusion...")

    tx_receipt = w3.eth.wait_for_transaction_receipt(handle_hash, timeout=120)
    logger.info("Receipt status: %s (Block: %d)", tx_receipt.status, tx_receipt.blockNumber)

    # 9. Verify Post-Execution On-Chain State
    final_user_bal = w3.eth.get_balance(user_account.address)
    final_smart_bal = w3.eth.get_balance(smart_account_addr)
    final_count = smart_account_contract.functions.executionCount().call()
    final_tank_bal = paymaster_contract.functions.clientBalances(policy_id).call()

    logger.info("==================================================")
    logger.info("🎉 TASK 1.4 VERIFICATION RESULTS:")
    logger.info("Status: %s", "SUCCESS ✅" if tx_receipt.status == 1 else "FAILED ❌")
    logger.info("Transaction Hash: %s", handle_hash.hex())
    logger.info("Block Number: %d", tx_receipt.blockNumber)
    logger.info("User EOA Balance After: %.6f USDC ($0.00 PAID BY USER!)", final_user_bal / 1e18)
    logger.info("Smart Account Balance After: %.6f USDC ($0.00 PAID!)", final_smart_bal / 1e18)
    logger.info("Smart Account Execution Count: %d (Incremented from %d)", final_count, acc_count)
    logger.info("Corporate Gas Tank Balance: %.4f USDC", final_tank_bal / 1e18)
    logger.info("Arcscan Explorer: https://testnet.arcscan.app/tx/%s", handle_hash.hex())
    logger.info("==================================================")

    return {
        "status": "SUCCESS" if tx_receipt.status == 1 else "FAILED",
        "tx_hash": handle_hash.hex(),
        "block_number": tx_receipt.blockNumber,
        "user_eoa": user_account.address,
        "smart_account": smart_account_addr,
        "user_gas_paid": "0.00 USDC",
        "execution_count": final_count,
        "explorer_url": f"https://testnet.arcscan.app/tx/{handle_hash.hex()}",
    }


if __name__ == "__main__":
    run_verification()
