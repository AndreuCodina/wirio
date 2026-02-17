from typing import TYPE_CHECKING, final

from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from wirio.service_collection import ServiceCollection


@final
class SqlmodelIntegration:
    @staticmethod
    def add_async_services(
        services: "ServiceCollection",
        connection_string: str,
        *,
        expire_on_commit: bool = False,
        autoflush: bool = True,
    ) -> None:
        def inject_sql_engine() -> AsyncEngine:
            return create_async_engine(url=connection_string)

        services.add_singleton(inject_sql_engine)

        def inject_sql_session_maker(
            async_engine: AsyncEngine,
        ) -> async_sessionmaker[AsyncSession]:
            return async_sessionmaker(
                bind=async_engine,
                class_=AsyncSession,
                expire_on_commit=expire_on_commit,
                autoflush=autoflush,
            )

        services.add_singleton(inject_sql_session_maker)

        def inject_sql_session(
            async_sessionmaker: async_sessionmaker[AsyncSession],
        ) -> AsyncSession:
            return async_sessionmaker()

        services.add_scoped(inject_sql_session)

    @staticmethod
    def add_sync_services(
        services: "ServiceCollection",
        connection_string: str,
        *,
        expire_on_commit: bool = True,
        autoflush: bool = True,
    ) -> None:
        def inject_sql_engine() -> Engine:
            return create_engine(url=connection_string)

        services.add_singleton(inject_sql_engine)

        def inject_sql_session_maker(
            engine: Engine,
        ) -> sessionmaker[Session]:
            return sessionmaker(
                bind=engine,
                class_=Session,
                expire_on_commit=expire_on_commit,
                autoflush=autoflush,
            )

        services.add_singleton(inject_sql_session_maker)

        def inject_sql_session(
            sessionmaker: sessionmaker[Session],
        ) -> Session:
            return sessionmaker()

        services.add_scoped(inject_sql_session)
