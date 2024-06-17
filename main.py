import asyncio

from logic import cyclic_observation


async def main():
    await cyclic_observation(sources='sources')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('script stopped')
