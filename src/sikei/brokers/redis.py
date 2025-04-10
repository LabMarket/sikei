import logging

import orjson
from redis.asyncio import Redis

from sikei.brokers.protocol import Message

logger = logging.getLogger(__name__)


class RedisMessageBroker:
    def __init__(self, client: Redis, *, channel_prefix: str | None = None) -> None:
        self._client = client
        self._channel_prefix = channel_prefix or "python_sikei_channel"

    async def send(self, message: Message) -> None:
        async with self._client.pubsub() as pubsub:
            channel = f"{self._channel_prefix}:{message.message_type}:{message.message_id}"

            await pubsub.subscribe(channel)

            logger.debug("Sending message to Redis Pub/Sub %s.", message.message_id)
            await self._client.publish(channel, orjson.dumps(message.model_dump()))
