from datetime import datetime

import aiohttp
from aiohttp import ClientSession

from config import root_path, source_settings


async def read_sources(file: str) -> dict:
    result = dict()
    with open(f'{root_path}/setup/{file}.txt', 'r', encoding='utf-8') as file:
        sources = [line.strip() for line in file.readlines()]
    for source in sources:
        if 'vk.com' in source:
            result['vk'] = result.get('vk', []) + [source.split('vk.com/')[1]]
        else:
            result['html'] = result.get('html', []) + [source]
    if result.get('vk'):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as aio_session:
            for _title in result.get('vk'):
                async with aio_session.get('https://api.vk.com/method/utils.resolveScreenName',
                                           params={
                                               'access_token': source_settings.vk_token.get_secret_value(),
                                               'v': 5.236,
                                               'screen_name': _title
                                           }) as resp:
                    if resp.status == 200:
                        r = await resp.json()
                        _id = {
                            r.get('response').get('object_id'): r.get('response').get('type')
                        }
                        result['vk'] = result.get('vk', []) + [_id]
                        result['vk'].remove(_title)
    return result


async def get_wall(session: ClientSession, _id: int, _type: str) -> list:
    async with session.get('https://api.vk.com/method/wall.get',
                           params={
                               'access_token': source_settings.vk_token.get_secret_value(),
                               'v': 5.199,
                               'owner_id': -abs(_id) if _type == 'group' else abs(_id),
                               'count': source_settings.posts_quantity,
                               'offset': source_settings.posts_offset,
                           }) as resp:
        if resp.status == 200:
            r = await resp.json()
            return r['response']['items']


async def check_data(post_id: int, source_id: int, text: str) -> bool:
    return True


async def scrape_vk_data(data: dict) -> dict:
    pass


async def send_notification(session: ClientSession, **kwargs):
    async with session.get(
        url=f"https://api.telegram.org/bot{source_settings.bot_token.get_secret_value()}"
            f"/sendMessage?chat_id={source_settings.post_editor}"
            f"&text=Работает"
            f"&disable_notification={source_settings.disable_notification}") as resp:
        await resp.json()
