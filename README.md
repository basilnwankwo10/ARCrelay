# ⚡ ArcRelay

<p align="center">
  <strong>The Gasless Economic Layer for Arc (Circle Ecosystem / Native USDC Gas)</strong><br>
  <em>ERC-4337 v0.7 Paymaster-as-a-Service & Multi-Tenant Corporate Gas Infrastructure.</em>
</p>

<p align="center">
  <a href="https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096"><img src="https://img.shields.io/badge/Arc_Testnet-Chain_5042002-0052FF?style=flat-square&logo=circle&logoColor=white" alt="Arc Testnet"></a>
  <a href="https://eips.ethereum.org/EIPS/eip-4337"><img src="https://img.shields.io/badge/ERC--4337-v0.7_Standard-8A2BE2?style=flat-square" alt="ERC-4337 v0.7"></a>
  <a href="https://www.python.org/downloads/release/python-3120/"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="https://twitter.com/ArcRelayHQ"><img src="https://img.shields.io/badge/X-@ArcRelayHQ-000000?style=flat-square&logo=x&logoColor=white" alt="X @ArcRelayHQ"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT"></a>
</p>

---

## 📖 Overview

**Arc** is Circle's flagship blockchain where **native USDC** powers both application liquidity and network gas fees. While native USDC gas eliminates the volatility of legacy gas tokens, mainstream users and consumer fintech apps still face high onboarding drop-off whenever hit with gas approval prompts, fee calculations, and balance management.

**ArcRelay** solves this by delivering **Paymaster-as-a-Service for Arc**:
* **100% Invisible Gas**: End users transact with **$0.00 gas fees** and zero gas popups.
* **Corporate Gas Tanks**: Enterprise dApps, games, and fintechs pre-fund gas balances with native USDC (or credit card via Circle Onramp Kit).
* **Cryptographic Safety**: Off-chain **EIP-712 authorization signatures** paired with an atomic sliding-window rate limiter ($1.00/day per user default) prevent treasury drainage.
* **Economic Model**: Predictable, transparent volume convenience markup (5%–8%) on sponsored gas volume.

---

## 🏛️ The Complete "Invisible Web3" Stack

ArcRelay pairs natively with Circle's App Kits to create a seamless Web2-grade onboarding experience:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Identity & Account                                  │
│    - Social Login / WebAuthn Passkeys (No seed phrases)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Account Funding (Circle Onramp Kit)                      │
│    - Embedded in-app fiat-to-USDC via Apple Pay / Debit Card│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Gasless Execution (ArcRelay Paymaster)                   │
│    - ERC-4337 v0.7 Paymaster & EIP-712 Policy Router        │
│    - $0 gas prompts for user; settled via Corporate Tank    │
└─────────────────────────────────────────────────────────────┘
```

---

## ⛓️ Live On-Chain Deployments (Arc Testnet)

| Component | Network | Contract Address / Hash | Explorer Link |
| :--- | :--- | :--- | :--- |
| **Canonical EntryPoint** | Arc Testnet (`5042002`) | `0x0000000071727De22E5E9d8BAf0edAc6f37da032` | [View on Arcscan](https://testnet.arcscan.app/address/0x0000000071727De22E5E9d8BAf0edAc6f37da032) |
| **ArcRelayPaymaster** | Arc Testnet (`5042002`) | `0x600c83F91464440A1Fc2c4C723C78e2f51F43096` | [View on Arcscan](https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096) |
| **Verified Genesis Gasless Tx** | Arc Testnet (`Block 64122404`) | `0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef` | [View Proof on Arcscan](https://testnet.arcscan.app/tx/0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef) |

> **Genesis Proof Results:** Test user with **0.000000 USDC** executed an on-chain smart contract call paying **$0.00 gas**. ArcRelayPaymaster covered the transaction fee from the corporate gas tank.

---

## 📁 Repository Structure

```
ARCrelay/
├── contracts/               # EVM Solidity workspace (Hardhat v2.28, Solidity 0.8.24)
│   ├── contracts/
│   │   ├── ArcRelayPaymaster.sol   # ERC-4337 v0.7 paymaster with EIP-712 validation
│   │   ├── interfaces/             # Canonical IEntryPoint, IPaymaster, PackedUserOperation
│   │   └── test/ArcTestAccount.sol # Minimal smart account for gasless testing
│   └── test/                       # 13/13 passing Hardhat unit tests
│
├── policy_engine/           # Python 3.12 Async Policy Router & Signing Daemon
│   ├── src/arcrelay_policy/
│   │   ├── signer.py        # Cryptographic EIP-712 sponsorship signer
│   │   ├── rate_limiter.py  # Sliding-window atomic quota manager ($1/day)
│   │   ├── models.py        # Pydantic v2 ERC-4337 data models
│   │   └── server.py        # aiohttp + orjson JSON-RPC 2.0 / REST server
│   └── tests/               # 14/14 passing pytest tests (mypy --strict clean)
│
├── assets/                  # Official brand assets (Avatar, 16:9 Header banner)
└── PROGRESS.md              # Master 60-day roadmap execution log
```

---

## 🚀 Quickstart & Developer Integration

### 1. Developer Client SDK (Preview)

```typescript
import { ArcRelay } from "@arcrelay/sdk";

// Initialize client
const arcrelay = new ArcRelay({
  apiKey: "arc_live_YOUR_API_KEY",
  policyId: "0x725e4501...50eb",
});

// Sponsor any ERC-4337 UserOperation in 1 line
const sponsoredUserOp = await arcrelay.sponsor(userOp);
```

### 2. Pre-Funding Corporate Gas Tanks

Corporate apps deposit native USDC directly into `ArcRelayPaymaster.sol`:

```solidity
// Direct on-chain deposit
paymaster.depositFor{value: 100 ether}(policyId);
```
*Funds are automatically credited to the client's internal policy tank and staked into the canonical EntryPoint for instant execution liquidity.*

---

## 🗺️ Master Roadmap & Sprint Log

* [x] **Phase 0: Genesis & Strategy** — Business plan, unit economics, architecture.
* [x] **Sprint 1: The Engine (Days 1–14)** — Completed in **48 hours**! Verified live gasless transaction on Arc Testnet (`Tx 0x29a6...4aef`).
* [ ] **Sprint 2: The Product & SDK (Days 15–30)** — Active: `@ArcRelayHQ` social launch, 3-line `@arcrelay/sdk` in TypeScript & Python, B2B landing page.
* [ ] **Sprint 3: Ecosystem Grants & Pilots (Days 31–45)** — Arc Ecosystem Fund grant submission, onboarding first 5 closed-beta apps.
* [ ] **Sprint 4: Commercial Cloud Launch (Days 46–60)** — Mainnet deployment & billing activation.

---

## 👥 Core Team & Community

* **Lead Founder & Architect:** Basil Chinaza Nwankwo ([@kryptbamba](https://twitter.com/kryptbamba))
* **Official Project Handle:** [@ArcRelayHQ](https://twitter.com/ArcRelayHQ)
* **Website:** [arcrelay.tech](https://arcrelay.tech)
* **License:** MIT License
