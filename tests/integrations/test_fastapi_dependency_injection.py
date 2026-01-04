from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from aspy_dependency_injection.annotations import Inject
from aspy_dependency_injection.service_collection import ServiceCollection
from tests.utils.services import ServiceWithNoDependencies

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    router = APIRouter()

    @router.get("/service-with-no-dependencies")
    async def service_with_no_dependencies_endpoint(  # pyright: ignore[reportUnusedFunction]
        service_with_no_dependencies: Annotated[ServiceWithNoDependencies, Inject()],
    ) -> None:
        assert isinstance(service_with_no_dependencies, ServiceWithNoDependencies)

    @router.get("/optional-service-with-no-dependencies")
    async def optional_service_with_no_dependencies_endpoint(  # pyright: ignore[reportUnusedFunction]
        service_with_no_dependencies: Annotated[
            ServiceWithNoDependencies | None, Inject()
        ],
    ) -> None:
        assert isinstance(service_with_no_dependencies, ServiceWithNoDependencies)

    @router.get("/sync-endpoint")
    async def sync_endpoint(  # pyright: ignore[reportUnusedFunction]
    ) -> None:
        pass

    app.include_router(router)
    services = ServiceCollection()
    services.add_transient(ServiceWithNoDependencies)
    services.configure_fastapi(app)
    return app


@pytest.fixture
def test_client(app: FastAPI) -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


class TestFastApi:
    def test_inject_service(self, test_client: TestClient) -> None:
        response = test_client.get("/service-with-no-dependencies")

        assert response.status_code == HTTPStatus.OK

    def test_not_interfere_with_sync_endpoints(self, test_client: TestClient) -> None:
        response = test_client.get("/sync-endpoint")

        assert response.status_code == HTTPStatus.OK

    def test_optional_dependency_returns_none_when_not_registered(self) -> None:
        app = FastAPI()

        @app.get("/optional-dependency")
        async def optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies | None, Inject()
            ],
        ) -> None:
            assert service_with_no_dependencies is None

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/optional-dependency")

        assert response.status_code == HTTPStatus.OK

    async def test_fail_when_non_optional_dependency_is_missing(self) -> None:
        app = FastAPI()

        @app.get("/non-optional-dependency")
        async def non_optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies, Inject()
            ],
        ) -> None:
            pass

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            with pytest.raises(RuntimeError) as exception_info:
                test_client.get("/non-optional-dependency")

            assert (
                str(exception_info.value)
                == "Unable to resolve service for type 'tests.utils.services.ServiceWithNoDependencies' while attempting to invoke endpoint"
            )
