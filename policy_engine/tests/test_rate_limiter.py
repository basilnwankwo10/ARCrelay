"""Tests for PolicyRateLimiter."""

import pytest

from arcrelay_policy.rate_limiter import PolicyRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_quota():
    limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    policy_id = "0xpolicy1"
    sender = "0xuserA"

    # Consume $0.40 -> should be allowed
    res1 = await limiter.check_and_consume(policy_id, sender, cost_usd=0.40)
    assert res1.allowed is True
    assert res1.consumed_today_usd == pytest.approx(0.40)
    assert res1.remaining_today_usd == pytest.approx(0.60)

    # Consume another $0.50 -> should be allowed ($0.90 total)
    res2 = await limiter.check_and_consume(policy_id, sender, cost_usd=0.50)
    assert res2.allowed is True
    assert res2.consumed_today_usd == pytest.approx(0.90)
    assert res2.remaining_today_usd == pytest.approx(0.10)


@pytest.mark.asyncio
async def test_rate_limiter_rejects_over_quota():
    limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    policy_id = "0xpolicy1"
    sender = "0xuserA"

    # Consume $0.80
    await limiter.check_and_consume(policy_id, sender, cost_usd=0.80)

    # Try consuming $0.30 ($1.10 total > $1.00 limit) -> rejected
    res = await limiter.check_and_consume(policy_id, sender, cost_usd=0.30)
    assert res.allowed is False
    assert "Daily sponsorship limit" in res.reason


@pytest.mark.asyncio
async def test_rate_limiter_custom_policy_limit():
    limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    policy_id = "0xenterprise_app"
    sender = "0xuserVIP"

    await limiter.set_policy_limit(policy_id, daily_limit_usd=10.00)

    # VIP user consumes $5.00 -> allowed
    res = await limiter.check_and_consume(policy_id, sender, cost_usd=5.00)
    assert res.allowed is True
    assert res.remaining_today_usd == pytest.approx(5.00)


@pytest.mark.asyncio
async def test_rate_limiter_user_isolation():
    limiter = PolicyRateLimiter(default_daily_user_limit_usd=1.00)
    policy_id = "0xpolicy1"
    user_a = "0xuserA"
    user_b = "0xuserB"

    # User A consumes $0.90
    await limiter.check_and_consume(policy_id, user_a, cost_usd=0.90)

    # User B should still have full $1.00 quota
    status_b = await limiter.get_user_status(policy_id, user_b)
    assert status_b.consumed_today_usd == 0.0
    assert status_b.remaining_today_usd == 1.00
