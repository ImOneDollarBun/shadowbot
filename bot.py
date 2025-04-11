import asyncio

from aiogram import Bot, Dispatcher
from settings import settings
from app.db.database import SQLBase
from app.handlers import rout


API_TOKEN = settings.Secure.API_KEY

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
sq = SQLBase(settings.Db.url)

dp.include_router(rout)


async def main():
    await sq.create_db()
    await dp.start_polling(bot)


async def stop():
    await dp.stop_polling()


if __name__ == "__main__":
    asyncio.run(main())
