from aiogram import executor
from bot.bot import dp, bot
from bot.handlers.commands import on_startup_commands

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup_commands, skip_updates=True)