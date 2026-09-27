/**
 * Custom error hierarchy for ArcRelay SDK
 */

/**
 * Base class for all ArcRelay SDK errors
 */
export class ArcRelayError extends Error {
  constructor(message: string, public readonly code?: number | string, public readonly details?: unknown) {
    super(message);
    this.name = 'ArcRelayError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Thrown when an application policy limit or user daily quota is exceeded
 */
export class RateLimitExceededError extends ArcRelayError {
  constructor(
    message: string,
    public readonly consumedTodayUsd?: number,
    public readonly dailyLimitUsd?: number,
    public readonly remainingTodayUsd?: number,
    details?: unknown
  ) {
    super(message, 'RATE_LIMIT_EXCEEDED', details);
    this.name = 'RateLimitExceededError';
  }
}

/**
 * Thrown when parameters fail client or server validation
 */
export class PolicyValidationError extends ArcRelayError {
  constructor(message: string, details?: unknown) {
    super(message, 'VALIDATION_ERROR', details);
    this.name = 'PolicyValidationError';
  }
}

/**
 * Thrown when an HTTP or RPC request exceeds the configured timeout
 */
export class NetworkTimeoutError extends ArcRelayError {
  constructor(message: string, public readonly timeoutMs: number) {
    super(message, 'NETWORK_TIMEOUT', { timeoutMs });
    this.name = 'NetworkTimeoutError';
  }
}

/**
 * Thrown when the policy engine or upstream RPC returns an unrecoverable failure
 */
export class RpcServiceError extends ArcRelayError {
  constructor(message: string, public readonly rpcCode: number, details?: unknown) {
    super(message, rpcCode, details);
    this.name = 'RpcServiceError';
  }
}
