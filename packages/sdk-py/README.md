# arcrelay-sdk ⚡

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg?style=flat-square)](https://pypi.org/project/arcrelay-sdk/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![Arc Testnet](https://img.shields.io/badge/Arc_Testnet-Chain_5042002-0052FF?style=flat-square)](https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096)

The official high-performance Python client for **ArcRelay** — The Gasless Economic Layer for Arc (Circle Ecosystem / Native USDC Gas).

Enable **100% invisible gas** for your Python backend services, Telegram trading bots, AI agents, and fintech platforms on Arc.

---

## 📦 Installation

```bash
pip install arcrelay-sdk
# or via uv
uv add arcrelay-sdk
```

---

## ⚡ Quickstart (3 Lines of Code)

```python
import asyncio
from arcrelay import ArcRelay, PackedUserOperation

async def main():
    # 1. Initialize client
    async with ArcRelay(
        rpc_url="https://relay.arcrelay.tech",
        policy_id="0x0000000000000000000000000000000000000000000000000000000000000001",
    ) as arcrelay:
        
        # 2. Sponsor UserOperation in 1 call
        sponsored_op = await arcrelay.sponsor(user_op)
        
        print(f"Sponsored paymasterAndData: {sponsored_op.paymasterAndData[:42]}...")

asyncio.run(main())
```

---

## 🛡️ Daily Spend Quota Checks

```python
limits = await arcrelay.get_policy_limits("0xUserAddress...")

print(f"Allowed: {limits.allowed}")
print(f"Remaining quota today: ${limits.remaining_today_usd}")
```

---

## 📜 License

MIT © [ArcRelay (@ArcRelayHQ)](https://twitter.com/ArcRelayHQ)
