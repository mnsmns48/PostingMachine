import asyncio

from engine import sync_db, db_engine
from models import PostingMachineBase


async def main():
    await sync_db(engine=db_engine, settings=db_engine, basemodel=PostingMachineBase)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('script stopped')
