class ServiceIdentifier:
    """Internal registered service during resolution."""

    service_type: type

    def __init__(self, service_type: type) -> None:
        self.service_type = service_type

    @staticmethod
    def from_service_type(service_type: type) -> ServiceIdentifier:
        return ServiceIdentifier(service_type)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ServiceIdentifier):
            return NotImplemented

        return self.service_type == value.service_type

    def __hash__(self) -> int:
        return hash(self.service_type)
