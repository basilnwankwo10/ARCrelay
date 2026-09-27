/**
 * Utility functions for gas limits, hex formatting, and UserOperation packing
 */

import {
  DEFAULT_PAYMASTER_POST_OP_GAS,
  DEFAULT_PAYMASTER_VERIFICATION_GAS,
} from './constants.js';
import { PolicyValidationError } from './errors.js';
import type { GasEstimate, PackedUserOperation, UserOperationInput } from './types.js';

/**
 * Normalizes an address string to lowercase with standard 0x prefix
 */
export function normalizeAddress(address: string): string {
  if (!address || typeof address !== 'string') {
    throw new PolicyValidationError(`Invalid address: ${address}`);
  }
  const clean = address.trim().toLowerCase();
  if (!/^0x[0-9a-f]{40}$/.test(clean)) {
    throw new PolicyValidationError(`Invalid Ethereum address format: ${address}`);
  }
  return clean;
}

/**
 * Converts a number, bigint, or string into a 0x-prefixed hex string
 */
export function toHex(value: bigint | number | string): string {
  if (typeof value === 'bigint') {
    return `0x${value.toString(16)}`;
  }
  if (typeof value === 'number') {
    if (isNaN(value) || value < 0) {
      throw new PolicyValidationError(`Invalid non-negative number for hex conversion: ${value}`);
    }
    return `0x${Math.floor(value).toString(16)}`;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed.startsWith('0x') || trimmed.startsWith('0X')) {
      return trimmed.toLowerCase();
    }
    // String number
    if (/^\d+$/.test(trimmed)) {
      return `0x${BigInt(trimmed).toString(16)}`;
    }
    throw new PolicyValidationError(`Unrecognized numeric string format: ${value}`);
  }
  throw new PolicyValidationError(`Unsupported value type for toHex: ${typeof value}`);
}

/**
 * Parses any hex or decimal input to bigint
 */
export function toBigInt(value: bigint | number | string | undefined, defaultValue: bigint = 0n): bigint {
  if (value === undefined || value === null) {
    return defaultValue;
  }
  if (typeof value === 'bigint') {
    return value;
  }
  if (typeof value === 'number') {
    return BigInt(Math.floor(value));
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (trimmed === '' || trimmed === '0x') {
      return defaultValue;
    }
    if (trimmed.startsWith('0x') || trimmed.startsWith('0X')) {
      return BigInt(trimmed);
    }
    return BigInt(trimmed);
  }
  return defaultValue;
}

/**
 * Pads a hex string with leading zeros to the specified number of bytes
 */
export function padHex(hex: string, byteLength: number): string {
  const stripped = hex.replace(/^0x/i, '');
  const targetChars = byteLength * 2;
  if (stripped.length > targetChars) {
    throw new PolicyValidationError(
      `Hex string exceeds expected length of ${byteLength} bytes: ${hex}`
    );
  }
  return `0x${stripped.padStart(targetChars, '0')}`;
}

/**
 * Packs 16-byte verificationGasLimit and 16-byte callGasLimit into 32-byte accountGasLimits
 */
export function packGasLimits(
  verificationGasLimit: bigint | number | string,
  callGasLimit: bigint | number | string
): string {
  const verifBig = toBigInt(verificationGasLimit);
  const callBig = toBigInt(callGasLimit);

  const verifHex = verifBig.toString(16).padStart(32, '0');
  const callHex = callBig.toString(16).padStart(32, '0');

  return `0x${verifHex}${callHex}`;
}

/**
 * Unpacks 32-byte accountGasLimits into verificationGasLimit and callGasLimit
 */
export function unpackGasLimits(accountGasLimits: string): {
  verificationGasLimit: bigint;
  callGasLimit: bigint;
} {
  const stripped = accountGasLimits.replace(/^0x/i, '').padStart(64, '0');
  const verifHex = stripped.slice(0, 32);
  const callHex = stripped.slice(32, 64);

  return {
    verificationGasLimit: BigInt(`0x${verifHex}`),
    callGasLimit: BigInt(`0x${callHex}`),
  };
}

/**
 * Packs 16-byte maxPriorityFeePerGas and 16-byte maxFeePerGas into 32-byte gasFees
 */
export function packGasFees(
  maxPriorityFeePerGas: bigint | number | string,
  maxFeePerGas: bigint | number | string
): string {
  const prioBig = toBigInt(maxPriorityFeePerGas);
  const maxBig = toBigInt(maxFeePerGas);

  const prioHex = prioBig.toString(16).padStart(32, '0');
  const maxHex = maxBig.toString(16).padStart(32, '0');

  return `0x${prioHex}${maxHex}`;
}

/**
 * Unpacks 32-byte gasFees into maxPriorityFeePerGas and maxFeePerGas
 */
export function unpackGasFees(gasFees: string): {
  maxPriorityFeePerGas: bigint;
  maxFeePerGas: bigint;
} {
  const stripped = gasFees.replace(/^0x/i, '').padStart(64, '0');
  const prioHex = stripped.slice(0, 32);
  const maxHex = stripped.slice(32, 64);

  return {
    maxPriorityFeePerGas: BigInt(`0x${prioHex}`),
    maxFeePerGas: BigInt(`0x${maxHex}`),
  };
}

/**
 * Ensures a policy ID is formatted as a 32-byte hex string
 */
export function formatPolicyId(policyId: string): string {
  const stripped = policyId.replace(/^0x/i, '');
  if (stripped.length > 64) {
    throw new PolicyValidationError(`Policy ID exceeds 32 bytes (64 hex characters): ${policyId}`);
  }
  return `0x${stripped.padStart(64, '0')}`;
}

/**
 * Transforms a UserOperationInput into an ERC-4337 v0.7 PackedUserOperation
 */
export function packUserOperation(input: UserOperationInput): PackedUserOperation {
  const sender = normalizeAddress(input.sender);
  const nonce = toBigInt(input.nonce, 0n);
  const initCode = input.initCode ? (input.initCode.startsWith('0x') ? input.initCode : `0x${input.initCode}`) : '0x';
  const callData = input.callData ? (input.callData.startsWith('0x') ? input.callData : `0x${input.callData}`) : '0x';

  // Pack accountGasLimits if unpacked fields provided
  let accountGasLimits = input.accountGasLimits;
  if (!accountGasLimits) {
    const verif = input.verificationGasLimit ?? 150_000n;
    const call = input.callGasLimit ?? 200_000n;
    accountGasLimits = packGasLimits(verif, call);
  } else {
    accountGasLimits = padHex(accountGasLimits, 32);
  }

  // Pre-verification gas
  const preVerificationGas = toBigInt(input.preVerificationGas, 50_000n);

  // Pack gasFees if unpacked fields provided
  let gasFees = input.gasFees;
  if (!gasFees) {
    const priority = input.maxPriorityFeePerGas ?? 2_000_000_000n; // 2 gwei
    const maxFee = input.maxFeePerGas ?? 25_000_000_000n; // 25 gwei
    gasFees = packGasFees(priority, maxFee);
  } else {
    gasFees = padHex(gasFees, 32);
  }

  const paymasterAndData = input.paymasterAndData || '0x';
  const signature = input.signature || '0x';

  return {
    sender,
    nonce: toHex(nonce),
    initCode,
    callData,
    accountGasLimits,
    preVerificationGas: toHex(preVerificationGas),
    gasFees,
    paymasterAndData,
    signature,
  };
}

/**
 * Calculates gas metrics and estimated USDC cost for a UserOperation
 */
export function calculateGasCost(
  userOp: PackedUserOperation | UserOperationInput,
  paymasterVerifGas: bigint = DEFAULT_PAYMASTER_VERIFICATION_GAS,
  postOpGas: bigint = DEFAULT_PAYMASTER_POST_OP_GAS
): GasEstimate {
  const packed = 'accountGasLimits' in userOp && userOp.accountGasLimits ? (userOp as PackedUserOperation) : packUserOperation(userOp);
  const limits = unpackGasLimits(packed.accountGasLimits);
  const fees = unpackGasFees(packed.gasFees);
  const preVerif = toBigInt(packed.preVerificationGas);

  const totalGas = preVerif + limits.verificationGasLimit + limits.callGasLimit + paymasterVerifGas + postOpGas;
  const maxFee = fees.maxFeePerGas > 0n ? fees.maxFeePerGas : 1_000_000_000n;
  const maxCostWei = totalGas * maxFee;

  // 1 USDC = 10^18 wei on Arc native USDC chain
  const maxCostUsdc = Number(maxCostWei) / 1e18;

  return {
    maxCostWei,
    maxCostUsdc,
    verificationGasLimit: limits.verificationGasLimit,
    callGasLimit: limits.callGasLimit,
    preVerificationGas: preVerif,
    maxFeePerGas: fees.maxFeePerGas,
    maxPriorityFeePerGas: fees.maxPriorityFeePerGas,
  };
}
