/**
 * ArcRelayClient: The 3-Line Developer Client for ArcRelay Paymaster-as-a-Service
 */

import {
  ARC_TESTNET_CHAIN_ID,
  DEFAULT_PAYMASTER_ADDRESS,
  DEFAULT_PAYMASTER_POST_OP_GAS,
  DEFAULT_PAYMASTER_VERIFICATION_GAS,
  DEFAULT_POLICY_ID,
  DEFAULT_TIMEOUT_MS,
} from './constants.js';
import {
  ArcRelayError,
  NetworkTimeoutError,
  PolicyValidationError,
  RateLimitExceededError,
  RpcServiceError,
} from './errors.js';
import type {
  ArcRelayConfig,
  GasEstimate,
  JsonRpcRequest,
  JsonRpcResponse,
  PackedUserOperation,
  PolicyLimits,
  SponsorshipResult,
  UserOperationInput,
} from './types.js';
import {
  calculateGasCost,
  formatPolicyId,
  normalizeAddress,
  packUserOperation,
} from './utils.js';

export class ArcRelayClient {
  public readonly rpcUrl: string;
  public readonly policyId: string;
  public readonly apiKey?: string;
  public readonly timeoutMs: number;
  public readonly chainId: number;
  public readonly paymasterAddress: string;
  private readonly _fetch: typeof fetch;
  private _requestId = 1;

  constructor(config: ArcRelayConfig) {
    if (!config || !config.rpcUrl) {
      throw new PolicyValidationError('ArcRelayConfig requires a valid "rpcUrl"');
    }

    this.rpcUrl = config.rpcUrl.replace(/\/+$/, '');
    this.policyId = formatPolicyId(config.policyId || DEFAULT_POLICY_ID);
    this.apiKey = config.apiKey;
    this.timeoutMs = config.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.chainId = config.chainId ?? ARC_TESTNET_CHAIN_ID;
    this.paymasterAddress = normalizeAddress(
      config.paymasterAddress || DEFAULT_PAYMASTER_ADDRESS
    );
    this._fetch = config.customFetch ?? globalThis.fetch.bind(globalThis);
  }

  /**
   * Sponsors a UserOperation in a single call.
   * Updates and returns the UserOperation with signed paymasterAndData attached.
   *
   * @example
   * ```typescript
   * const sponsoredOp = await arcrelay.sponsor(userOp);
   * ```
   */
  public async sponsor(userOp: UserOperationInput | PackedUserOperation): Promise<PackedUserOperation> {
    const packedOp = packUserOperation(userOp);
    const sponsorship = await this.getSponsorship(packedOp);

    return {
      ...packedOp,
      paymasterAndData: sponsorship.paymasterAndData,
    };
  }

  /**
   * Requests cryptographic EIP-712 sponsorship from the policy engine.
   *
   * @returns SponsorshipResult containing paymasterAndData and validity window
   */
  public async getSponsorship(userOp: UserOperationInput | PackedUserOperation): Promise<SponsorshipResult> {
    const packedOp = packUserOperation(userOp);

    // Call policy engine RPC: pm_sponsorUserOperation
    const result = await this._sendRpc<SponsorshipResult>('pm_sponsorUserOperation', [
      packedOp,
      this.policyId,
    ]);

    if (!result || !result.paymasterAndData) {
      throw new ArcRelayError('Invalid response from sponsorship service: missing paymasterAndData');
    }

    return result;
  }

  /**
   * Queries the remaining gas sponsorship limits for a given user or sender address.
   */
  public async getPolicyLimits(sender: string): Promise<PolicyLimits> {
    const cleanSender = normalizeAddress(sender);
    const result = await this._sendRpc<PolicyLimits>('pm_getPolicyLimits', [
      this.policyId,
      cleanSender,
    ]);

    return result;
  }

  /**
   * Calculates maximum gas units and estimated native USDC cost for a UserOperation.
   */
  public estimateGasCost(userOp: UserOperationInput | PackedUserOperation): GasEstimate {
    return calculateGasCost(userOp);
  }

  /**
   * Returns a stub paymasterAndData with dummy signature for gas estimation (Viem / Permissionless compatibility).
   */
  public async getPaymasterStubData(
    userOp: UserOperationInput | PackedUserOperation
  ): Promise<{ paymasterAndData: string; isFinal?: boolean }> {
    // 20 bytes paymaster + 16 bytes verif gas + 16 bytes postOp gas + 6 bytes validUntil + 6 bytes validAfter + 32 bytes policyId + 65 bytes dummy signature
    const paymasterClean = this.paymasterAddress.replace(/^0x/i, '');
    const verifGasHex = DEFAULT_PAYMASTER_VERIFICATION_GAS.toString(16).padStart(32, '0');
    const postOpGasHex = DEFAULT_PAYMASTER_POST_OP_GAS.toString(16).padStart(32, '0');
    const dummyPayload = '00'.repeat(109); // 109 bytes dummy payload

    const stub = `0x${paymasterClean}${verifGasHex}${postOpGasHex}${dummyPayload}`;
    return { paymasterAndData: stub, isFinal: false };
  }

  /**
   * Standard Viem / Permissionless paymaster client interface.
   */
  public async getPaymasterData(
    userOp: UserOperationInput | PackedUserOperation
  ): Promise<{ paymasterAndData: string }> {
    const result = await this.getSponsorship(userOp);
    return { paymasterAndData: result.paymasterAndData };
  }

  /**
   * Low-level JSON-RPC 2.0 transport handler with timeout and error classification
   */
  private async _sendRpc<T>(method: string, params: unknown[]): Promise<T> {
    const id = this._requestId++;
    const payload: JsonRpcRequest = {
      jsonrpc: '2.0',
      id,
      method,
      params,
    };

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    let response: Response;
    try {
      // If rpcUrl does not end with /rpc, use standard endpoint
      const targetUrl = this.rpcUrl.endsWith('/rpc') ? this.rpcUrl : `${this.rpcUrl}/rpc`;
      response = await this._fetch(targetUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
    } catch (err: unknown) {
      clearTimeout(timer);
      if (err instanceof Error && err.name === 'AbortError') {
        throw new NetworkTimeoutError(
          `Request to ArcRelay policy engine timed out after ${this.timeoutMs}ms`,
          this.timeoutMs
        );
      }
      throw new ArcRelayError(`Failed to connect to ArcRelay policy engine: ${(err as Error)?.message || err}`);
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new ArcRelayError(
        `ArcRelay service returned HTTP ${response.status}: ${errorText || response.statusText}`,
        response.status
      );
    }

    let jsonResponse: JsonRpcResponse<T>;
    try {
      jsonResponse = (await response.json()) as JsonRpcResponse<T>;
    } catch (err) {
      throw new ArcRelayError(`Failed to parse JSON response from ArcRelay: ${(err as Error)?.message}`);
    }

    if (jsonResponse.error) {
      const { code, message, data } = jsonResponse.error;

      // Rate limit error code
      if (code === -32001) {
        const rateData = data as
          | { consumed_today_usd?: number; daily_limit_usd?: number; remaining_today_usd?: number }
          | undefined;
        throw new RateLimitExceededError(
          message || 'Daily gas sponsorship quota exceeded',
          rateData?.consumed_today_usd,
          rateData?.daily_limit_usd,
          rateData?.remaining_today_usd,
          data
        );
      }

      // Parameter validation error
      if (code === -32602) {
        throw new PolicyValidationError(message, data);
      }

      throw new RpcServiceError(message, code, data);
    }

    return jsonResponse.result as T;
  }
}

/**
 * Convenience alias for ArcRelayClient
 */
export const ArcRelay = ArcRelayClient;
