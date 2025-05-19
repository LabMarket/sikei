import asyncio
from contextlib import asynccontextmanager
from typing import AsyncContextManager

from aio_pika import Channel, Connection, connect_robust
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from dependency_injector import providers

from sikei.brokers.amqp import AMQPMessageBroker
from sikei.container.injector import DependencyInjectorContainer
from sikei.events import (
    DomainEvent,
    Event,
    EventEmitter,
    EventHandler,
    EventMap,
    NotificationEvent,
)
from sikei.mediator import Mediator
from sikei.middlewares import MiddlewareChain
from sikei.requests import Request, RequestHandler, RequestMap


class JoinMeetingRoomCommand(Request):
    user_id: int


class UserJoinedDomainEvent(DomainEvent):
    user_id: int

class UserLeftDomainEvent(DomainEvent):
    user_id: int

class UserJoinedNotificationEvent(NotificationEvent):
    user_id: int


class JoinMeetingRoomCommandHandler(RequestHandler[JoinMeetingRoomCommand, None]):

    def __init__(self) -> None:
        self._events = []

    @property
    def events(self) -> list:
        return self._events

    async def handle(self, request: JoinMeetingRoomCommand) -> None:
        self._events.append(UserJoinedDomainEvent(user_id=request.user_id))
        self._events.append(UserJoinedNotificationEvent(user_id=123))
        print("COMMANDED")


class UserJoinedEventHandler(EventHandler[UserJoinedDomainEvent]):
    
    def __init__(self) -> None:
        self._events = []

    @property
    def events(self) -> list[Event]:
        return self._events

    async def handle(self, event: UserJoinedDomainEvent) -> None:
        self._events: list[Event] = []
        print("READY", event)


class UserLeftEventHandler(EventHandler[UserLeftDomainEvent]):
    
    def __init__(self) -> None:
        self._events = []
    
    @property
    def events(self) -> list[Event]:
        return self._events

    async def handle(self, event: UserLeftDomainEvent) -> None:
        self._events: list[Event] = []
        print("LEFT", event)


class FirstMiddleware:

    async def __call__(self, request: Request, handle):
        print("Before 1 handling...")
        response = await handle(request)
        print("After 1 handling...")
        return response


class SecondMiddleware:

    async def __call__(self, request: Request, handle):
        print("Before 2  handling...")
        response = await handle(request)
        print("After 2 handling...")
        return response

class Queue:

    def __init__(self, url: str) -> None:

        async def _connection() -> AbstractRobustConnection:
            return await connect_robust(url=url)

        async def _channel() -> Channel:
            async with _connection_pool.acquire() as _:
                return await _.channel()

        _connection_pool: Pool=Pool(_connection)
        self._channel_pool: Pool=Pool(_channel)
        
    @asynccontextmanager
    async def connection(self) -> AsyncContextManager[Connection]:
        async with self._channel_pool.acquire() as _:
            yield _


async def main() -> None:
    middleware_chain = MiddlewareChain()
    middleware_chain.add(FirstMiddleware())
    middleware_chain.add(SecondMiddleware())
    event_map = EventMap()
    event_map.bind(UserJoinedDomainEvent, UserJoinedEventHandler)
    request_map = RequestMap()
    request_map.bind(JoinMeetingRoomCommand, JoinMeetingRoomCommandHandler)


    
    container = DependencyInjectorContainer()
    container.c = providers.Factory(JoinMeetingRoomCommandHandler)
    container.e = providers.Factory(UserJoinedEventHandler)
    container.attach_external_container(container.c)
    container.attach_external_container(container.e)

    queue=providers.DelegatedFactory(
        Queue,
        url="amqp://sales:p4ssw0rd@127.0.0.1:5672/bookstore"
    )
    
    client=providers.Resource(
        queue.provided.connection
    )

    broker=providers.Factory(
        AMQPMessageBroker, 
        client=client, 
        routing="test_sikei_queue",
    )

    event_emitter = providers.Factory(
        EventEmitter,
        message_broker=broker,
        event_map=event_map,
        container=container,
    )

    mediator = providers.Factory(
        Mediator,
        request_map=request_map,
        event_emitter=event_emitter,
        container=container,
        middleware_chain=middleware_chain,
    )
    
    await mediator().send(JoinMeetingRoomCommand(user_id=100))


if __name__ == "__main__":
    asyncio.run(main())
