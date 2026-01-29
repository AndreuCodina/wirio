from typing import Annotated

from fastapi import FastAPI

from wirio.annotations import FromServices
from wirio.service_container import ServiceContainer


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
    user_service: Annotated[UserService, FromServices()],
) -> None:
    await user_service.create_user()


services = ServiceContainer()
services.add_transient(EmailService)
services.add_transient(UserService)
services.configure_fastapi(app)  # (1)!
