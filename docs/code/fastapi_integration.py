from typing import Annotated

from fastapi import FastAPI

from aspy_dependency_injection.annotations import Inject
from aspy_dependency_injection.service_collection import ServiceCollection


class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    async def create_user(self) -> None:
        pass


app = FastAPI()


@app.post("/users")
async def create_user(
    user_service: Annotated[UserService, Inject()],
) -> None:
    await user_service.create_user()


services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)
services.configure_fastapi(app)
