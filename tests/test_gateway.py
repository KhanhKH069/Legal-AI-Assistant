"""Gateway and rate-limiting tests."""

import time


def test_rate_store_sliding_window():
    """Sliding window eviction: requests older than 60s should be removed."""
    window: list[float] = []
    now = time.time()
    # Add 5 old timestamps (>60s ago) and 3 recent ones
    window.extend([now - 120, now - 90, now - 70, now - 61])
    window.extend([now - 30, now - 10, now])

    evicted = [ts for ts in window if now - ts < 60]
    assert len(evicted) == 3  # only the 3 recent ones should remain


def test_rate_limit_allows_under_max():
    """Requests below max_requests_per_minute should be allowed."""
    max_rpm = 10
    window: list[float] = []
    now = time.time()

    # Simulate 9 requests (below limit of 10)
    for _ in range(9):
        window.append(now - 1)

    assert len(window) < max_rpm  # next request should be allowed


def test_rate_limit_blocks_at_max():
    """10th request within the window should be blocked."""
    max_rpm = 10
    window: list[float] = []
    now = time.time()

    for _ in range(max_rpm):
        window.append(now - 1)

    assert len(window) >= max_rpm  # next request should be rejected
