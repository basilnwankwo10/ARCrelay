// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../interfaces/IEntryPoint.sol";
import "../interfaces/PackedUserOperation.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

interface IAccount {
    function validateUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external returns (uint256 validationData);
}

/**
 * @title ArcTestAccount
 * @notice Lightweight ERC-4337 v0.7 Smart Contract Account for ArcRelay verification.
 */
contract ArcTestAccount is IAccount {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    address public immutable owner;
    IEntryPoint public immutable entryPoint;
    uint256 public executionCount;

    event Executed(address indexed sender, address indexed target, uint256 count);

    constructor(IEntryPoint _entryPoint, address _owner) {
        entryPoint = _entryPoint;
        owner = _owner;
    }

    /**
     * @inheritdoc IAccount
     */
    function validateUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external override returns (uint256 validationData) {
        if (msg.sender != address(entryPoint)) {
            revert("Only EntryPoint");
        }

        // Verify owner signature on userOpHash
        bytes32 ethHash = userOpHash.toEthSignedMessageHash();
        address recovered = ethHash.recover(userOp.signature);

        if (recovered != owner) {
            return 1; // Signature failure
        }

        // When paymaster sponsors, missingAccountFunds is 0
        if (missingAccountFunds > 0) {
            (bool success, ) = payable(msg.sender).call{value: missingAccountFunds}("");
            require(success, "Prefund failed");
        }

        return 0; // Valid
    }

    /**
     * @notice Execute an arbitrary state change or interaction.
     */
    function execute(address target, uint256 value, bytes calldata data) external {
        require(msg.sender == address(entryPoint) || msg.sender == owner, "Unauthorized");
        executionCount += 1;

        if (target != address(0)) {
            (bool success, ) = target.call{value: value}(data);
            require(success, "Call failed");
        }

        emit Executed(msg.sender, target, executionCount);
    }

    receive() external payable {}
}
