import asyncio

import aiohttp

from crud import write_data
from engine import db_engine
from func import read_sources, get_wall, check_data, scrape_vk_data, send_notification
from models import PreModData


async def cyclic_observation(sources: str):
    source = await read_sources(file=sources)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as aio_session:
        for key, value in source.items():
            if key == 'vk':
                for source in value:
                    for _id, _type in source.items():
                        data = await get_wall(session=aio_session, _id=_id, _type=_type)
                        data.reverse()
                        for post in data:
                            repost = post.get('copy_history')
                            text = repost[0].get('text').strip() if repost else post.get('text')
                            check = await check_data(
                                post_id=post.get('id'),
                                source_id=post.get('owner_id'),
                                text=text)
                            if check:
                                post_data = await scrape_vk_data(data=post)
                        await send_notification(session=aio_session)
                                # async with db_engine.scoped_session() as session:
                                #     result = await write_data(session=session, table=PreModData, data=post_data)
                                #     if result:
                                #         await send_notification(session=aio_session)
                        await asyncio.sleep(10)