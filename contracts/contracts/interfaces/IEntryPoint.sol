// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./PackedUserOperation.sol";

/**
 * @title IEntryPoint
 * @notice Partial ERC-4337 v0.7 EntryPoint interface for paymaster deposit management.
 */
interface IEntryPoint {
    /**
     * @notice Deposit native gas tokens for an account.
     * @param account The address to deposit funds for.
     */
    function depositTo(address account) external payable;

    /**
     * @notice Withdraw deposited gas tokens.
     * @param withdrawAddress Destination address to send withdrawn tokens.
     * @param withdrawAmount Amount of tokens to withdraw.
     */
    function withdrawTo(address payable withdrawAddress, uint256 withdrawAmount) external;

    /**
     * @notice Query current gas deposit for an account.
     * @param account The address whose balance to inspect.
     * @return deposit Current deposited balance.
     */
    function balanceOf(address account) external view returns (uint256 deposit);
}
