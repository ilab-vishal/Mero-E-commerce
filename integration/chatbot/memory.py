"""
Redis-based Memory Persistence for Chatbot Sessions.
Professional implementation handling serialization and state management.
"""

# Standard library imports
import json
import os
from typing import Any, Dict, List

# Third-party imports
import redis

# Local imports
from utils.logging import get_logger

logger = get_logger(__name__)

class RedisMemory:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            self.ttl = 86400 * 7  # 7 Days TTL for chat sessions
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {self.redis_url}: {e}")
            self.client = None

    def _get_key(self, session_id: str) -> str:
        return f"chat:session:{session_id}"

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieve structured chat history from Redis.
        
        Args:
            session_id: The unique session identifier.
            limit: Smart Memory - Only fetch the last N messages to save costs (Sliding Window).
        """
        if not self.client:
            return []
        
        try:
            key = self._get_key(session_id)
            # Smart Retrieval: Get only the last 'limit' messages
            # failed negative indexing in some redis versions? No, standard redis supports it.
            range_start = -limit if limit > 0 else 0
            
            raw_history = self.client.lrange(key, range_start, -1)
            return [json.loads(msg) for msg in raw_history]
        except Exception as e:
            logger.error(f"Error reading history for {session_id}: {e}")
            return []

    def add_message(self, session_id: str, role: str, content: str):
        """Append a message to the session history."""
        if not self.client:
            return

        try:
            key = self._get_key(session_id)
            message_data = json.dumps({"role": role, "content": content})
            
            # Push to right (end of list)
            self.client.rpush(key, message_data)
            
            # Refresh TTL
            self.client.expire(key, self.ttl)
        except Exception as e:
            logger.error(f"Error saving message to {session_id}: {e}")

    def clear(self, session_id: str):
        """Clear session history."""
        if self.client:
            self.client.delete(self._get_key(session_id))

# Accessor
memory_store = RedisMemory()
