from func import read_sources


async def start_script(sources: str):
    await read_sources(file=sources)
