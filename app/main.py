import asyncio
from common import creds_notion_api
from services.container import ApplicationContainer


async def main():
    container = ApplicationContainer()
    telegram_bot = container.telegram_bot(token=creds_notion_api.bot_token)
    await telegram_bot.run()


if __name__ == '__main__':
    asyncio.run(main())
