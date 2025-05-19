import logging

import aio_pika
import orjson

from sikei.brokers.protocol import Message, MessageBroker

logger = logging.getLogger(__name__)


class AMQPMessageBroker(MessageBroker):
    def __init__(self, client: callable([..., aio_pika.Connection]), *, routing: str | None = None, exchange: str | None = None) -> None:
        self._client = client
        self._routing = routing 
        self._exchange = exchange 

    async def send(self, message: Message) -> None:
        async with self._client() as _:
            _r=self._routing or ""
            _m=aio_pika.Message(body=orjson.dumps(message.model_dump()))
            if self._exchange:
                _e=await _.declare_exchange(self._exchange, aio_pika.ExchangeType.DIRECT)
                await _e.publish(_m, routing_key=_r)
            else:
                await _.default_exchange.publish(_m, routing_key=_r)
