"""Rate limiting utilities for the application."""
from functools import wraps
from flask import request, current_app, jsonify
import redis
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter implementation using Redis."""
    
    def __init__(self, redis_url='redis://localhost:6379/0'):
        """Initialize rate limiter with Redis connection."""
        try:
            self.redis = redis.from_url(redis_url)
            self.redis.ping()  # Test connection
        except redis.ConnectionError:
            logger.warning("Redis not available, falling back to in-memory storage")
            self.redis = None
            self._in_memory = {}
    
    def _get_rate_limit_key(self, key_prefix):
        """Generate rate limit key based on IP and optional prefix."""
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        return f"rate_limit:{key_prefix}:{ip}"
    
    def is_rate_limited(self, key_prefix, limit=100, period=3600):
        """Check if the request is rate limited.
        
        Args:
            key_prefix: Prefix for the rate limit key
            limit: Maximum number of requests allowed
            period: Time period in seconds
        
        Returns:
            tuple: (is_limited, remaining, reset_time)
        """
        key = self._get_rate_limit_key(key_prefix)
        now = int(time.time())
        
        if self.redis:
            pipeline = self.redis.pipeline()
            pipeline.zremrangebyscore(key, 0, now - period)
            pipeline.zadd(key, {str(now): now})
            pipeline.zcard(key)
            pipeline.expire(key, period)
            _, _, request_count, _ = pipeline.execute()
        else:
            # In-memory fallback
            if key not in self._in_memory:
                self._in_memory[key] = []
            
            # Remove old entries
            self._in_memory[key] = [ts for ts in self._in_memory[key] if ts > now - period]
            self._in_memory[key].append(now)
            request_count = len(self._in_memory[key])
        
        remaining = max(0, limit - request_count)
        reset_time = now + period
        
        return request_count > limit, remaining, reset_time

def rate_limit(limit=100, period=3600, key_prefix='default'):
    """Rate limiting decorator.
    
    Args:
        limit: Maximum number of requests allowed
        period: Time period in seconds
        key_prefix: Prefix for the rate limit key
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            limiter = current_app.config.get('rate_limiter')
            if not limiter:
                return f(*args, **kwargs)
            
            is_limited, remaining, reset_time = limiter.is_rate_limited(
                key_prefix, limit, period
            )
            
            response = make_response(f(*args, **kwargs))
            response.headers['X-RateLimit-Limit'] = str(limit)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            if is_limited:
                logger.warning(f"Rate limit exceeded for {request.remote_addr}")
                response = jsonify({
                    'error': 'Too many requests',
                    'remaining': remaining,
                    'reset': datetime.fromtimestamp(reset_time).isoformat()
                }), 429
            
            return response
        return wrapped
    return decorator
