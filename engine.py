from asyncio import current_task
from contextlib import asynccontextmanager
from typing import Type

import asyncpg
from asyncpg import InvalidCatalogNameError
from sqlalchemy import URL, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_scoped_session

from config import DBSettings
from models import PostingMachineBase

db_settings = DBSettings()


def get_url(engine_settings: DBSettings) -> URL:
    url_object = URL.create(
        drivername=engine_settings.driver_name,
        username=engine_settings.username,
        password=engine_settings.password.get_secret_value(),
        host=engine_settings.host,
        database=engine_settings.database,
        port=engine_settings.port
    )
    return url_object


class DataBase:
    def __init__(self, url: URL, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            poolclass=NullPool
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def scoped_session(self) -> AsyncSession:
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )
        try:
            async with session() as s:
                yield s
        finally:
            await session.remove()


db_engine = DataBase(get_url(engine_settings=db_settings), echo=db_settings.echo)


async def sync_db(engine: DataBase, settings: DBSettings, basemodel: Type[PostingMachineBase]):
    try:
        async with engine.engine.begin() as async_connect:
            await async_connect.run_sync(basemodel.metadata.create_all)
    except InvalidCatalogNameError:
        conn = await asyncpg.connect(
            database='postgres',
            user=settings.username,
            password=settings.password.get_secret_value(),
            host=settings.host,
            port=settings.port
        )
        sql_query = f'CREATE DATABASE "{settings.database}"'
        await conn.execute(sql_query)
        await conn.close()
        print(f"DB <{settings.database}> success created")
        async with engine.engine.begin() as async_connect:
            await async_connect.run_sync(basemodel.metadata.create_all)
