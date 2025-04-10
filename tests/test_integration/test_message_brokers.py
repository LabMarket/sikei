import json
from typing import Optional

import pytest
import redis.asyncio as redis
from aio_pika.abc import AbstractIncomingMessage

from sikei.brokers.rabbitmq import Message, RabbitMQMessageBroker
from sikei.brokers.redis import RedisMessageBroker


async def test_redis_message_broker_publish_event(
    redis_message_broker: RedisMessageBroker, redis_client: redis.Redis
) -> None:
    async with redis_client.pubsub() as pubsub:
        await pubsub.psubscribe("test_sikei_channel:*")

        message = Message(payload={"phrase": "hello"}, message_type="", message_name="")
        await redis_message_broker.send(message=message)
        await pubsub.get_message(ignore_subscribe_messages=True)
        pubsub_data: dict = await pubsub.get_message(ignore_subscribe_messages=True)

        assert pubsub_data

        data = json.loads(pubsub_data["data"].decode())

        assert "message_type" in data
        assert "message_id" in data
        
@pytest.mark.skip(reason="don't have RabbitMQ available")
async def test_rabbitmq_message_broker_publish_event(
    rabbitmq_client_subs, rabbitmq_message_broker: RabbitMQMessageBroker
) -> None:
    
    async with  rabbitmq_client_subs as connection:
        
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=100)
        queue = await channel.declare_queue("test_sikei_queue")

        message = Message(payload={"phrase": "hello"}, message_type="", message_name="")
        await rabbitmq_message_broker.send(message=message)

        await channel.set_qos(prefetch_count=100)
  
        incoming_message: Optional[AbstractIncomingMessage] = await queue.get(
            timeout=5, fail=False
        )
        await incoming_message.ack()
        data = json.loads(incoming_message.body.decode())
        assert "message_type" in data
        assert "message_id" in data
        assert data["payload"] == {"phrase": "hello"}
        await queue.delete()
