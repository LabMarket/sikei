import asyncio

from di import Container, bind_by_type
from di.dependent import Dependent
from redis import asyncio as redis

from sikei.brokers.redis import RedisMessageBroker
from sikei.container.di import DIContainer
from sikei.events import (
    DomainEvent,
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


class UserJoinedEventHandler(EventHandler[UserJoinedDomainEvent]):
    async def handle(self, event: UserJoinedDomainEvent) -> None:
        print("READY", event)


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


def configure() -> DIContainer:
    container = Container()

    container.bind(bind_by_type(Dependent(UserJoinedEventHandler, scope="request"), UserJoinedEventHandler))
    container.bind(
        bind_by_type(
            Dependent(JoinMeetingRoomCommandHandler, scope="request"),
            JoinMeetingRoomCommandHandler,
        )
    )

    di_container = DIContainer()
    di_container.attach_external_container(container)

    return di_container


async def main() -> None:
    middleware_chain = MiddlewareChain()
    middleware_chain.add(FirstMiddleware())
    middleware_chain.add(SecondMiddleware())
    event_map = EventMap()
    event_map.bind(UserJoinedDomainEvent, UserJoinedEventHandler)
    request_map = RequestMap()
    request_map.bind(JoinMeetingRoomCommand, JoinMeetingRoomCommandHandler)
    
    container = configure()

    redis_client: redis.Redis = redis.Redis.from_url("redis://broker:p4ssw0rd@127.0.0.1:6379/3")

    event_emitter = EventEmitter(
        message_broker=RedisMessageBroker(redis_client),
        event_map=event_map,
        container=container,
    )

    mediator = Mediator(
        request_map=request_map,
        event_emitter=event_emitter,
        container=container,
        middleware_chain=middleware_chain,
    )

    await mediator.send(JoinMeetingRoomCommand(user_id=1))


if __name__ == "__main__":
    asyncio.run(main())
