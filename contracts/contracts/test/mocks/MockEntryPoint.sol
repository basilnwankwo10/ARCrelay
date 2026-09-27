// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../../interfaces/IEntryPoint.sol";
import "../../interfaces/IPaymaster.sol";
import "../../interfaces/PackedUserOperation.sol";

/**
 * @title MockEntryPoint
 * @notice Mock ERC-4337 EntryPoint contract for testing ArcRelayPaymaster.
 */
contract MockEntryPoint is IEntryPoint {
    mapping(address => uint256) public deposits;

    function depositTo(address account) external payable override {
        deposits[account] += msg.value;
    }

    function withdrawTo(address payable withdrawAddress, uint256 withdrawAmount) external override {
        require(deposits[msg.sender] >= withdrawAmount, "Insufficient deposit");
        deposits[msg.sender] -= withdrawAmount;
        (bool success, ) = withdrawAddress.call{value: withdrawAmount}("");
        require(success, "Withdraw transfer failed");
    }

    function balanceOf(address account) external view override returns (uint256) {
        return deposits[account];
    }

    function simulateValidation(
        IPaymaster paymaster,
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    ) external returns (bytes memory context, uint256 validationData) {
        return paymaster.validatePaymasterUserOp(userOp, userOpHash, maxCost);
    }

    function simulatePostOp(
        IPaymaster paymaster,
        PostOpMode mode,
        bytes calldata context,
        uint256 actualGasCost,
        uint256 actualUserOpFeePerGas
    ) external {
        paymaster.postOp(mode, context, actualGasCost, actualUserOpFeePerGas);
    }

    receive() external payable {}
}
