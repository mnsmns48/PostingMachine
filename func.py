import aiohttp

from config import root_path, main_settings


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
            for group_title in result.get('vk'):
                async with aio_session.get('https://api.vk.com/method/utils.resolveScreenName',
                                           params={
                                               'access_token': main_settings.vk_token.get_secret_value(),
                                               'v': 5.236,
                                               'screen_name': group_title
                                           }) as resp:
                    if resp.status == 200:
                        r = await resp.json()
                        group_id = r.get('response').get('object_id')
                        result['vk'] = result.get('vk', []) + [group_id]
                        result['vk'].remove(group_title)
    return result
