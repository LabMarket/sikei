from typing import Type, TypeVar

from dependency_injector import containers

from sikei.container.protocol import Container

T = TypeVar("T")


class DependencyInjectorContainer(Container[containers.Container]):
    
    def __init__(self) -> None:
        self._external_container: containers.Container | None = None

    @property
    def external_container(self) -> containers.Container:
        if not self._external_container:
            raise AttributeError("External container is not attached.")

        return self._external_container

    def attach_external_container(self, container: containers.Container) -> None:
        self._external_container = container

    async def resolve(self, type_: Type[T]) -> T:
        if not callable(type_):
            raise TypeError(f"Expected {type_} to be a factory function")
        else:
            return type_()
