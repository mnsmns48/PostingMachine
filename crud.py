from typing import Type

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models import PostingMachineBase


async def write_data(session: AsyncSession, table: Type[PostingMachineBase], data: list | dict) -> bool:
    await session.execute(insert(table).values(data))
    await session.commit()
    return True
