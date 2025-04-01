from typing import Protocol

from sikei.dispatcher.result import DispatchResult
from sikei.requests.request import Request


class Dispatcher(Protocol):
    async def dispatch(self, request: Request) -> DispatchResult:
        ...
