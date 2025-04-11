import asyncio

from aiogram import Bot, Dispatcher
from settings import settings
from app.core import router

from app.db.database import SQLBase


API_TOKEN = settings.Secure.API_KEY

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

dp.include_router(router)



async def main():
    await SQLBase(settings.Db.url).create_db()
    await dp.start_polling(bot)


async def stop():
    await dp.stop_polling()


if __name__ == "__main__":
    asyncio.run(main())
