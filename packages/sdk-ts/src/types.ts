/**
 * Core type definitions for @arcrelay/sdk
 * ERC-4337 v0.7 compliant types for ArcRelay Paymaster-as-a-Service
 */

/**
 * ERC-4337 v0.7 PackedUserOperation representation
 */
export interface PackedUserOperation {
  sender: string;
  nonce: string | number | bigint;
  initCode: string;
  callData: string;
  accountGasLimits: string;
  preVerificationGas: string | number | bigint;
  gasFees: string;
  paymasterAndData: string;
  signature: string;
}

/**
 * Flexible UserOperation input allowing either packed or unpacked gas fields
 */
export interface UserOperationInput {
  sender: string;
  nonce?: string | number | bigint;
  initCode?: string;
  callData?: string;
  // Packed format
  accountGasLimits?: string;
  gasFees?: string;
  // Unpacked format
  verificationGasLimit?: string | number | bigint;
  callGasLimit?: string | number | bigint;
  maxPriorityFeePerGas?: string | number | bigint;
  maxFeePerGas?: string | number | bigint;
  preVerificationGas?: string | number | bigint;
  paymasterAndData?: string;
  signature?: string;
}

/**
 * Configuration options for initializing the ArcRelay client
 */
export interface ArcRelayConfig {
  /** URL of the ArcRelay Policy Engine RPC / REST service */
  rpcUrl: string;
  /** B2B Policy ID registered with ArcRelay (32-byte hex string) */
  policyId: string;
  /** Optional developer API key for authentication */
  apiKey?: string;
  /** Request timeout in milliseconds (default: 10,000ms) */
  timeoutMs?: number;
  /** Arc Network Chain ID (default: 5042002 for Arc Testnet) */
  chainId?: number;
  /** ArcRelay Paymaster smart contract address */
  paymasterAddress?: string;
  /** Custom fetch implementation (optional, defaults to global fetch) */
  customFetch?: typeof fetch;
}

/**
 * Response returned from policy engine when sponsoring a UserOperation
 */
export interface SponsorshipResult {
  paymasterAndData: string;
  validUntil: number;
  validAfter: number;
  maxCost: string;
}

/**
 * Status of client daily gas policy limits
 */
export interface PolicyLimits {
  allowed: boolean;
  consumedTodayUsd: number;
  dailyLimitUsd: number;
  remainingTodayUsd: number;
  reason?: string;
}

/**
 * Calculated gas cost breakdown in native units (wei) and USD/USDC
 */
export interface GasEstimate {
  maxCostWei: bigint;
  maxCostUsdc: number;
  verificationGasLimit: bigint;
  callGasLimit: bigint;
  preVerificationGas: bigint;
  maxFeePerGas: bigint;
  maxPriorityFeePerGas: bigint;
}

/**
 * Standard JSON-RPC 2.0 Request payload
 */
export interface JsonRpcRequest {
  jsonrpc: '2.0';
  id: number | string;
  method: string;
  params: unknown[];
}

/**
 * Standard JSON-RPC 2.0 Response payload
 */
export interface JsonRpcResponse<T = unknown> {
  jsonrpc: '2.0';
  id: number | string;
  result?: T;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}
