import asyncio
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import Final, Self, final, override

from wirio._service_lookup._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from wirio._service_lookup._call_site_chain import CallSiteChain
from wirio._service_lookup._call_site_factory import CallSiteFactory
from wirio._service_lookup._call_site_runtime_resolver import CallSiteRuntimeResolver
from wirio._service_lookup._call_site_validator import CallSiteValidator
from wirio._service_lookup._constant_call_site import (
    ConstantCallSite,
)
from wirio._service_lookup._runtime_service_provider_engine import (
    RuntimeServiceProviderEngine,
)
from wirio._service_lookup._service_call_site import (
    ServiceCallSite,
)
from wirio._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from wirio._service_lookup._service_provider_call_site import (
    ServiceProviderCallSite,
)
from wirio._service_lookup._service_provider_engine import (
    ServiceProviderEngine,
)
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from wirio.abstractions.base_service_provider import BaseServiceProvider
from wirio.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from wirio.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from wirio.abstractions.service_scope import (
    AbstractAsyncContextManager,
    ServiceScope,
)
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.exceptions import (
    ObjectDisposedError,
)
from wirio.service_descriptor import ServiceDescriptor
from wirio.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


@final
@dataclass(frozen=True)
class _ServiceAccessor:
    call_site: ServiceCallSite | None
    realized_service: Callable[[ServiceProviderEngineScope], Awaitable[object | None]]


@final
class ServiceProvider(
    BaseServiceProvider, AbstractAsyncContextManager["ServiceProvider"]
):
    """Provider that resolves services."""

    _descriptors: Final[list["ServiceDescriptor"]]
    _pending_descriptors: Final[list["ServiceDescriptor"]]
    _call_site_validator: Final[CallSiteValidator | None]
    _validate_on_build: Final[bool]
    _root: Final[ServiceProviderEngineScope]
    _engine: Final[ServiceProviderEngine]
    _service_accessors: Final[
        AsyncConcurrentDictionary[ServiceIdentifier, _ServiceAccessor]
    ]
    _is_disposed: bool
    _call_site_factory: Final[CallSiteFactory]
    _is_aenter_executed: bool

    def __init__(
        self,
        descriptors: list["ServiceDescriptor"],
        validate_scopes: bool,
        validate_on_build: bool,
    ) -> None:
        self._descriptors = []
        self._pending_descriptors = descriptors.copy()
        self._call_site_validator = CallSiteValidator() if validate_scopes else None
        self._validate_on_build = validate_on_build
        self._root = ServiceProviderEngineScope(
            service_provider=self, is_root_scope=True
        )
        self._engine = self._get_engine()
        self._service_accessors = AsyncConcurrentDictionary()
        self._is_disposed = False
        self._call_site_factory = CallSiteFactory(descriptors)
        self._is_aenter_executed = False

    @property
    def root(self) -> ServiceProviderEngineScope:
        return self._root

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def is_fully_initialized(self) -> bool:
        """Indicate whether the provider is fully initialized (useful for Jupyter notebooks, which don't work well with context managers)."""
        return self._is_aenter_executed and len(self._pending_descriptors) == 0

    @property
    def call_site_validator(self) -> CallSiteValidator | None:
        return self._call_site_validator

    @property
    def pending_descriptors(self) -> list[ServiceDescriptor]:
        return self._pending_descriptors

    @override
    async def get_service_object(self, service_type: TypedType) -> object | None:
        if self._is_disposed:
            raise ObjectDisposedError

        await self.fully_initialize_if_not_fully_initialized()
        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self._root,
        )

    @override
    async def get_keyed_service_object(
        self, service_key: object | None, service_type: TypedType
    ) -> object | None:
        if self._is_disposed:
            raise ObjectDisposedError

        await self.fully_initialize_if_not_fully_initialized()
        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(
                service_type=service_type, service_key=service_key
            ),
            service_provider_engine_scope=self._root,
        )

    def create_scope(self) -> ServiceScope:
        """Create a new :class:`ServiceScope` that can be used to resolve scoped services."""
        if self._is_disposed:
            raise ObjectDisposedError

        return ServiceProviderEngineScope(service_provider=self, is_root_scope=False)

    async def aclose(self) -> None:
        """Dispose the service provider and release all resources."""
        await self.__aexit__(None, None, None)

    async def get_service_from_service_identifier(
        self,
        service_identifier: ServiceIdentifier,
        service_provider_engine_scope: ServiceProviderEngineScope,
    ) -> object | None:
        override_call_site = self.get_overridden_call_site(service_identifier)

        if override_call_site is not None:
            realized_override = self._engine.realize_service(override_call_site)
            return await realized_override(service_provider_engine_scope)

        service_accessor = await self._service_accessors.get_or_add(
            key=service_identifier, value_factory=self._create_service_accessor
        )
        self._on_resolve(service_accessor.call_site, service_provider_engine_scope)
        return await service_accessor.realized_service(service_provider_engine_scope)

    @contextmanager
    def override_service(
        self, service_type: type, implementation_instance: object | None
    ) -> Generator[None]:
        """Override a service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        service_identifier = ServiceIdentifier.from_service_type(
            TypedType.from_type(service_type)
        )

        with self._call_site_factory.override_service(
            service_identifier=service_identifier,
            implementation_instance=implementation_instance,
        ):
            yield

    @contextmanager
    def override_keyed_service(
        self,
        service_key: object | None,
        service_type: type,
        implementation_instance: object | None,
    ) -> Generator[None]:
        """Override a keyed service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        service_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(service_type),
            service_key=service_key,
        )

        with self._call_site_factory.override_service(
            service_identifier=service_identifier,
            implementation_instance=implementation_instance,
        ):
            yield

    def get_overridden_call_site(
        self, service_identifier: ServiceIdentifier
    ) -> ServiceCallSite | None:
        """Retrieve the override call site for a given identifier if present."""
        return self._call_site_factory.get_overridden_call_site(service_identifier)

    def add_descriptor(self, descriptor: ServiceDescriptor) -> None:
        self._pending_descriptors.append(descriptor)
        self._call_site_factory.add_descriptor(descriptor)

    async def fully_initialize_if_not_fully_initialized(self) -> None:
        if not self.is_fully_initialized:
            await self.__aenter__()

    async def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceAccessor:
        def get_realized_service_returning_service_object(
            service_object: object | None,
        ) -> Callable[[ServiceProviderEngineScope], Awaitable[object | None]]:
            def realized_service_returning_service_object(
                _: ServiceProviderEngineScope,
            ) -> Awaitable[object | None]:
                future = asyncio.Future[object | None]()
                future.set_result(service_object)
                return future

            return realized_service_returning_service_object

        def realized_service_returning_none(
            _: ServiceProviderEngineScope,
        ) -> Awaitable[object | None]:
            future = asyncio.Future[None]()
            future.set_result(None)
            return future

        call_site = await self._call_site_factory.get_call_site_from_service_identifier(
            service_identifier, CallSiteChain()
        )

        if call_site is not None:
            await self._on_create(call_site)

            # Optimize singleton case
            if call_site.cache.location == CallSiteResultCacheLocation.ROOT:
                service_object = await CallSiteRuntimeResolver.INSTANCE.resolve(
                    call_site, self._root
                )
                realized_service = get_realized_service_returning_service_object(
                    service_object
                )
                return _ServiceAccessor(
                    call_site=call_site, realized_service=realized_service
                )

            realized_service = self._engine.realize_service(call_site)
            return _ServiceAccessor(
                call_site=call_site, realized_service=realized_service
            )

        return _ServiceAccessor(
            call_site=call_site, realized_service=realized_service_returning_none
        )

    def _get_engine(self) -> ServiceProviderEngine:
        return RuntimeServiceProviderEngine.INSTANCE

    async def _add_built_in_services(self) -> None:
        """Add built-in services that aren't part of the list of service descriptors."""
        if self._is_aenter_executed:
            return

        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(BaseServiceProvider)
            ),
            ServiceProviderCallSite(),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceScopeFactory)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceScopeFactory),
                self._root,
            ),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceProviderIsService)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceProviderIsService), self._call_site_factory
            ),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceProviderIsKeyedService)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceProviderIsKeyedService),
                self._call_site_factory,
            ),
        )

    async def _activate_auto_activated_singletons(self) -> None:
        """Activate all singletons registered with auto_activate=True."""
        for service_descriptor in self._pending_descriptors:
            if not service_descriptor.auto_activate:
                continue

            await self.get_service_from_service_identifier(
                service_identifier=ServiceIdentifier.from_descriptor(
                    service_descriptor
                ),
                service_provider_engine_scope=self._root,
            )

    async def _validate_service(self, service_descriptor: "ServiceDescriptor") -> None:
        try:
            call_site = (
                await self._call_site_factory.get_call_site_from_service_descriptor(
                    service_descriptor, CallSiteChain()
                )
            )

            if call_site is not None:
                await self._on_create(call_site)
        except Exception as exception:
            error_message = f"Error while validating the service descriptor '{service_descriptor}': {exception!r}"
            raise RuntimeError(error_message) from exception

    async def _on_create(self, call_site: ServiceCallSite) -> None:
        if self._call_site_validator is not None:
            await self._call_site_validator.validate_call_site(call_site)

    def _on_resolve(
        self, call_site: ServiceCallSite | None, scope: ServiceScope
    ) -> None:
        if call_site is not None and self._call_site_validator is not None:
            self._call_site_validator.validate_resolution(
                call_site=call_site, scope=scope, root_scope=self._root
            )

    @override
    async def __aenter__(self) -> Self:
        await self._add_built_in_services()
        await self._activate_auto_activated_singletons()
        await self._validate_services()
        self._descriptors.extend(self._pending_descriptors)
        self._pending_descriptors.clear()
        self._is_aenter_executed = True
        return self

    async def _validate_services(self) -> None:
        if self._validate_on_build:
            exceptions: list[Exception] | None = None

            for service_descriptor in self._pending_descriptors:
                try:
                    await self._validate_service(service_descriptor)
                except Exception as exception:  # noqa: BLE001
                    if exceptions is None:
                        exceptions = []

                    exceptions.append(exception)

            if exceptions is not None:
                error_message = "Some services are not able to be constructed"
                raise ExceptionGroup(error_message, exceptions)

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._is_disposed = True
        await self._root.__aexit__(exc_type, exc_val, exc_tb)
