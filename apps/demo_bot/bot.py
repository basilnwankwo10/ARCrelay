"""ArcRelay Dedicated Public Demo Telegram Bot (@ArcRelayDemo_bot).

Delivers an interactive, 1-tap gasless sponsorship demonstration for partners,
investors, and developers on Arc, with a private Founder Admin Panel (/admin).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "demo_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("arcrelay-demo-bot")

TELEGRAM_API_BASE = "https://api.telegram.org/bot"
MAX_TG_MESSAGE_LEN = 4000


def clean_telegram_text(text: str) -> str:
    """Strips all asterisks, markdown hashtags/headers, and cleans formatting."""
    if not text:
        return text
    text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = text.replace("#", "")
    text = re.sub(r"^\s*[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    text = text.replace("*", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class LeadTracker:
    """Manages persistent lead storage and access analytics."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._data: dict[str, Any] = {
            "realtime_alerts": True,
            "total_demos": 0,
            "unique_users": {},
            "leads": [],
        }
        self.load()

    def load(self) -> None:
        if self.db_path.is_file():
            try:
                self._data = json.loads(self.db_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Error loading leads database: %s", e)

    def save(self) -> None:
        try:
            self.db_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except OSError as e:
            logger.error("Error saving leads database: %s", e)

    @property
    def realtime_alerts(self) -> bool:
        return bool(self._data.get("realtime_alerts", True))

    def toggle_alerts(self) -> bool:
        new_val = not self.realtime_alerts
        self._data["realtime_alerts"] = new_val
        self.save()
        return new_val

    def record_interaction(
        self, user_id: int, username: str, first_name: str, action: str, details: str = ""
    ) -> None:
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        uid_str = str(user_id)

        # Update unique user profile
        self._data.setdefault("unique_users", {})
        self._data["unique_users"][uid_str] = {
            "username": username,
            "first_name": first_name,
            "last_seen": now_utc,
        }

        if action == "demo":
            self._data["total_demos"] = self._data.get("total_demos", 0) + 1

        self._data.setdefault("leads", [])
        self._data["leads"].append(
            {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "action": action,
                "details": details,
                "timestamp": now_utc,
            }
        )
        self.save()

    def get_stats(self) -> dict[str, Any]:
        return {
            "unique_visitors": len(self._data.get("unique_users", {})),
            "total_demos": self._data.get("total_demos", 0),
            "total_leads": len(self._data.get("leads", [])),
            "alerts_enabled": self.realtime_alerts,
        }

    def get_recent_leads(self, count: int = 5) -> list[dict[str, Any]]:
        leads = self._data.get("leads", [])
        return leads[-count:]


class ArcRelayDemoBot:
    """Standalone public Telegram bot with private Founder Admin Panel."""

    def __init__(self, token: str, owner_id: int | None = None, proxy: str | None = None) -> None:
        if not token or token == "your_botfather_token_here":
            raise ValueError("Invalid bot token. Please configure DEMO_BOT_TOKEN in .env")

        self.token = token
        self.owner_id = owner_id
        self.proxy = proxy
        self.api_url = f"{TELEGRAM_API_BASE}{token}"
        self.offset = 0
        self.offset_file = Path(__file__).parent / "demo_offset.json"
        if self.offset_file.is_file():
            try:
                self.offset = int(json.loads(self.offset_file.read_text(encoding="utf-8")).get("offset", 0))
            except (json.JSONDecodeError, OSError, ValueError) as e:
                logger.debug("Could not read offset file: %s", e)
                self.offset = 0

        self.tracker = LeadTracker(Path(__file__).parent / "leads.json")

    def save_offset(self) -> None:
        try:
            self.offset_file.write_text(json.dumps({"offset": self.offset}), encoding="utf-8")
        except OSError as e:
            logger.debug("Could not save offset file: %s", e)

    async def send_message(
        self,
        client: httpx.AsyncClient,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        text = clean_telegram_text(text)
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = await client.post(f"{self.api_url}/sendMessage", json=payload, timeout=20.0)
            if resp.status_code != 200:
                logger.warning("sendMessage failed: %s %s", resp.status_code, resp.text)
        except (httpx.HTTPError, OSError) as e:
            logger.error("Exception in sendMessage: %s", e)

    async def answer_callback_query(
        self, client: httpx.AsyncClient, callback_query_id: str, text: str = ""
    ) -> None:
        try:
            await client.post(
                f"{self.api_url}/answerCallbackQuery",
                json={"callback_query_id": callback_query_id, "text": text},
                timeout=10.0,
            )
        except (httpx.HTTPError, OSError) as e:
            logger.debug("Failed to answer callback query: %s", e)

    async def notify_founder(self, client: httpx.AsyncClient, notification: str) -> None:
        """Sends lead alert to founder ONLY IF realtime alerts are enabled."""
        if not self.owner_id or not self.tracker.realtime_alerts:
            return
        await self.send_message(client, self.owner_id, notification)

    def get_main_menu_keyboard(self) -> dict[str, Any]:
        """Returns the public interactive inline keyboard."""
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "⚡ Run Gasless Sponsor Demo",
                        "callback_data": "run_demo",
                    }
                ],
                [
                    {
                        "text": "🌐 Visit arcrelay.tech",
                        "url": "https://arcrelay.tech",
                    },
                    {
                        "text": "📦 View Developer SDK",
                        "callback_data": "view_sdk",
                    },
                ],
                [
                    {
                        "text": "📝 Apply for Pilot ($500 Gas Credit)",
                        "callback_data": "apply_pilot",
                    }
                ],
                [
                    {
                        "text": "🔍 View Verified Tx on Arcscan",
                        "url": "https://testnet.arcscan.app/tx/0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef",
                    }
                ],
            ]
        }

    def get_admin_dashboard_text(self) -> str:
        """Constructs the private founder dashboard text."""
        stats = self.tracker.get_stats()
        alerts_status = "ACTIVE 🔔" if stats["alerts_enabled"] else "MUTED 🔕"

        recent = self.tracker.get_recent_leads(count=5)
        recent_lines = []
        if recent:
            for r in reversed(recent):
                recent_lines.append(
                    f"• @{r['username']} ({r['first_name']}): {r['action'].upper()} at {r['timestamp']}"
                )
        else:
            recent_lines.append("• No interactions recorded yet.")

        leads_formatted = "\n".join(recent_lines)

        return (
            "👑 ArcRelay Founder Command Center\n\n"
            "📊 Traffic & Interaction Analytics:\n"
            f"• Unique Visitors: {stats['unique_visitors']}\n"
            f"• Gasless Demos Run: {stats['total_demos']}\n"
            f"• Total Logged Events: {stats['total_leads']}\n"
            f"• Real-Time Telegram Alerts: {alerts_status}\n\n"
            "📋 Recent Activity (Last 5):\n"
            f"{leads_formatted}\n\n"
            "Only you (Owner ID: 8059484922) can view this panel."
        )

    def get_admin_keyboard(self) -> dict[str, Any]:
        """Returns the private admin controls keyboard."""
        alerts_btn = "🔕 Mute Alerts" if self.tracker.realtime_alerts else "🔔 Enable Alerts"
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 Refresh Stats", "callback_data": "admin_refresh"},
                    {"text": alerts_btn, "callback_data": "admin_toggle_alerts"},
                ],
                [
                    {"text": "📋 View Recent 10 Leads", "callback_data": "admin_view_leads"},
                ],
                [
                    {"text": "🌐 Visit Portal", "url": "https://arcrelay.tech"},
                ],
            ]
        }

    async def handle_update(self, client: httpx.AsyncClient, update: dict[str, Any]) -> None:
        # 1. Handle Inline Button Clicks
        callback = update.get("callback_query")
        if callback:
            cb_id = callback.get("id")
            cb_data = callback.get("data")
            from_user = callback.get("from", {})
            chat_id = callback.get("message", {}).get("chat", {}).get("id")
            username = from_user.get("username", "Anonymous")
            first_name = from_user.get("first_name", "User")
            user_id = from_user.get("id")

            await self.answer_callback_query(client, cb_id)

            # --- Admin Callbacks (Owner Only) ---
            if cb_data and cb_data.startswith("admin_"):
                if user_id != self.owner_id:
                    await self.send_message(client, chat_id, "⛔ Access denied.")
                    return

                if cb_data == "admin_refresh":
                    await self.send_message(
                        client, chat_id, self.get_admin_dashboard_text(), reply_markup=self.get_admin_keyboard()
                    )
                    return

                if cb_data == "admin_toggle_alerts":
                    new_state = self.tracker.toggle_alerts()
                    status_text = "ENABLED 🔔 (You will receive a notification for each visitor interaction)" if new_state else "MUTED 🔕 (Alerts will be saved silently to /admin)"
                    await self.send_message(
                        client,
                        chat_id,
                        f"Real-Time Alerts are now {status_text}",
                        reply_markup=self.get_admin_keyboard(),
                    )
                    return

                if cb_data == "admin_view_leads":
                    recent = self.tracker.get_recent_leads(count=10)
                    lead_entries = []
                    for r in reversed(recent):
                        detail_str = f" - '{r['details']}'" if r.get("details") else ""
                        lead_entries.append(
                            f"• @{r['username']} ({r['first_name']}) [ID: {r['user_id']}]\n  Action: {r['action'].upper()}{detail_str}\n  Time: {r['timestamp']}"
                        )
                    msg_leads = "📋 Recent 10 Visitor Logs:\n\n" + ("\n\n".join(lead_entries) if lead_entries else "No logs yet.")
                    await self.send_message(client, chat_id, msg_leads, reply_markup=self.get_admin_keyboard())
                    return

            # --- Public Callbacks ---
            if cb_data == "run_demo" and chat_id:
                # Record in database
                self.tracker.record_interaction(user_id, username, first_name, "demo")

                # Send response to the user
                intro = (
                    "⚡ ArcRelay Gasless Sponsorship Initiated!\n\n"
                    "Simulating live ERC-4337 v0.7 UserOperation on Arc Testnet (Chain ID 5042002):\n\n"
                    "• User Smart Account: 0x17887CE04165076d7d9ec251380d0A7Ab4c272D8\n"
                    "• Initial User Gas Balance: 0.00 USDC\n"
                    "• Paymaster Contract: 0x600c83F91464440A1Fc2c4C723C78e2f51F43096\n"
                    "• Standard: ERC-4337 v0.7 EntryPoint"
                )
                await self.send_message(client, chat_id, intro)

                await asyncio.sleep(1.2)

                result = (
                    "🎉 TRANSACTION MINED & EXECUTED!\n\n"
                    "• Status: SUCCESS (0.00 Gas Paid by User)\n"
                    "• Network: Arc Testnet (Chain ID 5042002)\n"
                    "• Block Number: 64,122,404\n"
                    "• Tx Hash: 0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef\n"
                    "• User Gas Cost: $0.0000 USDC\n"
                    "• Corporate Gas Tank Deduction: 0.0033 USDC\n"
                    "• Gasless Execution Time: 2.1 seconds\n\n"
                    "How to integrate this into your dApp:\n"
                    "import { ArcRelay } from '@arcrelay/sdk';\n"
                    "await arcrelay.sponsor(tx);\n\n"
                    "Explore the live portal: https://arcrelay.tech"
                )

                kb = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "🔍 View Live Proof on Arcscan",
                                "url": "https://testnet.arcscan.app/tx/0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef",
                            }
                        ],
                        [
                            {
                                "text": "📝 Apply for Pilot ($500 Credit)",
                                "callback_data": "apply_pilot",
                            }
                        ],
                    ]
                }
                await self.send_message(client, chat_id, result, reply_markup=kb)

                # Send founder notification ONLY to owner_id if alerts are enabled
                if user_id != self.owner_id:
                    await self.notify_founder(
                        client,
                        f"🔔 New Visitor Lead on @ArcRelayDemo_bot!\n\n"
                        f"• User: @{username} ({first_name})\n"
                        f"• User ID: {user_id}\n"
                        f"• Action: Executed 1-Tap Gasless Demo",
                    )
                return

            if cb_data == "view_sdk" and chat_id:
                self.tracker.record_interaction(user_id, username, first_name, "view_sdk")
                sdk_info = (
                    "📦 ArcRelay Developer SDK (TypeScript & Python)\n\n"
                    "Integrate invisible gas in 3 lines of code:\n\n"
                    "TypeScript (@arcrelay/sdk):\n"
                    "import { ArcRelay } from '@arcrelay/sdk';\n"
                    "const relay = new ArcRelay({ policyId: '0x...' });\n"
                    "const sponsoredOp = await relay.sponsor(userOp);\n\n"
                    "Python (arcrelay-sdk):\n"
                    "from arcrelay import ArcRelay\n"
                    "async with ArcRelay(policy_id='0x...') as relay:\n"
                    "    sponsored_op = await relay.sponsor(user_op)\n\n"
                    "• Full ERC-4337 v0.7 compatibility\n"
                    "• Zero external dependencies\n"
                    "• Automatic rate-limiting and fraud protection"
                )
                kb = {
                    "inline_keyboard": [
                        [
                            {"text": "📦 GitHub Repository", "url": "https://github.com/basilnwankwo10/ARCrelay"},
                            {"text": "⚡ Run Demo", "callback_data": "run_demo"},
                        ]
                    ]
                }
                await self.send_message(client, chat_id, sdk_info, reply_markup=kb)
                return

            if cb_data == "apply_pilot" and chat_id:
                self.tracker.record_interaction(user_id, username, first_name, "apply_pilot")
                pilot_info = (
                    "📝 ArcRelay Closed Beta Pilot Program\n\n"
                    "We are onboarding 5 launch partners across Fintech, Gaming, DeFi, and AI Agents.\n\n"
                    "What selected pilot teams receive:\n"
                    "• $500 in free native USDC gas sponsorship credits\n"
                    "• Dedicated integration engineering support\n"
                    "• Featured promotion on @ArcRelayHQ and Circle Arc showcases\n\n"
                    "To apply:\n"
                    "1. Visit https://arcrelay.tech and submit the pilot form\n"
                    "2. OR simply reply to this bot with your Project Name and Category!"
                )
                kb = {
                    "inline_keyboard": [
                        [{"text": "🌐 Open Pilot Form on Website", "url": "https://arcrelay.tech"}],
                        [{"text": "⚡ Run Demo First", "callback_data": "run_demo"}],
                    ]
                }
                await self.send_message(client, chat_id, pilot_info, reply_markup=kb)
                return

        # 2. Handle Text Messages
        msg = update.get("message")
        if not msg:
            return

        chat_id = msg.get("chat", {}).get("id")
        user = msg.get("from", {})
        username = user.get("username", "Anonymous")
        first_name = user.get("first_name", "Friend")
        user_id = user.get("id")
        text = msg.get("text", "").strip()

        if not chat_id or not text:
            return

        logger.info("Message from %s (@%s) [ID: %s]: %s", first_name, username, user_id, text[:50])

        # Secret Admin Command (Owner Only)
        if text.lower() == "/admin":
            if user_id != self.owner_id:
                await self.send_message(client, chat_id, "⛔ Access denied. Founder command only.")
                return

            await self.send_message(
                client, chat_id, self.get_admin_dashboard_text(), reply_markup=self.get_admin_keyboard()
            )
            return

        # Start / Help Menu
        if text.lower() in ("/start", "/help", "hi", "hello", "menu"):
            self.tracker.record_interaction(user_id, username, first_name, "start")
            welcome = (
                f"⚡ Welcome to ArcRelay, {first_name}!\n\n"
                "ArcRelay is the Gasless Economic Layer for Arc (Circle Ecosystem / Native USDC Gas).\n\n"
                "We provide ERC-4337 v0.7 Paymaster-as-a-Service and multi-tenant corporate gas tanks so your users enjoy 100% invisible gas with zero popups.\n\n"
                "Tap a button below to test live sponsorship or explore the SDK:"
            )
            await self.send_message(client, chat_id, welcome, reply_markup=self.get_main_menu_keyboard())
            return

        # Direct demo trigger
        if text.lower() in ("/demo", "/sponsor", "demo", "sponsor"):
            self.tracker.record_interaction(user_id, username, first_name, "demo_text")
            intro = (
                "⚡ ArcRelay 1-Tap Gasless Sponsorship Executed!\n\n"
                "• Status: SUCCESS (Mined in Block 64,122,404)\n"
                "• Network: Arc Testnet (Chain ID 5042002)\n"
                "• Gas Paid by User: $0.0000 USDC\n"
                "• Tx Hash: 0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef\n\n"
                "Arcscan Link: https://testnet.arcscan.app/tx/0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef\n\n"
                "Visit our portal: https://arcrelay.tech"
            )
            await self.send_message(client, chat_id, intro, reply_markup=self.get_main_menu_keyboard())
            return

        # Pilot Application or Message from Visitor
        self.tracker.record_interaction(user_id, username, first_name, "message", details=text)

        reply = (
            f"Thank you, {first_name}! Your message has been received by the ArcRelay team.\n\n"
            "If you submitted a pilot application, our team will review your project and whitelist your gas sponsorship credits.\n\n"
            "Official Portal: https://arcrelay.tech\n"
            "Follow updates on X: https://twitter.com/ArcRelayHQ"
        )
        await self.send_message(client, chat_id, reply, reply_markup=self.get_main_menu_keyboard())

        # Forward lead directly to founder if enabled
        if user_id != self.owner_id:
            await self.notify_founder(
                client,
                f"📩 New Pilot Lead / Inquiry on @ArcRelayDemo_bot!\n\n"
                f"• From: @{username} ({first_name})\n"
                f"• User ID: {user_id}\n"
                f"• Message:\n\"{text}\"",
            )

    async def run(self) -> None:
        """Main long-polling loop with exponential backoff and proxy support."""
        logger.info("Starting @ArcRelayDemo_bot long-polling daemon with Founder Admin...")
        backoff = 1.0

        mounts = {}
        if self.proxy:
            mounts = {
                "http://": httpx.AsyncHTTPTransport(proxy=self.proxy),
                "https://": httpx.AsyncHTTPTransport(proxy=self.proxy),
            }

        async with httpx.AsyncClient(timeout=35.0, mounts=mounts) as client:
            while True:
                try:
                    resp = await client.get(
                        f"{self.api_url}/getUpdates",
                        params={"offset": self.offset, "timeout": 20, "allowed_updates": json.dumps(["message", "callback_query"])},
                    )
                    if resp.status_code == 200:
                        backoff = 1.0
                        data = resp.json()
                        updates = data.get("result", [])
                        for update in updates:
                            update_id = update.get("update_id", 0)
                            if update_id >= self.offset:
                                self.offset = update_id + 1
                                self.save_offset()
                            try:
                                await self.handle_update(client, update)
                            except Exception:
                                logger.exception("Error handling update %s", update_id)
                    elif resp.status_code in (401, 404):
                        logger.critical("Bot token invalid (HTTP %s). Exiting.", resp.status_code)
                        print(f"ERROR: Bot token rejected by Telegram (HTTP {resp.status_code}). Check .env file.")
                        return
                    else:
                        logger.warning("getUpdates returned HTTP %s: %s", resp.status_code, resp.text)
                        await asyncio.sleep(min(backoff, 30.0))
                        backoff = min(backoff * 1.5, 30.0)
                except httpx.TimeoutException:
                    pass
                except (httpx.HTTPError, OSError) as e:
                    logger.warning("Polling error: %s. Retrying in %.1fs...", e, backoff)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5, 30.0)


def main() -> None:
    env_path = Path(__file__).parent / ".env"
    env = dotenv_values(env_path) if env_path.is_file() else {}

    token = os.getenv("DEMO_BOT_TOKEN") or env.get("DEMO_BOT_TOKEN", "")
    owner_str = os.getenv("OWNER_CHAT_ID") or env.get("OWNER_CHAT_ID", "8059484922")
    proxy = os.getenv("PROXY_URL") or env.get("PROXY_URL", "http://127.0.0.1:17891")

    if not token or token == "your_botfather_token_here":
        print(f"⚠️ Please add your BotFather token to: {env_path.resolve()}")
        sys.exit(1)

    owner_id = int(owner_str) if owner_str and owner_str.isdigit() else None
    bot = ArcRelayDemoBot(token=token, owner_id=owner_id, proxy=proxy)
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
