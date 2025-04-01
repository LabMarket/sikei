from dataclasses import dataclass, field

from sikei.events.event import Event
from sikei.response import Response


@dataclass
class DispatchResult:
    response: Response | None = field(default=None)
    events: list[Event] = field(default_factory=list)
