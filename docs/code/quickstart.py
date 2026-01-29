import asyncio

from wirio.service_container import ServiceContainer


class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service

    async def create_user(self) -> None:
        pass


services = ServiceContainer()
services.add_transient(EmailService)
services.add_transient(UserService)


async def main() -> None:
    async with services:
        user_service = await services.get(UserService)
        await user_service.create_user()


if __name__ == "__main__":
    asyncio.run(main())
