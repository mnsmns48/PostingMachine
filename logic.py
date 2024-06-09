import asyncio

import aiohttp

from config import source_settings
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
                    data = await get_wall(session=aio_session, _id=source.get('_id'), _type=source.get('_type'))
                    data.reverse()
                    count = source_settings.posts_quantity
                    for post in data:
                        repost = True if post.get('copy_history') else False
                        text = post.get('copy_history')[0].get('text').strip() if repost else post.get('text')
                        check = await check_data(
                            post_id=post.get('id'),
                            source_id=post.get('owner_id'),
                            text=text)
                        if check:
                            # print(count)
                            post_data = await scrape_vk_data(data=post,
                                                             session=aio_session,
                                                             _type=source.get('_type'),
                                                             screen_name=source.get('screen_name'),
                                                             is_repost=repost,
                                                             source='vk')
                            async with db_engine.scoped_session() as session:
                                result = await write_data(session=session, table=PreModData, data=post_data)
                            #     if result:
                            #         await send_notification(session=aio_session)
                        count -= 1
                        await asyncio.sleep(1)
