import test from 'node:test';
import assert from 'node:assert/strict';
import {
  ArcRelay,
  ArcRelayClient,
  packGasLimits,
  unpackGasLimits,
  packGasFees,
  unpackGasFees,
  packUserOperation,
  calculateGasCost,
  formatPolicyId,
  normalizeAddress,
  RateLimitExceededError,
  PolicyValidationError,
  NetworkTimeoutError,
  DEFAULT_PAYMASTER_ADDRESS,
  DEFAULT_POLICY_ID,
} from '../dist/index.js';

test('Gas Limits: packGasLimits and unpackGasLimits round-trip', () => {
  const verifGas = 150_000n;
  const callGas = 300_000n;

  const packed = packGasLimits(verifGas, callGas);
  assert.equal(typeof packed, 'string');
  assert.equal(packed.length, 66); // '0x' + 64 hex chars (32 bytes)

  const unpacked = unpackGasLimits(packed);
  assert.equal(unpacked.verificationGasLimit, verifGas);
  assert.equal(unpacked.callGasLimit, callGas);
});

test('Gas Fees: packGasFees and unpackGasFees round-trip', () => {
  const priorityFee = 2_000_000_000n; // 2 gwei
  const maxFee = 25_000_000_000n; // 25 gwei

  const packed = packGasFees(priorityFee, maxFee);
  assert.equal(typeof packed, 'string');
  assert.equal(packed.length, 66);

  const unpacked = unpackGasFees(packed);
  assert.equal(unpacked.maxPriorityFeePerGas, priorityFee);
  assert.equal(unpacked.maxFeePerGas, maxFee);
});

test('packUserOperation: correctly packs unpacked user op input', () => {
  const input = {
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
    nonce: 0,
    initCode: '0x',
    callData: '0x1234',
    verificationGasLimit: 120_000n,
    callGasLimit: 250_000n,
    maxPriorityFeePerGas: 2_000_000_000n,
    maxFeePerGas: 20_000_000_000n,
    preVerificationGas: 50_000n,
  };

  const packed = packUserOperation(input);
  assert.equal(packed.sender, '0x8b397aa41da9383eab34f9a268fcecd86813f7dd');
  assert.equal(packed.callData, '0x1234');
  assert.equal(packed.accountGasLimits.length, 66);
  assert.equal(packed.gasFees.length, 66);
  assert.equal(packed.paymasterAndData, '0x');
  assert.equal(packed.signature, '0x');
});

test('calculateGasCost: computes expected USDC cost on Arc', () => {
  const input = {
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
    verificationGasLimit: 100_000n,
    callGasLimit: 100_000n,
    preVerificationGas: 50_000n,
    maxFeePerGas: 20_000_000_000n, // 20 gwei
    maxPriorityFeePerGas: 2_000_000_000n,
  };

  const estimate = calculateGasCost(input, 100_000n, 50_000n);
  // Total gas: 50k + 100k + 100k + 100k (pm verif) + 50k (pm postOp) = 400k
  // Max cost wei: 400_000 * 20_000_000_000 = 8_000_000_000_000_000 wei
  assert.equal(estimate.maxCostWei, 8_000_000_000_000_000n);
  assert.equal(estimate.maxCostUsdc, 0.008);
});

test('ArcRelayClient: validates configuration on instantiation', () => {
  assert.throws(
    () => new ArcRelayClient({ rpcUrl: '', policyId: '0x1' }),
    PolicyValidationError
  );

  const client = new ArcRelayClient({
    rpcUrl: 'http://localhost:8545',
    policyId: '0x1',
  });

  assert.equal(client.rpcUrl, 'http://localhost:8545');
  assert.equal(client.policyId, formatPolicyId('0x1'));
  assert.equal(client.paymasterAddress, normalizeAddress(DEFAULT_PAYMASTER_ADDRESS));
});

test('ArcRelayClient: 1-line sponsor(userOp) returns sponsored UserOp', async () => {
  const mockSignedData = '0x600c83f91464440a1fc2c4c723c78e2f51f43096000000000000000000000000000186a00000000000000000000000000000c35000006700000000006600' + '11'.repeat(32) + '22'.repeat(65);

  const customFetch = async (url, options) => {
    const body = JSON.parse(options.body);
    assert.equal(body.method, 'pm_sponsorUserOperation');
    assert.equal(body.params[1], formatPolicyId('0x1'));

    return {
      ok: true,
      status: 200,
      json: async () => ({
        jsonrpc: '2.0',
        id: body.id,
        result: {
          paymasterAndData: mockSignedData,
          validUntil: 1790400000,
          validAfter: 1790300000,
          maxCost: '0x1c9c380',
        },
      }),
    };
  };

  const relay = new ArcRelay({
    rpcUrl: 'http://localhost:8545',
    policyId: '0x1',
    customFetch,
  });

  const userOp = {
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
    nonce: 0,
    initCode: '0x',
    callData: '0x1234',
  };

  const sponsored = await relay.sponsor(userOp);
  assert.equal(sponsored.paymasterAndData, mockSignedData);
  assert.equal(sponsored.sender, '0x8b397aa41da9383eab34f9a268fcecd86813f7dd');
});

test('ArcRelayClient: throws RateLimitExceededError when daily quota is reached', async () => {
  const customFetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      jsonrpc: '2.0',
      id: 1,
      error: {
        code: -32001,
        message: 'Rate limit exceeded: Daily spend limit reached',
        data: {
          allowed: false,
          consumed_today_usd: 1.05,
          daily_limit_usd: 1.0,
          remaining_today_usd: 0.0,
        },
      },
    }),
  });

  const relay = new ArcRelay({
    rpcUrl: 'http://localhost:8545',
    policyId: '0x1',
    customFetch,
  });

  const userOp = {
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
  };

  await assert.rejects(
    async () => await relay.sponsor(userOp),
    (err) => {
      assert(err instanceof RateLimitExceededError);
      assert.equal(err.consumedTodayUsd, 1.05);
      assert.equal(err.dailyLimitUsd, 1.0);
      assert.equal(err.remainingTodayUsd, 0.0);
      return true;
    }
  );
});

test('ArcRelayClient: handles network timeout with NetworkTimeoutError', async () => {
  const customFetch = async (url, options) => {
    return new Promise((resolve, reject) => {
      options.signal.addEventListener('abort', () => {
        const err = new Error('The operation was aborted');
        err.name = 'AbortError';
        reject(err);
      });
    });
  };

  const relay = new ArcRelay({
    rpcUrl: 'http://localhost:8545',
    policyId: '0x1',
    timeoutMs: 50,
    customFetch,
  });

  const userOp = {
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
  };

  await assert.rejects(
    async () => await relay.sponsor(userOp),
    (err) => {
      assert(err instanceof NetworkTimeoutError);
      assert.equal(err.timeoutMs, 50);
      return true;
    }
  );
});

test('ArcRelayClient: Viem getPaymasterStubData returns correct 161-byte prefix stub', async () => {
  const relay = new ArcRelay({
    rpcUrl: 'http://localhost:8545',
    policyId: '0x1',
  });

  const stub = await relay.getPaymasterStubData({
    sender: '0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD',
  });

  assert(stub.paymasterAndData.startsWith(DEFAULT_PAYMASTER_ADDRESS.toLowerCase()));
  // Total hex length: 2 chars ('0x') + (20 + 16 + 16 + 109) * 2 = 2 + 322 = 324 chars
  assert.equal(stub.paymasterAndData.length, 324);
});
