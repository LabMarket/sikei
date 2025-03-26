from typing import Type, TypeVar

from dependency_injector import containers

T = TypeVar("T")


class DependencyInjectorContainer:
    def __init__(self) -> None:
        self._external_container: containers.DeclarativeContainer | None = None

    @property
    def external_container(self) -> containers.DeclarativeContainer:
        if not self._external_container:
            raise AttributeError("External container is not attached.")

        return self._external_container

    def attach_external_container(self, container: containers.DeclarativeContainer) -> None:
        self._external_container = container

    async def resolve(self, type_: Type[T]) -> T:
        provider = self.external_container.providers['dependency']

        return provider()
