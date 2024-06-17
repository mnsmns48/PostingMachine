import asyncio
import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

import aiohttp
from aiohttp import ClientSession
from sqlalchemy import select, and_, Result

from config import root_path, source_settings, bot
from engine import db_engine
from models import Posts, PreModData, BadPosts


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
                            '_id': r.get('response').get('object_id'),
                            '_type': r.get('response').get('type'),
                            'screen_name': _title
                        }
                        result['vk'] = result.get('vk', []) + [_id]
                        result['vk'].remove(_title)
    return result


async def get_wall(session: ClientSession, _id: int, _type: str) -> list:
    owner_id = int()
    if _type == 'group' or 'page':
        owner_id = -abs(_id)
    if _type == 'user':
        owner_id = _id
    async with session.get('https://api.vk.com/method/wall.get',
                           params={
                               'access_token': source_settings.vk_token.get_secret_value(),
                               'v': 5.199,
                               'owner_id': owner_id,
                               'count': source_settings.posts_quantity,
                               'offset': source_settings.posts_offset,
                           }) as resp:
        if resp.status == 200:
            r = await resp.json()
            return r['response']['items']


async def check_data(post_id: int, source_id: int) -> bool:
    tab1 = select(PreModData.internal_id).filter(and_(PreModData.internal_id == post_id),
                                                 (PreModData.source_id == source_id))
    tab2 = select(Posts.post_id).filter(and_(Posts.post_id == post_id),
                                        (Posts.group_id == source_id))
    tab3 = select(BadPosts.internal_id).filter(and_(BadPosts.internal_id == post_id),
                                               (BadPosts.source_id == source_id))
    query = tab1.union(tab2, tab3)
    async with db_engine.scoped_session() as session:
        r = await session.execute(query)
        res: Result = r.fetchall()
    if res:
        return False
    else:
        return True


async def get_contact(data: dict, is_repost: bool) -> int | None:
    if is_repost:
        text = data['copy_history'][0].get('text')
    else:
        text = data.get('text')
    edit_text = text.replace('-', '').replace(')', '').replace('(', '')
    match = re.findall(r'\b\+?[7,8](\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2})\b', edit_text)
    try:
        if match[0]:
            response = match[0].replace(' ', '')
            if len(response) == 10:
                r = '7' + response
                await asyncio.sleep(0.1)
                return int(r)
    except IndexError:
        await asyncio.sleep(0.1)
        return None


async def de_anonymization(data: dict, is_repost: bool, phone_number: int | None) -> None | int:
    if is_repost:
        signer_id = data['copy_history'][0].get('signer_id')
    else:
        signer_id = data.get('signer_id')
    if signer_id is None and phone_number is None:
        return None
    elif isinstance(signer_id, int) and phone_number is None:
        return signer_id
    elif signer_id is None and phone_number:
        async with db_engine.scoped_session() as session:
            query = select(Posts.signer_id).filter(Posts.phone_number == phone_number)
            result = await session.execute(query)
            response = result.scalars().all()
            try:
                counter = Counter(response)
                item, count = max(counter.items(), key=lambda p: p[::-1])
                if item:
                    return int(item)
            except ValueError:
                if len(response) == 0:
                    return None
    return signer_id


async def get_name_by_id(_id: int | None, session: ClientSession) -> str:
    if _id is None:
        return 'Анонимно'
    params = {
        'access_token': source_settings.vk_token.get_secret_value(),
        'lang': 'ru',
        'v': 5.199,
    }
    if _id > 0:
        params.update(
            {
                'user_ids': abs(_id)
            }
        )
        async with session.get('https://api.vk.com/method/users.get', params=params) as resp:
            if resp.status == 200:
                result = await resp.json()
                return f"{result['response'][0].get('first_name')} {result['response'][0].get('last_name')}"
            print(resp)

    params.update(
        {
            'group_ids': abs(_id)
        }
    )
    async with session.get('https://api.vk.com/method/groups.getById', params=params) as resp:
        result = await resp.json()
        return result['response']['groups'][0].get('name')


def photo_attachment_parsing(pics: list) -> dict:
    result = dict()
    items = [line.get('height') for line in pics]
    items.sort(reverse=True)
    for item in pics:
        if item.get('height') == items[-4]:  # -1 - худшее качество
            result.update({'preview_size': item.get('url')})
        if item.get('height') == items[1]:  # 0 - лучшее качество, 1-предлучшее
            result.update({'big_size': item.get('url')})
    return result


def docs_attachment_parsing(data: dict) -> dict[str, Any]:
    """ Docs types:
        1 — text docs;
        3 — gif;
        4 — pics;"""
    docs_depends = {
        1: lambda x: {
            'link': x.get('url'),
            'title': x.get('title'),
            'ext': x.get('ext')},
        3: lambda x: {
            'link': x['preview']['video'].get('src'),
            'title': x.get('title'),
            'ext': x.get('ext')},
        4: lambda x: {
            'link': x['preview']['photo']['sizes'][-1].get('src'),
            'title': x.get('title'),
            'ext': x.get('ext')}
    }
    func = docs_depends.get(data.get('type'))
    response = func(data)
    return response


async def pars_attachments(data: dict, is_repost: bool) -> json:
    attachments_dict = dict()
    if not is_repost:
        attachments = data.get('attachments')
    else:
        attachments = data['copy_history'][0].get('attachments')
    if attachments:
        for attache in attachments:
            attache_type = attache.get('type')
            if attache_type == 'video':
                autor = attache.get('video').get('signer_id') if attache.get('video').get('signer_id') \
                    else attache.get('video').get('owner_id')
                attachments_dict['video'] = attachments_dict.get(attache_type, []) + [
                    f"https://vk.com/video{autor}_{attache.get('video').get('id')}"]
            elif attache_type == 'photo':
                attachments_dict['photo'] = attachments_dict.get(attache_type, []) + [
                    photo_attachment_parsing(pics=attache[attache_type]['sizes'])]
            # elif attache_type == 'doc':
            #     attachments_dict['doc'] = docs_attachment_parsing(data=attache[attache_type])
            # elif attache_type == 'link' or 'audio':
            #     attachments_dict['url'] = attachments_dict.get(attache_type, []) + [
            #         attache[attache_type]['url']]
            # elif attache_type == 'poll':
            #     attachments_dict['poll'] = attachments_dict.get(attache_type, []) + [
            #         attache[attache_type]['question']]
        result = json.dumps(attachments_dict)
        return result
    return None


async def attache_info(attache: json) -> str | None:
    result = str()
    if attache is not None:
        data = json.loads(attache)
        for k, v in data.items():
            result += f"{k}:{len(v)} "
        return result.strip()
    return None


async def scrape_vk_data(data: dict, session: ClientSession, **kwargs) -> dict:
    result = dict()
    is_repost = kwargs.get('is_repost')
    phone_number = await get_contact(data=data, is_repost=is_repost)
    signer_id = await de_anonymization(data=data, is_repost=is_repost, phone_number=phone_number)
    repost_source_id = data['copy_history'][0].get('from_id') if is_repost else None
    attachments = await pars_attachments(data=data, is_repost=is_repost)
    result.update(
        {
            'url': f"https://vk.com/wall{data.get('from_id')}_{data.get('id')}",
            'date': datetime.fromtimestamp(data.get('date')),
            'source': kwargs.get('source'),
            'internal_id': data.get('id'),
            'source_id': data.get('owner_id'),
            'source_title': kwargs.get('screen_name'),
            'phone_number': phone_number,
            'signer_id': signer_id,
            'signer_name': await get_name_by_id(_id=signer_id, session=session),
            'is_repost': is_repost,
            'repost_source_id': repost_source_id,
            'repost_source_title': await get_name_by_id(_id=repost_source_id, session=session),
            'text': data['copy_history'][0].get('text') if is_repost else data.get('text'),
            'attachments': attachments,
            'attachments_info': await attache_info(attache=attachments)
        }
    )
    # print(result['source_title'], result['internal_id'], result['url'])
    return result


async def send_notification(session: ClientSession, text: str):
    async with session.get(
            url=f"https://api.telegram.org/bot{source_settings.bot_token.get_secret_value()}"
                f"/sendMessage?chat_id={source_settings.post_editor}"
                f"&text=Обновлено:{text}"
    ) as resp:  # f"&disable_notification={source_settings.disable_notification}"
        await resp.json()


async def alert_editor(source: str):
    await bot.send_message(chat_id=source_settings.post_editor, text=f'Обновлено:\n\n{source}')
