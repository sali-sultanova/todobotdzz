import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
import json
from bottoken import TOKEN
from aiogram.client.session.aiohttp import AiohttpSession

FILE = "tasks.json"

dp = Dispatcher()


class TaskState(StatesGroup):
    add1 = State()
    done1 = State()
    delete1 = State()


def load_data():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f)


tasks = load_data()

@dp.message(Command("start"))
async def main_start(message: Message):
    await message.answer(
        f"Добро пожаловать., {message.from_user.first_name}!\n Я бот-менеджер задач\n Команды: \n /add - добавление задачи\n /tasks - просмотр задач\n /done - отметить задачу выполненной \n /delete - удалить задачу \n /stats - статистика ")


@dp.message(Command("add"))
async def adds(message: Message, state: FSMContext):
    await message.answer(f"Напиши текст задачи")
    await state.set_state(TaskState.add1)


@dp.message(TaskState.add1)
async def add_finish(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    if uid not in tasks:
        tasks[uid] = []
    tasks[uid].append({"text": message.text, "done": False})

    save_data(tasks)
    await message.answer("Задача добавлена!")
    await state.clear()


@dp.message(Command("tasks"))
async def alltask(message: Message):
    uid = str(message.from_user.id)
    if uid in tasks:
        tasks1 = tasks[uid]
    else:
        tasks1 = []
    if not tasks1:
        return await message.answer("Список пуст.")
    res = "Ваши задачи:\n"
    num = 1
    for i in tasks1:
        tik = "✅" if i["done"] else ""
        res += f"{num}. {i['text']} {tik}\n"
        num += 1
    await message.answer(res)


@dp.message(Command("done"))
async def done_start(message: Message, state: FSMContext):
    await message.answer("Напиши номер выполненной задачи:")
    await state.set_state(TaskState.done1)


@dp.message(TaskState.done1)
async def done_finish(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    if uid in tasks:
        tasks1 = tasks[uid]
    else:
        tasks1 = []
    try:
        ind = int(message.text) - 1
        if 0 <= ind < len(tasks1):
            tasks1[ind]["done"] = True
            save_data(tasks)
            await message.answer(f"Задача '{tasks1[ind]['text']}' выполнена! ✅")
        else:
            await message.answer("Задачи не существует.")
    except:
        await message.answer("Ошибка! Введите число.")
    await state.clear()


@dp.message(Command("delete"))
async def delete_start(message: Message, state: FSMContext):
    await message.answer("Напиши номер задачи для удаления:")
    await state.set_state(TaskState.delete1)

@dp.message(TaskState.delete1)
async def delete_finish(message: Message, state: FSMContext):
    uid = str(message.from_user.id)
    if uid in tasks:
        tasks1 = tasks[uid]
    else:
        tasks1 = []
    try:
        ind = int(message.text) - 1
        removed = tasks1.pop(ind)
        save_data(tasks)
        await message.answer(f"Задача '{removed['text']}' удалена")
    except:
        await message.answer("Ошибка! Введите число.")
    await state.clear()


@dp.message(Command("stats"))
async def stats(message: Message):
    uid = str(message.from_user.id)
    if uid in tasks:
        tasks1 = tasks[uid]
    else:
        tasks1 = []
    total = len(tasks1)
    donecount = sum(1 for i in tasks1 if i["done"])
    await message.answer(f"Всего: {total}\nВыполнено: {donecount}\nОсталось: {total - donecount}")

async def main():
    session = AiohttpSession(proxy="http://oNKKt5:H0ET6w@161.115.231.116:9019")
    bot = Bot(
        token=TOKEN,
        session = session
    )

    print("Бот запущен")
    await dp.start_polling(bot)


asyncio.run(main())
