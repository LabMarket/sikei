from dataclasses import dataclass

import pytest
from redis import asyncio as redis
from rodi import Container, ServiceLifeStyle
from sikei.container.rodi import RodiContainer
from sikei.events import EventEmitter, EventMap
from sikei.mesikei import Mesikei
from sikei.message_brokers.redis import RedisMessageBroker
from sikei.middlewares import MiddlewareChain
from sikei.requests import Request, RequestHandler, RequestMap


@dataclass(frozen=True, kw_only=True)
class JoinMeetingRoomCommand(Request):
    meeting_id: int
    user_id: int


class JoinMeetingRoomCommandHandler(RequestHandler[JoinMeetingRoomCommand, None]):
    def __init__(self, redis_client: redis.Redis) -> None:
        self._events = []
        self._redis_client = redis_client

    @property
    def events(self) -> list:
        return self._events

    async def handle(self, request: JoinMeetingRoomCommand) -> None:
        await self._redis_client.set(str(request.meeting_id), str(request.user_id))


class TestMiddleware:
    _counter = 0

    async def __call__(self, request: Request, handle):
        self._counter += 5
        return await handle(request)


@pytest.fixture
def mesikei(redis_client) -> Mesikei:
    container = Container()
    container.register_factory(
        lambda: redis_client,
        redis.Redis,
        ServiceLifeStyle.TRANSIENT,
    )
    container.register(JoinMeetingRoomCommandHandler)
    rodi_container = RodiContainer()
    rodi_container.attach_external_container(container)

    request_map = RequestMap()
    request_map.bind(JoinMeetingRoomCommand, JoinMeetingRoomCommandHandler)

    redis_client = redis_client
    middleware_chain = MiddlewareChain()
    middleware_chain.add(TestMiddleware())

    event_emitter = EventEmitter(
        message_broker=RedisMessageBroker(redis_client),
        event_map=EventMap(),
        container=rodi_container,
    )

    return Mesikei(
        request_map=request_map,
        event_emitter=event_emitter,
        container=rodi_container,
        middleware_chain=middleware_chain,
    )


@pytest.fixture
def mesikei_without_broker(redis_client) -> Mesikei:
    container = Container()
    container.register_factory(
        lambda: redis_client,
        redis.Redis,
        ServiceLifeStyle.TRANSIENT,
    )
    container.register(JoinMeetingRoomCommandHandler)
    rodi_container = RodiContainer()
    rodi_container.attach_external_container(container)

    request_map = RequestMap()
    request_map.bind(JoinMeetingRoomCommand, JoinMeetingRoomCommandHandler)

    middleware_chain = MiddlewareChain()
    middleware_chain.add(TestMiddleware())

    event_emitter = EventEmitter(
        event_map=EventMap(),
        container=rodi_container,
    )

    return Mesikei(
        request_map=request_map,
        event_emitter=event_emitter,
        container=rodi_container,
        middleware_chain=middleware_chain,
    )


@pytest.fixture
def mesikei_without_event_emitter(redis_client) -> Mesikei:
    container = Container()
    container.register_factory(
        lambda: redis_client,
        redis.Redis,
        ServiceLifeStyle.TRANSIENT,
    )
    container.register(JoinMeetingRoomCommandHandler)
    rodi_container = RodiContainer()
    rodi_container.attach_external_container(container)

    request_map = RequestMap()
    request_map.bind(JoinMeetingRoomCommand, JoinMeetingRoomCommandHandler)

    middleware_chain = MiddlewareChain()
    middleware_chain.add(TestMiddleware())

    return Mesikei(
        request_map=request_map,
        container=rodi_container,
        middleware_chain=middleware_chain,
    )


async def test_send_command_with_middleware(redis_client: redis.Redis, mesikei: Mesikei):
    await mesikei.send(JoinMeetingRoomCommand(user_id=1, meeting_id=1))

    value = await redis_client.get("1")

    assert value == b"1"


async def test_mesikei_without_message_broker(mesikei_without_broker: Mesikei) -> None:
    await mesikei_without_broker.send(JoinMeetingRoomCommand(user_id=1, meeting_id=1))


async def test_mesikei_without_message_event_emitter(mesikei_without_event_emitter: Mesikei) -> None:
    await mesikei_without_event_emitter.send(JoinMeetingRoomCommand(user_id=1, meeting_id=1))
