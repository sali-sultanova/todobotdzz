import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
import json
from bottoken import TOKEN
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


FILE = "tasks.json"

dp = Dispatcher()
sh = AsyncIOScheduler()

class TaskState(StatesGroup):
    add1 = State()
    adddeadline= State()
    remindtime = State()
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

async def remind(bot: Bot, chat_id: str, text: str):
    await bot.send_message(chat_id, f"!!!: {text}")

def get_remind():
    buttons = [
        [InlineKeyboardButton(text="Через 1 час", callback_data="r_60")],
        [InlineKeyboardButton(text="Через 3 часа", callback_data="r_180")],
        [InlineKeyboardButton(text="Через 1 день", callback_data="r_1440")],
        [InlineKeyboardButton(text="Ввести свою дату", callback_data="r_custom")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
    await state.update_data(task=message.text)
    await message.answer("Введите дату дедлайна (ex: 29.03.2026):")
    await state.set_state(TaskState.adddeadline)

@dp.message(TaskState.adddeadline)
async def adddeadline_finish(message: Message, state: FSMContext):
    await state.update_data(deadline=message.text)
    await message.answer("Когда напоминанить?", reply_markup=get_remind())
    await state.set_state(TaskState.remindtime)

@dp.callback_query(F.data.startswith("r"))
async def remind_choice(callback: CallbackQuery, state: FSMContext):
    if callback.data == "r_custom":
        await callback.message.answer("Введите дату напоминания (формат: 29.03.2026 16:00):")
        await callback.answer()
        return
    minutes = int(callback.data.split("_")[1])
    userd = await state.get_data()
    task = userd['task']
    deadline = userd['deadline']
    uid = str(callback.from_user.id)
    if uid not in tasks:
        tasks[uid] = []
    tasks[uid].append({"text": task, "done": False, "date": deadline})
    save_data(tasks)

    timer = datetime.now() + timedelta(minutes=minutes)
    sh.add_job(
        remind,
        trigger="date",
        run_date=timer,
        kwargs={"bot": callback.bot, "chat_id": uid, "text": task}
    )
    await callback.message.answer(f"Задача добавлена! Напомню через {minutes} мин.")
    await callback.answer()
    await state.clear()


@dp.message(TaskState.remindtime)
async def customremind(message: Message, state: FSMContext):
    try:
        timer = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        if timer < datetime.now():
            return await message.answer("Введите будущую дату:")
        await finish(message, state, timer)
    except ValueError:
        await message.answer("неправильный формат. Пример: 29.03.2026 18:00")

async def finish(message: Message, state: FSMContext, timer_date: datetime):
    userd = await state.get_data()
    task = userd['task']
    deadline = userd['deadline']
    uid = str(message.chat.id)
    if uid not in tasks:
        tasks[uid] = []
    tasks[uid].append({"text": task, "done": False, "date": deadline})
    save_data(tasks)
    sh.add_job(
        remind,
        trigger="date",
        run_date=timer_date,
        kwargs={"bot": message.bot, "chat_id": uid, "text": task}
    )
    await message.answer(f"Задача добавлена! Напомню: {timer_date.strftime('%d.%m %H:%M')}")
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
        if 'date' in i:
            deadline = i["date"]
        else:
            deadline = ""
        res += f"{num}. {i['text']} (дедлайн: {deadline})  {tik}\n"
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
    sh.start()
    await dp.start_polling(bot)


asyncio.run(main())
