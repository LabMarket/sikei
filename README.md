
<a href="https://github.com/LabMarket/sikei/actions?query=setup%3ACI%2FCD+event%3Apush+branch%3Adev" target="_blank">
    <img src="https://github.com/LabMarket/sikei/actions/workflows/ci.yml/badge.svg?branch=dev" alt="Test">
</a>
<a href="https://pypi.org/project/sikei" target="_blank">
    <img src="https://img.shields.io/pypi/v/sikei?color=red&labelColor=black" alt="Package version">
</a>
<a href="https://pypi.org/project/sikei" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/sikei.svg?color=red&labelColor=black" alt="Supported Python versions">
</a>

# SiKei - CQRS Library for Python
**[Docs](https://akhundmurad.github.io/sikei/) | [PyPI](https://pypi.org/project/sikei/)**

SiKei is a Python library for implementing CQRS pattern in your Python applications forked from Diator (https://akhundmurad.github.io/diator/). It provides a set of abstractions and utilities to help you separate your read and write concerns, allowing for better scalability, performance, and maintainability of your application.

## Features :bulb:

- Implements the CQRS pattern.
- Simple, yet flexible API.
- Supports multiple message brokers, such as [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/), [RabbitMQ](https://www.rabbitmq.com/) and [Azure Service Bus](https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-messaging-overview).
- Supports various di-frameworks, such as [Dependency Injector](https://github.com/ets-labs/python-dependency-injector) and [di](https://github.com/adriangb/di) and [rodi](https://github.com/Neoteroi/rodi).
- Easy to integrate with existing codebases.

## Differences from original project :wrench:

- Added support to [RabbitMQ](https://www.rabbitmq.com/) based on work from [Fran Martin](https://github.com/manudiv16/diator).
- Added support to [Dependency Injector](https://github.com/ets-labs/python-dependency-injector) from **ETS Labs**.
- Migration to [Pydantic](https://pydantic-docs.helpmanual.io/) based on work from [0xSecure](https://github.com/0xSecure/diator).
- Some incompatibilities in modules names and project organization to better integrate with my setup (easy to adapt from legacy projects)

## Installation :triangular_ruler:

Install the SiKei library with [pip](https://pypi.org/project/sikei/)

```bash
pip install sikei
```

There are also several installation options:

- To use Redis as Message Broker

    ```bash
    pip install sikei[redis]
    ```

- Or Azure Service Bus

    ```bash
    pip install sikei[azure]
    ```

## Simple Example :hammer_and_wrench:

Minimal example of sikei usage:

```python
import asyncio
from dataclasses import dataclass, field
from di import Container, bind_by_type
from di.dependent import Dependent
from sikei.events import EventMap, Event, EventEmitter
from sikei.container.di import DIContainer
from sikei.mediator import Mediator
from sikei.requests import Request, RequestHandler, RequestMap


@dataclass(frozen=True, kw_only=True)
class JoinMeetingCommand(Request):
    meeting_id: int
    user_id: int
    is_late: bool = field(default=False)


class JoinMeetingCommandHandler(RequestHandler[JoinMeetingCommand, None]):
    def __init__(self, meeting_api) -> None:
        self._meeting_api = meeting_api
        self._events: list[Event] = []

    @property
    def events(self) -> list[Event]:
        return self._events

    async def handle(self, request: JoinMeetingCommand) -> None:
        self._meeting_api.join(request.meeting_id, request.user_id)
        if request.is_late:
            self._meeting_api.warn(request.user_id)


def setup_di() -> DIContainer:
    external_container = Container()

    external_container.bind(
        bind_by_type(
            Dependent(JoinMeetingCommandHandler, scope="request"),
            JoinMeetingCommandHandler,
        )
    )

    container = DIContainer()
    container.attach_external_container(external_container)

    return container


async def main() -> None:
    container = setup_di()

    request_map = RequestMap()
    request_map.bind(JoinMeetingCommand, JoinMeetingCommandHandler)

    event_emitter = EventEmitter(
        event_map=EventMap(), container=container, message_broker=None
    )

    mediator = Mediator(
        request_map=request_map,
        event_emitter=event_emitter,
        container=container,
    )

    await mediator.send(JoinMeetingCommand(user_id=1, meeting_id=1, is_late=True))


if __name__ == "__main__":
    asyncio.run(main())

```

## Further reading :scroll:

- [Udi Dahan - Clarified CQRS](https://udidahan.com/2009/12/09/clarified-cqrs/)
- [Martin Fowler - CQRS](https://martinfowler.com/bliki/CQRS.html)
- [Marting Fowler - What do you mean by “Event-Driven”?](https://martinfowler.com/articles/201701-event-driven.html)
- [Vlad Khononov - Learning Domain-Driven Design](https://www.oreilly.com/library/view/learning-domain-driven-design/9781098100124/)
- [Vaughn Vernon - Really Simple CQRS](https://kalele.io/really-simple-cqrs/)

## License

This project is licensed under the terms of the MIT license.


# UV

Using UV to sync, build and publish

```sh
uv sync
uv build
uv publish
```

> Inform `__token__` and use token created at pypi.org
