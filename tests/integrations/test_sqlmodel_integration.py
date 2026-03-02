import os
from typing import TYPE_CHECKING, Any, ClassVar

import pytest
from testcontainers.postgres import (  # pyright: ignore[reportMissingTypeStubs]
    PostgresContainer,
)

from wirio._utils._extra_dependencies import ExtraDependencies
from wirio.service_collection import ServiceCollection

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import Session, select, text
    from sqlmodel.ext.asyncio.session import AsyncSession
else:
    Engine = Any
    AsyncEngine = Any
    async_sessionmaker = Any
    sessionmaker = Any
    Session = Any
    select = Any
    text = Any
    AsyncSession = Any

try:
    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import Session, select, text
    from sqlmodel.ext.asyncio.session import AsyncSession
except ImportError:
    pass


@pytest.mark.skipif(
    os.environ.get("CI") is None,
    reason="Slow tests",
)
@pytest.mark.skipif(
    not ExtraDependencies.is_sqlmodel_installed(),
    reason=ExtraDependencies.SQLMODEL_NOT_INSTALLED_ERROR_MESSAGE,
)
class TestSqlmodelIntegration:
    POSTGRE_SQL_IMAGE: ClassVar[str] = (
        "postgres@sha256:b6b4d0b75c699a2c94dfc5a94fe09f38630f3b67ab0e1653ede1b7ac8e13c197"  # 18.2
    )
    ASYNC_POSTGRE_SQL_DRIVER: ClassVar[str] = "asyncpg"
    SYNC_POSTGRE_SQL_DRIVER: ClassVar[str] = "psycopg2"

    async def test_add_async_sqlmodel(self) -> None:
        expected_selected_number = 1

        with PostgresContainer(
            image=self.POSTGRE_SQL_IMAGE, driver=self.ASYNC_POSTGRE_SQL_DRIVER
        ) as postgres_container:
            connection_string = postgres_container.get_connection_url()
            services = ServiceCollection()
            services.add_sqlmodel(connection_string=connection_string)

            async with services.build_service_provider() as service_provider:
                sql_engine = await service_provider.get_required_service(AsyncEngine)

                assert isinstance(sql_engine, AsyncEngine)

                async with sql_engine.connect() as sql_connection:
                    query_result = await sql_connection.execute(
                        text(f"SELECT {expected_selected_number}")
                    )
                    result = query_result.scalar_one()

                    assert result == expected_selected_number

            async with services.build_service_provider() as service_provider:
                sql_session_maker = await service_provider.get_required_service(
                    async_sessionmaker[AsyncSession]
                )

                assert isinstance(sql_session_maker, async_sessionmaker)

                async with sql_session_maker() as sql_session:
                    query_result = await sql_session.exec(
                        select(expected_selected_number)
                    )
                    result = query_result.one()

                    assert result == expected_selected_number

            async with (
                services.build_service_provider() as service_provider,
                service_provider.create_scope() as service_scope,
            ):
                sql_session = await service_scope.get_required_service(AsyncSession)

                assert isinstance(sql_session, AsyncSession)

                query_result = await sql_session.exec(select(expected_selected_number))
                result = query_result.one()

                assert result == expected_selected_number

    async def test_add_sync_sqlmodel(self) -> None:
        expected_selected_number = 1

        with PostgresContainer(
            image=self.POSTGRE_SQL_IMAGE, driver=self.SYNC_POSTGRE_SQL_DRIVER
        ) as postgres_container:
            connection_string = postgres_container.get_connection_url()
            services = ServiceCollection()
            services.add_sync_sqlmodel(connection_string=connection_string)

            async with services.build_service_provider() as service_provider:
                sql_engine = await service_provider.get_required_service(Engine)

                assert isinstance(sql_engine, Engine)

                with sql_engine.connect() as sql_connection:
                    query_result = sql_connection.execute(
                        text(f"SELECT {expected_selected_number}")
                    )
                    result = query_result.scalar_one()

                    assert result == expected_selected_number

            async with services.build_service_provider() as service_provider:
                sql_session_maker = await service_provider.get_required_service(
                    sessionmaker[Session]
                )

                assert isinstance(sql_session_maker, sessionmaker)

                with sql_session_maker() as sql_session:
                    query_result = sql_session.exec(select(expected_selected_number))
                    result = query_result.one()

                    assert result == expected_selected_number

            async with (
                services.build_service_provider() as service_provider,
                service_provider.create_scope() as service_scope,
            ):
                sql_session = await service_scope.get_required_service(Session)

                assert isinstance(sql_session, Session)

                query_result = sql_session.exec(select(expected_selected_number))
                result = query_result.one()

                assert result == expected_selected_number
