import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from .settings import settings

_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def enforce_auth_rate_limit(request: Request, action: str) -> None:
    """单实例基础限流；多实例部署时再替换为 Redis 共享实现。"""
    forwarded = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip() if settings.trust_proxy_headers else ""
    client_ip = forwarded or (request.client.host if request.client else "unknown")
    key = f"{action}:{client_ip}"
    now = time.monotonic()
    window = settings.auth_rate_window_seconds
    limit = settings.auth_rate_limit if action == "login" else max(3, settings.auth_rate_limit // 2)
    with _lock:
        bucket = _attempts[key]
        while bucket and now - bucket[0] >= window:
            bucket.popleft()
        # 顺手清理一小批已经完全过期的来源，避免公网长期运行时字典只增不减。
        if len(_attempts) > 1024:
            stale_keys = [
                item_key for item_key, timestamps in list(_attempts.items())[:128]
                if not timestamps or now - timestamps[-1] >= window
            ]
            for stale_key in stale_keys:
                if stale_key != key:
                    _attempts.pop(stale_key, None)
        if len(bucket) >= limit:
            retry_after = max(1, int(window - (now - bucket[0])))
            raise HTTPException(429, "操作过于频繁，请稍后再试", headers={"Retry-After": str(retry_after)})
        bucket.append(now)
