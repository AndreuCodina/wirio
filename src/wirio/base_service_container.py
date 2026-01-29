from abc import ABC

from wirio.abstractions.base_service_provider import BaseServiceProvider


class BaseServiceContainer(BaseServiceProvider, ABC):
    """Define a mechanism for retrieving a service object; that is, an object that provides custom support to other objects."""
