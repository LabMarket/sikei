import asyncio
from contextlib import asynccontextmanager

from aio_pika import connect_robust
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

    @asynccontextmanager
    async def amqp_client_subs():
        try:
            connection = await connect_robust(
                "amqp://sales:p4ssw0rd@127.0.0.1:5672/bookstore", 
                client_properties={"connection_name": "caller"}
            )
            yield connection
        finally:
            await connection.close()

    # amqp_client_subs = await connect_robust(
    #     "amqp://sales:p4ssw0rd@127.0.0.1:5672/bookstore", 
    #     client_properties={"connection_name": "caller"}
    # )

    event_emitter = EventEmitter(
        message_broker=AMQPMessageBroker(amqp_client_subs, routing_key="test_sikei_queue"),
        event_map=event_map,
        container=container,
    )

    mediator = Mediator(
        request_map=request_map,
        event_emitter=event_emitter,
        container=container,
        middleware_chain=middleware_chain,
    )

    await mediator.send(JoinMeetingRoomCommand(user_id=100))

    # await amqp_client_subs.close()



if __name__ == "__main__":
    asyncio.run(main())
