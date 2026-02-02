from collections.abc import Generator
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

import pytest

from tests.utils.services import ServiceWithNoDependencies
from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.annotations import FromKeyedServices, FromServices
from wirio.exceptions import CannotResolveServiceFromEndpointError
from wirio.service_collection import ServiceCollection

if TYPE_CHECKING:
    from fastapi import APIRouter, Depends, FastAPI
    from fastapi.testclient import TestClient
else:
    APIRouter = None
    Depends = None
    FastAPI = None
    TestClient = None

try:
    ExtraDependencies.import_fastapi()
    from fastapi import APIRouter, Depends, FastAPI
    from fastapi.testclient import TestClient
except ImportError:
    pass


@pytest.mark.skipif(
    not ExtraDependencies.is_fastapi_installed(),
    reason="wirio[fastapi] is not installed",
)
class TestFastApi:
    @pytest.fixture
    def app(self) -> FastAPI:
        app = FastAPI()
        router = APIRouter()

        @router.get("/service-with-no-dependencies")
        async def service_with_no_dependencies_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies, FromServices()
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
    def test_client(self, app: FastAPI) -> Generator[TestClient]:
        with TestClient(app) as test_client:
            yield test_client

    def test_inject_service(self, test_client: TestClient) -> None:
        response = test_client.get("/service-with-no-dependencies")

        assert response.status_code == HTTPStatus.OK

    def test_not_interfere_with_sync_endpoints(self, test_client: TestClient) -> None:
        response = test_client.get("/sync-endpoint")

        assert response.status_code == HTTPStatus.OK

    async def test_not_interfere_with_non_annotated_parameters(self) -> None:
        expected_test_value = "test-value"
        app = FastAPI()
        router = APIRouter()

        @router.get("/non-annotated-parameter")
        async def non_annotated_parameter_endpoint(  # pyright: ignore[reportUnusedFunction]
            some_parameter: str,
        ) -> None:
            assert some_parameter == expected_test_value

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get(
                "/non-annotated-parameter",
                params={"some_parameter": expected_test_value},
            )

            assert response.status_code == HTTPStatus.OK

    async def test_not_interfere_with_fastapi_depends(self) -> None:
        expected_test_value = "test-value"
        app = FastAPI()
        router = APIRouter()

        def test_dependency() -> str:
            return expected_test_value

        @router.get("/fastapi-depends")
        async def fastapi_depends_endpoint(  # pyright: ignore[reportUnusedFunction]
            test_dependency: Annotated[str, Depends(test_dependency)],
        ) -> None:
            assert test_dependency == expected_test_value

        app.include_router(router)
        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/fastapi-depends")

            assert response.status_code == HTTPStatus.OK

    def test_return_service_when_optional_dependency_is_registered(self) -> None:
        app = FastAPI()

        @app.get("/optional-dependency")
        async def optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies | None, FromServices()
            ],
        ) -> None:
            assert isinstance(service_with_no_dependencies, ServiceWithNoDependencies)

        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/optional-dependency")

            assert response.status_code == HTTPStatus.OK

    def test_return_service_when_optional_dependency_is_not_registered(self) -> None:
        app = FastAPI()

        @app.get("/optional-dependency")
        async def optional_dependency_endpoint(  # pyright: ignore[reportUnusedFunction]
            service_with_no_dependencies: Annotated[
                ServiceWithNoDependencies | None, FromServices()
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
                ServiceWithNoDependencies, FromServices()
            ],
        ) -> None:
            pass

        services = ServiceCollection()
        services.configure_fastapi(app)

        with TestClient(app) as test_client:  # noqa: SIM117
            with pytest.raises(CannotResolveServiceFromEndpointError):
                test_client.get("/non-optional-dependency")

    async def test_combine_request_types_fastapi_depends_and_wirio_injection(
        self,
    ) -> None:
        expected_request_parameter = "test-value1"
        expected_fastapi_depends = "test-value2"
        expected_wirio_injection = "test-value3"
        app = FastAPI()
        router = APIRouter()

        def test_dependency() -> str:
            return expected_fastapi_depends

        @router.get("/endpoint")
        async def fastapi_depends_endpoint(  # pyright: ignore[reportUnusedFunction]
            request_parameter: str,
            fastapi_depends: Annotated[str, Depends(test_dependency)],
            wirio_inject: Annotated[str, FromServices()],
        ) -> None:
            assert request_parameter == expected_request_parameter
            assert fastapi_depends == expected_fastapi_depends
            assert wirio_inject == expected_wirio_injection

        app.include_router(router)
        services = ServiceCollection()
        services.add_singleton(str, expected_wirio_injection)
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get(
                "/endpoint", params={"request_parameter": expected_request_parameter}
            )

            assert response.status_code == HTTPStatus.OK

    async def test_resolve_keyed_service(self) -> None:
        service_key = "key"
        app = FastAPI()
        router = APIRouter()

        @router.get("/endpoint")
        async def endpoint(  # pyright: ignore[reportUnusedFunction]
            service: Annotated[
                ServiceWithNoDependencies, FromKeyedServices(service_key)
            ],
        ) -> None:
            assert isinstance(service, ServiceWithNoDependencies)

        app.include_router(router)
        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.configure_fastapi(app)

        with TestClient(app) as test_client:
            response = test_client.get("/endpoint")

            assert response.status_code == HTTPStatus.OK
