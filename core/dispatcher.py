from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher

storage = MemoryStorage()
dp = Dispatcher(storage=storage)