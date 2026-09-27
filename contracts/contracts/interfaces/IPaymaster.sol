// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./PackedUserOperation.sol";

/**
 * @notice Post-operation mode for ERC-4337 v0.7 paymasters.
 */
enum PostOpMode {
    opSucceeded,     // User operation executed successfully
    opReverted,      // User operation reverted, but gas was still consumed
    postOpReverted   // Execution of postOp itself reverted
}

/**
 * @title IPaymaster
 * @notice Standard ERC-4337 v0.7 paymaster interface.
 */
interface IPaymaster {
    /**
     * @notice Validates whether the paymaster agrees to sponsor the given user operation.
     * @param userOp The packed user operation calldata.
     * @param userOpHash Hash of the user operation.
     * @param maxCost Maximum cost of gas that may be charged to the paymaster.
     * @return context Arbitrary byte context passed to postOp upon execution.
     * @return validationData Packed validation data containing authorizer, validUntil, and validAfter.
     */
    function validatePaymasterUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    ) external returns (bytes memory context, uint256 validationData);

    /**
     * @notice Hook called after user operation execution to settle gas accounting.
     * @param mode Success or failure mode of the userOp.
     * @param context Context returned by validatePaymasterUserOp.
     * @param actualGasCost Actual gas fee consumed by the user operation.
     * @param actualUserOpFeePerGas Fee per gas unit paid for the execution.
     */
    function postOp(
        PostOpMode mode,
        bytes calldata context,
        uint256 actualGasCost,
        uint256 actualUserOpFeePerGas
    ) external;
}
