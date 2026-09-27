# @arcrelay/sdk ⚡

[![npm version](https://img.shields.io/badge/npm-v0.1.0-blue.svg?style=flat-square)](https://www.npmjs.com/package/@arcrelay/sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Arc Testnet](https://img.shields.io/badge/Arc_Testnet-Chain_5042002-0052FF?style=flat-square)](https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096)
[![ERC-4337](https://img.shields.io/badge/ERC--4337-v0.7_Standard-8A2BE2?style=flat-square)](https://eips.ethereum.org/EIPS/eip-4337)

The official 3-line TypeScript/JavaScript client for **ArcRelay** — The Gasless Economic Layer for Arc (Circle Ecosystem / Native USDC Gas).

Enable **100% invisible gas** for your users. Pre-fund a corporate gas tank in native USDC and let users transact without gas popups, gas calculations, or token approvals.

---

## 📦 Installation

```bash
npm install @arcrelay/sdk
# or
pnpm add @arcrelay/sdk
# or
yarn add @arcrelay/sdk
```

---

## ⚡ Quickstart (3 Lines of Code)

```typescript
import { ArcRelay } from '@arcrelay/sdk';

// 1. Initialize client with your Policy ID
const arcrelay = new ArcRelay({
  rpcUrl: 'https://relay.arcrelay.tech',
  policyId: '0x0000000000000000000000000000000000000000000000000000000000000001',
});

// 2. Sponsor any ERC-4337 UserOperation in 1 call
const sponsoredUserOp = await arcrelay.sponsor(userOp);

// 3. Submit to bundler (Permissionless.js, Biconomy, ZeroDev, or standard EntryPoint)
const userOpHash = await bundlerClient.sendUserOperation({
  userOperation: sponsoredUserOp,
});
```

---

## 🛠️ Features

* **ERC-4337 v0.7 Native**: Built specifically for the v0.7 `PackedUserOperation` standard.
* **Zero Bloat**: Zero external dependencies. Uses standard `fetch` API.
* **Flexible Input**: Accepts both packed (`accountGasLimits`, `gasFees`) and unpacked (`verificationGasLimit`, `callGasLimit`, `maxFeePerGas`) gas parameters.
* **Automatic Rate Limit Safety**: Enforces application daily spend limits and returns typed `RateLimitExceededError`.
* **Viem & Permissionless.js Ready**: Drop-in compatible via `getPaymasterStubData` and `getPaymasterData`.

---

## 💡 Checking Daily Policy Allowance

Query remaining gas sponsorship quota before submitting transactions:

```typescript
const limits = await arcrelay.getPolicyLimits('0xUserAddress...');

console.log(`Allowed: ${limits.allowed}`);
console.log(`Consumed today: $${limits.consumedTodayUsd}`);
console.log(`Remaining quota: $${limits.remainingTodayUsd}`);
```

---

## 📊 Estimating USDC Gas Cost

```typescript
const estimate = arcrelay.estimateGasCost(userOp);

console.log(`Max cost in native wei: ${estimate.maxCostWei}`);
console.log(`Estimated USDC cost: $${estimate.maxCostUsdc}`);
```

---

## 🛡️ Error Handling

```typescript
import { ArcRelay, RateLimitExceededError, PolicyValidationError, NetworkTimeoutError } from '@arcrelay/sdk';

try {
  const sponsored = await arcrelay.sponsor(userOp);
} catch (err) {
  if (err instanceof RateLimitExceededError) {
    console.error('User exceeded daily $1.00 gas cap:', err.consumedTodayUsd);
  } else if (err instanceof PolicyValidationError) {
    console.error('Invalid parameters:', err.message);
  } else if (err instanceof NetworkTimeoutError) {
    console.error('ArcRelay policy engine timeout:', err.timeoutMs);
  }
}
```

---

## 🌐 Arc Testnet Deployment Information

* **Network**: Arc Testnet
* **Chain ID**: `5042002`
* **EntryPoint (v0.7)**: `0x0000000071727De22E5E9d8BAf0edAc6f37da032`
* **ArcRelayPaymaster**: [`0x600c83F91464440A1Fc2c4C723C78e2f51F43096`](https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096)
* **Gas Token**: Native USDC

---

## 📜 License

MIT © [ArcRelay (@ArcRelayHQ)](https://twitter.com/ArcRelayHQ)
