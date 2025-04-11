from aiogram import Router
from app.handlers import rout

router = Router()

router.include_router(rout)
