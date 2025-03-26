from dependency_injector import containers, providers

from sikei.container.dependency_injector import DependencyInjectorContainer


class Dependency:
    ...


async def test_dependency_injector_container_resolve() -> None:
    class ExternalContainer(containers.DeclarativeContainer):
        dependency = providers.Factory(Dependency)

    external_container = ExternalContainer()

    container = DependencyInjectorContainer()
    container.attach_external_container(external_container)

    resolved = await container.resolve(Dependency)

    assert isinstance(resolved, Dependency)


