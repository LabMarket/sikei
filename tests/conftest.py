import aio_pika
import pytest
import redis.asyncio as redis

from sikei.brokers.amqp import AMQPMessageBroker
from sikei.brokers.redis import RedisMessageBroker


@pytest.fixture()
def redis_client() -> redis.Redis:
    # return redis.Redis.from_url("redis://localhost:6379/0")
    return redis.Redis.from_url("redis://broker:p4ssw0rd@127.0.0.1:6379/3")

@pytest.fixture()
def redis_message_broker(redis_client: redis.Redis) -> RedisMessageBroker:
    return RedisMessageBroker(client=redis_client, channel_prefix="test_sikei_channel")

@pytest.fixture()
async def amqp_client() -> aio_pika.Connection:
    connection = await aio_pika.connect_robust("amqp://sales:p4ssw0rd@127.0.0.1:5672/%2f")
    return connection

@pytest.fixture()
async def amqp_client_subs() -> aio_pika.Connection:
    connection = await aio_pika.connect_robust("amqp://sales:p4ssw0rd@127.0.0.1:5672/%2f", client_properties={"connection_name": "caller"})
    return connection

@pytest.fixture()
async def amqp_message_broker(amqp_client_subs: aio_pika.Connection) -> AMQPMessageBroker:
    return AMQPMessageBroker(client=amqp_client, routing_key="test_sikei_queue")