from typing import Optional
from uuid import uuid4

from sikei.dispatcher import DefaultDispatcher
from sikei.events import Event
from sikei.middlewares import MiddlewareChain
from sikei.requests import Request, RequestHandler
from sikei.requests.map import RequestMap
from sikei.response import Response


class ReadMeetingDetailsQuery(Request):
    meeting_room_id: str
    second: Optional[str] = None
    third: Optional[str] = None


class ReadMeetingDetailsQueryResult(Response):
    meeting_room_id: str
    second: Optional[str] = None
    third: Optional[str] = None


class ReadMeetingDetailsQueryHandler(
    RequestHandler[ReadMeetingDetailsQuery, ReadMeetingDetailsQueryResult]  # type: ignore
):
    def __init__(self) -> None:
        self.called = False
        self._events: list[Event] = []

    @property
    def events(self) -> list:
        return self._events

    async def handle(self, request: ReadMeetingDetailsQuery) -> ReadMeetingDetailsQueryResult:
        self.called = True
        return ReadMeetingDetailsQueryResult(meeting_room_id=request.meeting_room_id)


class TestQueryContainer:
    _handler = ReadMeetingDetailsQueryHandler()

    async def resolve(self, type_):
        return self._handler


async def test_default_dispatcher_logic() -> None:
    middleware = FirstMiddleware()
    request_map = RequestMap()
    request_map.bind(ReadMeetingDetailsQuery, ReadMeetingDetailsQueryHandler)
    middleware_chain = MiddlewareChain()
    middleware_chain.add(middleware)
    dispatcher = DefaultDispatcher(
        request_map=request_map,
        container=TestQueryContainer(),
        middleware_chain=middleware_chain,
    )

    request = ReadMeetingDetailsQuery(meeting_room_id=str(uuid4()))

    result = await dispatcher.dispatch(request)

    assert request.meeting_room_id == "REQ"
    assert result.response.meeting_room_id == "RES"


async def test_default_dispatcher_chain_logic() -> None:
    request_map = RequestMap()
    request_map.bind(ReadMeetingDetailsQuery, ReadMeetingDetailsQueryHandler)
    middleware_chain = MiddlewareChain()
    middleware_chain.set([FirstMiddleware(), SecondMiddleware(), ThirdMiddleware()])
    dispatcher = DefaultDispatcher(
        request_map=request_map,
        container=TestQueryContainer(),
        middleware_chain=middleware_chain,
    )

    request = ReadMeetingDetailsQuery(meeting_room_id=str(uuid4()))

    result = await dispatcher.dispatch(request)

    assert request.meeting_room_id == "REQ"
    assert result.response.meeting_room_id == "RES"

    assert request.second == "DONE"
    assert result.response.second == "DONE"

    assert request.third == "DONE"
    assert result.response.third == "DONE"


class FirstMiddleware:
    async def __call__(self, request: Request, handle):
        request.meeting_room_id = "REQ"
        response = await handle(request)
        response.meeting_room_id = "RES"
        return response


class SecondMiddleware:
    async def __call__(self, request: Request, handle):
        request.second = "DONE"
        response = await handle(request)
        response.second = "DONE"
        return response


class ThirdMiddleware:
    async def __call__(self, request: Request, handle):
        request.third = "DONE"
        response = await handle(request)
        response.third = "DONE"
        return response
