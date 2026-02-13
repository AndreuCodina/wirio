from collections.abc import Sequence
from typing import Final, final

from wirio._service_lookup._call_site_kind import CallSiteKind
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._service_call_site import ServiceCallSite
from wirio._service_lookup._typed_type import TypedType


@final
class SequenceCallSite(ServiceCallSite):
    _item_type: Final[TypedType]
    _service_call_sites: Final[list[ServiceCallSite]]

    def __init__(
        self,
        result_cache: ResultCache,
        item_type: TypedType,
        service_call_sites: list[ServiceCallSite],
        service_key: object | None = None,
    ) -> None:
        self._item_type = item_type
        self._service_call_sites = service_call_sites
        super().__init__(cache=result_cache, key=service_key)

    @property
    def service_type(self) -> TypedType:
        type_ = self._item_type.to_type()
        return TypedType.from_type(Sequence[type_])  # ty: ignore[invalid-type-form]

    @property
    def kind(self) -> CallSiteKind:
        return CallSiteKind.SEQUENCE

    @property
    def service_call_sites(self) -> list[ServiceCallSite]:
        return self._service_call_sites
