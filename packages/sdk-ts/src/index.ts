/**
 * @arcrelay/sdk: Official Developer SDK for ArcRelay
 * The Gasless Economic Layer for Arc (ERC-4337 v0.7 Paymaster)
 */

export { ArcRelay, ArcRelayClient } from './client.js';
export {
  ARC_TESTNET_CHAIN_ID,
  ARC_TESTNET_RPC,
  DEFAULT_ENTRY_POINT_ADDRESS,
  DEFAULT_PAYMASTER_ADDRESS,
  DEFAULT_PAYMASTER_POST_OP_GAS,
  DEFAULT_PAYMASTER_VERIFICATION_GAS,
  DEFAULT_POLICY_ID,
  DEFAULT_TIMEOUT_MS,
} from './constants.js';
export {
  ArcRelayError,
  NetworkTimeoutError,
  PolicyValidationError,
  RateLimitExceededError,
  RpcServiceError,
} from './errors.js';
export type {
  ArcRelayConfig,
  GasEstimate,
  JsonRpcRequest,
  JsonRpcResponse,
  PackedUserOperation,
  PolicyLimits,
  SponsorshipResult,
  UserOperationInput,
} from './types.js';
export {
  calculateGasCost,
  formatPolicyId,
  normalizeAddress,
  packGasFees,
  packGasLimits,
  packUserOperation,
  padHex,
  toBigInt,
  toHex,
  unpackGasFees,
  unpackGasLimits,
} from './utils.js';
