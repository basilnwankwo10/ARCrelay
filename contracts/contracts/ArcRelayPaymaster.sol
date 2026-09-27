// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

import "./interfaces/IPaymaster.sol";
import "./interfaces/IEntryPoint.sol";
import "./interfaces/PackedUserOperation.sol";

/**
 * @title ArcRelayPaymaster
 * @notice Enterprise ERC-4337 v0.7 Gasless Paymaster for Arc (Native USDC Gas Layer).
 * @dev Sponsoring paymaster validating off-chain EIP-712 authorizations from the ArcRelay
 * Policy Engine and managing enterprise client pre-funded corporate gas tanks.
 */
contract ArcRelayPaymaster is IPaymaster, Ownable, Pausable, EIP712 {
    using ECDSA for bytes32;

    // --- Constants ---
    
    /// @notice EIP-712 struct typehash for sponsorship authorizations
    bytes32 public constant SPONSORSHIP_TYPEHASH = keccak256(
        "Sponsorship(address sender,uint256 nonce,uint48 validUntil,uint48 validAfter,uint256 maxCost,bytes32 policyId)"
    );

    /// @notice Standard ERC-4337 v0.7 paymasterAndData prefix offset:
    /// 20 bytes paymaster + 16 bytes verificationGasLimit + 16 bytes postOpGasLimit = 52 bytes
    uint256 public constant PAYMASTER_DATA_OFFSET = 52;

    /// @notice Length of payload inside paymasterData:
    /// 6 bytes validUntil + 6 bytes validAfter + 32 bytes policyId + 65 bytes signature = 109 bytes
    uint256 public constant PAYMASTER_PAYLOAD_LENGTH = 109;

    /// @notice Maximum allowed markup fee (20.00% = 2000 bps)
    uint16 public constant MAX_FEE_MARKUP_BPS = 2000;

    // --- State Variables ---

    /// @notice The ERC-4337 EntryPoint contract
    IEntryPoint public immutable entryPoint;

    /// @notice The public address of the ArcRelay Policy Engine signing key
    address public verifyingSigner;

    /// @notice Platform convenience markup in basis points (e.g., 500 = 5.00%)
    uint16 public feeMarkupBps;

    /// @notice Corporate gas tank balances per client policy (policyId => deposited balance)
    mapping(bytes32 => uint256) public clientBalances;

    /// @notice Client owners of specific policies (policyId => client owner address)
    mapping(bytes32 => address) public policyOwners;

    // --- Events ---

    event UserOpSponsored(
        bytes32 indexed policyId,
        address indexed sender,
        uint256 actualGasCost,
        uint256 feeCharged
    );
    event ClientDeposited(
        bytes32 indexed policyId,
        address indexed depositor,
        uint256 amount
    );
    event ClientWithdrawn(
        bytes32 indexed policyId,
        address indexed recipient,
        uint256 amount
    );
    event PolicyRegistered(
        bytes32 indexed policyId,
        address indexed owner
    );
    event VerifyingSignerUpdated(
        address indexed oldSigner,
        address indexed newSigner
    );
    event FeeMarkupUpdated(
        uint16 oldMarkupBps,
        uint16 newMarkupBps
    );

    // --- Custom Errors ---

    error OnlyEntryPoint();
    error InvalidPaymasterDataLength();
    error InsufficientClientBalance(bytes32 policyId, uint256 required, uint256 available);
    error UnauthorizedPolicyAccess();
    error PolicyAlreadyRegistered(bytes32 policyId);
    error ZeroAddress();
    error ZeroDeposit();
    error FeeMarkupTooHigh(uint16 markupBps);

    // --- Modifiers ---

    modifier onlyEntryPoint() {
        if (msg.sender != address(entryPoint)) {
            revert OnlyEntryPoint();
        }
        _;
    }

    // --- Constructor ---

    /**
     * @param _entryPoint The official ERC-4337 v0.7 EntryPoint contract address.
     * @param _verifyingSigner The initial off-chain authorization signer address.
     * @param _initialOwner The owner of the Paymaster contract.
     * @param _feeMarkupBps Initial convenience fee markup in bps (e.g. 500 for 5%).
     */
    constructor(
        IEntryPoint _entryPoint,
        address _verifyingSigner,
        address _initialOwner,
        uint16 _feeMarkupBps
    )
        Ownable(_initialOwner)
        EIP712("ArcRelayPaymaster", "1")
    {
        if (address(_entryPoint) == address(0) || _verifyingSigner == address(0)) {
            revert ZeroAddress();
        }
        if (_feeMarkupBps > MAX_FEE_MARKUP_BPS) {
            revert FeeMarkupTooHigh(_feeMarkupBps);
        }

        entryPoint = _entryPoint;
        verifyingSigner = _verifyingSigner;
        feeMarkupBps = _feeMarkupBps;
    }

    // --- ERC-4337 Core Logic ---

    /**
     * @inheritdoc IPaymaster
     * @dev Validates whether this paymaster agrees to sponsor the UserOperation.
     */
    function validatePaymasterUserOp(
        PackedUserOperation calldata userOp,
        bytes32 /* userOpHash */,
        uint256 maxCost
    )
        external
        override
        onlyEntryPoint
        whenNotPaused
        returns (bytes memory context, uint256 validationData)
    {
        // 1. Verify paymasterAndData length
        if (userOp.paymasterAndData.length < PAYMASTER_DATA_OFFSET + PAYMASTER_PAYLOAD_LENGTH) {
            revert InvalidPaymasterDataLength();
        }

        // 2. Decode custom paymasterData
        bytes calldata payload = userOp.paymasterAndData[PAYMASTER_DATA_OFFSET:];
        uint48 validUntil = uint48(bytes6(payload[0:6]));
        uint48 validAfter = uint48(bytes6(payload[6:12]));
        bytes32 policyId = bytes32(payload[12:44]);
        bytes calldata signature = payload[44:109];

        // 3. Verify client corporate gas tank balance
        uint256 currentBalance = clientBalances[policyId];
        if (currentBalance < maxCost) {
            revert InsufficientClientBalance(policyId, maxCost, currentBalance);
        }

        // 4. Verify EIP-712 off-chain policy authorization signature
        bytes32 structHash = keccak256(
            abi.encode(
                SPONSORSHIP_TYPEHASH,
                userOp.sender,
                userOp.nonce,
                validUntil,
                validAfter,
                maxCost,
                policyId
            )
        );
        bytes32 digest = _hashTypedDataV4(structHash);
        address recoveredSigner = ECDSA.recover(digest, signature);

        // If signature does not match verifying signer, return sigFailed
        if (recoveredSigner != verifyingSigner) {
            return ("", _packValidationData(true, validUntil, validAfter));
        }

        // 5. Context passed to postOp for final settlement
        context = abi.encode(policyId, userOp.sender, maxCost);
        validationData = _packValidationData(false, validUntil, validAfter);
    }

    /**
     * @inheritdoc IPaymaster
     * @dev Post-operation settlement deducting actual gas fee plus platform markup from client tank.
     */
    function postOp(
        PostOpMode /* mode */,
        bytes calldata context,
        uint256 actualGasCost,
        uint256 /* actualUserOpFeePerGas */
    )
        external
        override
        onlyEntryPoint
    {
        (bytes32 policyId, address sender, ) = abi.decode(context, (bytes32, address, uint256));

        // Calculate total fee including convenience markup
        uint256 feeCharged = actualGasCost;
        if (feeMarkupBps > 0) {
            feeCharged += (actualGasCost * feeMarkupBps) / 10000;
        }

        // Deduct from client tank
        uint256 balance = clientBalances[policyId];
        if (balance <= feeCharged) {
            clientBalances[policyId] = 0;
        } else {
            clientBalances[policyId] = balance - feeCharged;
        }

        emit UserOpSponsored(policyId, sender, actualGasCost, feeCharged);
    }

    // --- Client Gas Tank & Policy Management ---

    /**
     * @notice Register a unique policy ID for an enterprise client.
     * @param policyId Unique identifier for the sponsorship policy / corporate account.
     */
    function registerPolicy(bytes32 policyId) external {
        if (policyOwners[policyId] != address(0)) {
            revert PolicyAlreadyRegistered(policyId);
        }
        policyOwners[policyId] = msg.sender;
        emit PolicyRegistered(policyId, msg.sender);
    }

    /**
     * @notice Pre-fund a client corporate gas tank with native gas tokens (USDC on Arc).
     * @dev The funds are immediately deposited into the EntryPoint for execution liquidity.
     * @param policyId The policy account to credit.
     */
    function depositFor(bytes32 policyId) external payable {
        if (msg.value == 0) {
            revert ZeroDeposit();
        }
        if (policyOwners[policyId] == address(0)) {
            policyOwners[policyId] = msg.sender;
            emit PolicyRegistered(policyId, msg.sender);
        }

        clientBalances[policyId] += msg.value;

        // Forward native deposit directly to EntryPoint
        entryPoint.depositTo{value: msg.value}(address(this));

        emit ClientDeposited(policyId, msg.sender, msg.value);
    }

    /**
     * @notice Withdraw unspent client gas deposit back to client.
     * @param policyId The policy identifier to withdraw from.
     * @param recipient The destination address receiving the refund.
     * @param amount The token amount to withdraw.
     */
    function withdrawClientBalance(
        bytes32 policyId,
        address payable recipient,
        uint256 amount
    )
        external
    {
        if (msg.sender != policyOwners[policyId] && msg.sender != owner()) {
            revert UnauthorizedPolicyAccess();
        }
        if (recipient == address(0)) {
            revert ZeroAddress();
        }

        uint256 balance = clientBalances[policyId];
        if (balance < amount) {
            revert InsufficientClientBalance(policyId, amount, balance);
        }

        clientBalances[policyId] = balance - amount;

        // Withdraw from EntryPoint and send to recipient
        entryPoint.withdrawTo(recipient, amount);

        emit ClientWithdrawn(policyId, recipient, amount);
    }

    // --- Admin / Emergency Functions ---

    /**
     * @notice Update the off-chain authorization signing key.
     * @param newSigner New verifying signer address.
     */
    function setVerifyingSigner(address newSigner) external onlyOwner {
        if (newSigner == address(0)) {
            revert ZeroAddress();
        }
        address oldSigner = verifyingSigner;
        verifyingSigner = newSigner;
        emit VerifyingSignerUpdated(oldSigner, newSigner);
    }

    /**
     * @notice Update the convenience fee markup in basis points.
     * @param newMarkupBps New markup in bps (max 2000 = 20%).
     */
    function setFeeMarkup(uint16 newMarkupBps) external onlyOwner {
        if (newMarkupBps > MAX_FEE_MARKUP_BPS) {
            revert FeeMarkupTooHigh(newMarkupBps);
        }
        uint16 oldMarkup = feeMarkupBps;
        feeMarkupBps = newMarkupBps;
        emit FeeMarkupUpdated(oldMarkup, newMarkupBps);
    }

    /**
     * @notice Withdraw surplus Paymaster funds held at the EntryPoint.
     * @param to Destination address.
     * @param amount Amount to withdraw.
     */
    function withdrawEntryPointDeposit(address payable to, uint256 amount) external onlyOwner {
        if (to == address(0)) {
            revert ZeroAddress();
        }
        entryPoint.withdrawTo(to, amount);
    }

    /**
     * @notice Pause sponsorship in emergency.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpause sponsorship.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // --- Internal Helpers ---

    /**
     * @dev Packs validation result conforming to ERC-4337 v0.7:
     * bits 0..159: authorizer (0 for success, 1 for signature failure)
     * bits 160..207: validUntil (48 bits)
     * bits 208..255: validAfter (48 bits)
     */
    function _packValidationData(
        bool sigFailed,
        uint48 validUntil,
        uint48 validAfter
    ) internal pure returns (uint256) {
        return (sigFailed ? 1 : 0) | (uint256(validUntil) << 160) | (uint256(validAfter) << 208);
    }

    /// @notice Allows contract to receive native gas refunds from EntryPoint
    receive() external payable {}
}
