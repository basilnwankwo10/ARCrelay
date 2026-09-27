"""Asynchronous In-Memory Rate Limiter & Spend Tracker for ArcRelay."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from arcrelay_policy.models import RateLimitStatus


@dataclass
class UserSpendRecord:
    """Tracks daily spending for a user address."""

    window_start: float = field(default_factory=time.time)
    spent_usd: float = 0.0


class PolicyRateLimiter:
    """Enforces per-user and per-policy sponsorship spend limits."""

    def __init__(self, default_daily_user_limit_usd: float = 1.00) -> None:
        self.default_daily_user_limit_usd = default_daily_user_limit_usd
        self._policy_limits: dict[str, float] = {}
        # Key: (policy_id, sender_address_lower) => UserSpendRecord
        self._user_records: dict[tuple[str, str], UserSpendRecord] = {}
        self._lock = asyncio.Lock()

    async def set_policy_limit(self, policy_id: str, daily_limit_usd: float) -> None:
        """Sets custom daily limit for a specific policy."""
        async with self._lock:
            self._policy_limits[policy_id.lower()] = daily_limit_usd

    def get_policy_limit(self, policy_id: str) -> float:
        """Gets daily limit for a policy or falls back to default."""
        return self._policy_limits.get(policy_id.lower(), self.default_daily_user_limit_usd)

    async def check_and_consume(
        self, policy_id: str, sender: str, cost_usd: float
    ) -> RateLimitStatus:
        """Checks if user has enough quota and consumes the cost atomically."""
        async with self._lock:
            key = (policy_id.lower(), sender.lower())
            now = time.time()
            limit = self.get_policy_limit(policy_id)

            record = self._user_records.get(key)
            if record is None or (now - record.window_start) >= 86400:
                # Fresh 24-hour window
                record = UserSpendRecord(window_start=now, spent_usd=0.0)
                self._user_records[key] = record

            if record.spent_usd + cost_usd > limit:
                return RateLimitStatus(
                    allowed=False,
                    consumed_today_usd=record.spent_usd,
                    daily_limit_usd=limit,
                    remaining_today_usd=max(0.0, limit - record.spent_usd),
                    reason=f"Daily sponsorship limit of ${limit:.2f} exceeded for user",
                )

            # Consume quota
            record.spent_usd += cost_usd
            remaining = max(0.0, limit - record.spent_usd)

            return RateLimitStatus(
                allowed=True,
                consumed_today_usd=record.spent_usd,
                daily_limit_usd=limit,
                remaining_today_usd=remaining,
            )

    async def get_user_status(self, policy_id: str, sender: str) -> RateLimitStatus:
        """Queries current quota without consuming."""
        async with self._lock:
            key = (policy_id.lower(), sender.lower())
            now = time.time()
            limit = self.get_policy_limit(policy_id)

            record = self._user_records.get(key)
            if record is None or (now - record.window_start) >= 86400:
                return RateLimitStatus(
                    allowed=True,
                    consumed_today_usd=0.0,
                    daily_limit_usd=limit,
                    remaining_today_usd=limit,
                )

            return RateLimitStatus(
                allowed=record.spent_usd < limit,
                consumed_today_usd=record.spent_usd,
                daily_limit_usd=limit,
                remaining_today_usd=max(0.0, limit - record.spent_usd),
            )
