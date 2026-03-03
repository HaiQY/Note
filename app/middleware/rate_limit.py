from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import threading

class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def _cleanup_old_requests(self, client_id: str):
        """清理过期请求记录"""
        now = datetime.now()
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if now - req_time < timedelta(hours=1)
        ]
    
    def is_allowed(self, client_id: str) -> tuple[bool, str]:
        """检查是否允许请求"""
        with self._lock:
            now = datetime.now()
            self._cleanup_old_requests(client_id)
            
            minute_ago = now - timedelta(minutes=1)
            requests_last_minute = sum(1 for t in self._requests[client_id] if t > minute_ago)
            
            if requests_last_minute >= self.requests_per_minute:
                return False, f"请求过于频繁，请稍后再试 (限制: {self.requests_per_minute}/分钟)"
            
            if len(self._requests[client_id]) >= self.requests_per_hour:
                return False, f"请求次数已达上限 (限制: {self.requests_per_hour}/小时)"
            
            self._requests[client_id].append(now)
            return True, ""


rate_limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    """限流中间件"""
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    client_id = request.client.host if request.client else "unknown"
    if "authorization" in request.headers:
        client_id = request.headers["authorization"][:50]
    
    allowed, message = rate_limiter.is_allowed(client_id)
    if not allowed:
        raise HTTPException(status_code=429, detail=message)
    
    return await call_next(request)