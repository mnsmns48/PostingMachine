import asyncio

import aiohttp

from crud import write_data
from engine import db_engine, sync_db
from func import read_sources, get_wall, check_data, scrape_vk_data, send_notification
from models import PreModData, PostingMachineBase


async def cyclic_observation(sources: str):
    await sync_db(engine=db_engine, settings=db_engine, basemodel=PostingMachineBase)
    print('Start PostingMachine')
    notificator = ''
    while True:
        source = await read_sources(file=sources)
        for key, value in source.items():
            if key == 'vk':
                for source in value:
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as aio_session:
                        data = await get_wall(session=aio_session, _id=source.get('_id'), _type=source.get('_type'))
                        data.reverse()
                        async with db_engine.scoped_session() as db_session:
                            for post in data:
                                repost = True if post.get('copy_history') else False
                                # text = post.get('copy_history')[0].get('text').strip() if repost else post.get('text')
                                check = await check_data(
                                    post_id=post.get('id'),
                                    source_id=post.get('owner_id'))
                                if check:
                                    post_data = await scrape_vk_data(data=post,
                                                                     session=aio_session,
                                                                     _type=source.get('_type'),
                                                                     screen_name=source.get('screen_name'),
                                                                     is_repost=repost,
                                                                     source='vk')
                                    await write_data(session=db_session, table=PreModData, data=post_data)
                                    notificator = ' ' + source.get('screen_name')
                                await asyncio.sleep(0.8)
                        if notificator:
                            await send_notification(session=aio_session, text=notificator)
                            notificator = ''
        await asyncio.sleep(30)