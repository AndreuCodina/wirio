class ServiceWithNoDependencies:
    pass


class ServiceWithDependencies:
    def __init__(self, service_with_no_dependencies: ServiceWithNoDependencies) -> None:
        self.service_with_no_dependencies = service_with_no_dependencies
