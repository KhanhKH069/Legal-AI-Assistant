"""In-process AI metrics collector for Paraline HR Agent.

Tracks per-request: agent routing, response time, cache hints, user type.
Thread-safe singleton — import get_metrics_collector() from anywhere.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List


@dataclass
class RequestRecord:
    timestamp: float
    user_id: str
    agent_name: str
    response_time_ms: float
    cached: bool
    message_preview: str
    is_guest: bool = False


class MetricsCollector:
    """Thread-safe in-process metrics collector (no external DB needed)."""

    def __init__(self, max_history: int = 200) -> None:
        self._lock = Lock()
        self._history: List[RequestRecord] = []
        self._max_history = max_history
        self._agent_counts: Dict[str, int] = defaultdict(int)
        self._agent_times: Dict[str, List[float]] = defaultdict(list)
        self._total: int = 0
        self._cache_hits: int = 0
        self._guest_requests: int = 0
        self._started_at: float = time.time()

    def record(
        self,
        user_id: str,
        agent_name: str,
        response_time_ms: float,
        *,
        cached: bool = False,
        message_preview: str = "",
        is_guest: bool = False,
    ) -> None:
        with self._lock:
            rec = RequestRecord(
                timestamp=time.time(),
                user_id=user_id if not is_guest else "guest",
                agent_name=agent_name,
                response_time_ms=round(response_time_ms),
                cached=cached,
                message_preview=message_preview[:80],
                is_guest=is_guest,
            )
            self._history.append(rec)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            self._agent_counts[agent_name] += 1
            self._agent_times[agent_name].append(response_time_ms)
            self._total += 1
            if cached:
                self._cache_hits += 1
            if is_guest:
                self._guest_requests += 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            agent_stats: Dict[str, Any] = {}
            for agent, count in sorted(self._agent_counts.items(), key=lambda x: -x[1]):
                times = self._agent_times[agent]
                agent_stats[agent] = {
                    "count": count,
                    "percentage": round(count / self._total * 100, 1)
                    if self._total
                    else 0,
                    "avg_ms": round(sum(times) / len(times)) if times else 0,
                    "min_ms": round(min(times)) if times else 0,
                    "max_ms": round(max(times)) if times else 0,
                }

            all_times = [t for ts in self._agent_times.values() for t in ts]
            avg_overall = round(sum(all_times) / len(all_times)) if all_times else 0

            peak_agent = (
                max(self._agent_counts, key=self._agent_counts.get)
                if self._agent_counts
                else "—"
            )

            recent = [
                {
                    "timestamp": r.timestamp,
                    "user_id": r.user_id,
                    "agent_name": r.agent_name,
                    "response_time_ms": r.response_time_ms,
                    "cached": r.cached,
                    "message_preview": r.message_preview,
                    "is_guest": r.is_guest,
                }
                for r in sorted(self._history, key=lambda x: x.timestamp, reverse=True)[
                    :20
                ]
            ]

            return {
                "total_requests": self._total,
                "employee_requests": self._total - self._guest_requests,
                "guest_requests": self._guest_requests,
                "cache_hits": self._cache_hits,
                "cache_hit_rate": round(self._cache_hits / self._total * 100, 1)
                if self._total
                else 0,
                "avg_response_time_ms": avg_overall,
                "peak_agent": peak_agent,
                "uptime_seconds": round(time.time() - self._started_at),
                "by_agent": agent_stats,
                "recent_requests": recent,
            }


_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    return _collector
