import json
from typing import Optional

import aio_pika
import pytest
import redis.asyncio as redis
from aio_pika.abc import AbstractIncomingMessage

from sikei.brokers.amqp import AMQPMessageBroker, Message
from sikei.brokers.redis import RedisMessageBroker


async def test_redis_message_broker_publish_event(
    redis_message_broker: RedisMessageBroker, redis_client: redis.Redis
) -> None:
    async with redis_client.pubsub() as pubsub:
        await pubsub.psubscribe("test_sikei_channel:*")

        message = Message(payload={"phrase": "hello"}, message_type="", message_name="")
        await redis_message_broker.send(message=message)
        # await pubsub.get_message(ignore_subscribe_messages=True)
        pubsub_data = await pubsub.get_message(ignore_subscribe_messages=True)

        assert pubsub_data

        data = json.loads(pubsub_data["data"].decode())

        assert "message_type" in data
        assert "message_id" in data

@pytest.mark.skip(reason="Don't know how to configure conftest")
async def test_amqp_message_broker_publish_event(
    amqp_message_broker: AMQPMessageBroker, amqp_client_subs: aio_pika.Connection
) -> None:
    
    async with  amqp_client_subs as connection:
        
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=100)
        queue = await channel.declare_queue("test_sikei_queue")

        message = Message(payload={"phrase": "hello"}, message_type="", message_name="")
        await amqp_message_broker.send(message=message)

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
