import logging

import orjson
from redis.asyncio import Redis

from sikei.brokers.protocol import Message

logger = logging.getLogger(__name__)


class RedisMessageBroker:
    def __init__(self, client: callable([..., Redis]), *, prefix: str | None = None) -> None:
        self._client = client
        self._prefix = prefix or "python_sikei_channel"

    async def send(self, message: Message) -> None:
        channel = f"{self._prefix}:{message.message_type}:{message.message_id}"
        logger.debug("Sending message to Redis Pub/Sub %s.", message.message_id)
        async for _ in self._client():
            await _.publish(channel, orjson.dumps(message.model_dump()))
            await _.aclose()
            break
