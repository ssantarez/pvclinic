import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, CLINIC_NAME
from database import save_session, save_contact
from data import ZONES, PROBLEMS_BY_ZONE
from recommendations import get_recommendations
from pdf_generator import generate_pdf
from amocrm import send_to_amocrm

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class QuizState(StatesGroup):
    choose_direction = State()
    age = State()
    zones = State()
    problem = State()
    cleanser = State()
    skin_type = State()
    skin_problems = State()
    contact_name = State()
    contact_phone = State()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подобрать процедуры")],
            [KeyboardButton(text="Подобрать домашний уход")],
            [KeyboardButton(text="Комплексный подбор")],
        ],
        resize_keyboard=True
    )

def get_age_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="До 25"), KeyboardButton(text="25-35")],
            [KeyboardButton(text="35-45"), KeyboardButton(text="45-55")],
            [KeyboardButton(text="55+")],
        ],
        resize_keyboard=True
    )

def get_zones_keyboard(selected=None):
    if selected is None:
        selected = []
    buttons = []
    for zone in ZONES:
        check = "✅ " if zone in selected else "➖ "
        buttons.append([KeyboardButton(text=f"{check}{zone}")])
    buttons.append([KeyboardButton(text="Готово")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_problems_keyboard(zone):
    problems = PROBLEMS_BY_ZONE.get(zone, ["морщины", "акне", "пигментация"])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=p)] for p in problems], resize_keyboard=True)

def get_cleanser_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пенка/гель")],
            [KeyboardButton(text="Мицеллярная вода")],
            [KeyboardButton(text="Обычная вода")],
        ],
        resize_keyboard=True
    )

def get_skin_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Жирная"), KeyboardButton(text="Сухая")],
            [KeyboardButton(text="Комбинированная"), KeyboardButton(text="Чувствительная")],
        ],
        resize_keyboard=True
    )

def get_skin_problems_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Акне")],
            [KeyboardButton(text="Пигментация")],
            [KeyboardButton(text="Морщины")],
            [KeyboardButton(text="Нет проблем")],
        ],
        resize_keyboard=True
    )

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"Добро пожаловать в {CLINIC_NAME}!\nВыберите:", reply_markup=get_main_keyboard())

@dp.message(F.text == "Подобрать процедуры")
async def choose_procedures(message: types.Message, state: FSMContext):
    await state.update_data(direction="procedures")
    await state.set_state(QuizState.age)
    await message.answer("Сколько вам лет?", reply_markup=get_age_keyboard())

@dp.message(F.text == "Подобрать домашний уход")
async def choose_homecare(message: types.Message, state: FSMContext):
    await state.update_data(direction="homecare")
    await state.set_state(QuizState.age)
    await message.answer("Сколько вам лет?", reply_markup=get_age_keyboard())

@dp.message(F.text == "Комплексный подбор")
async def choose_complex(message: types.Message, state: FSMContext):
    await state.update_data(direction="complex")
    await state.set_state(QuizState.age)
    await message.answer("Сколько вам лет?", reply_markup=get_age_keyboard())

@dp.message(QuizState.age)
async def process_age(message: types.Message, state: FSMContext):
    age = message.text
    if age not in ["До 25", "25-35", "35-45", "45-55", "55+"]:
        await message.answer("Выберите из кнопок")
        return
    await state.update_data(age=age)
    await state.set_state(QuizState.zones)
    await state.update_data(zones=[])
    await message.answer("Выберите зоны (можно несколько):", reply_markup=get_zones_keyboard([]))

@dp.message(QuizState.zones, F.text.startswith(("➖", "✅")))
async def toggle_zone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    zones = data.get("zones", [])
    zone_name = message.text.replace("✅ ", "").replace("➖ ", "")
    if zone_name in zones:
        zones.remove(zone_name)
    else:
        zones.append(zone_name)
    await state.update_data(zones=zones)
    await message.answer("Выбранные зоны:", reply_markup=get_zones_keyboard(zones))

@dp.message(QuizState.zones, F.text == "Готово")
async def zones_done(message: types.Message, state: FSMContext):
    data = await state.get_data()
    zones = data.get("zones", [])
    if not zones:
        await message.answer("Выберите хотя бы одну зону")
        return
    await state.update_data(remaining_zones=zones.copy(), problems=[])
    await state.set_state(QuizState.problem)
    await message.answer(f"Для зоны {zones[0]} выберите проблему:", reply_markup=get_problems_keyboard(zones[0]))

@dp.message(QuizState.problem)
async def process_problem(message: types.Message, state: FSMContext):
    data = await state.get_data()
    problems = data.get("problems", [])
    remaining = data.get("remaining_zones", [])
    problems.append(message.text)
    remaining.pop(0)
    await state.update_data(problems=problems, remaining_zones=remaining)
    if remaining:
        await message.answer(f"Для зоны {remaining[0]} выберите проблему:", reply_markup=get_problems_keyboard(remaining[0]))
    else:
        direction = data.get("direction")
        if direction in ["homecare", "complex"]:
            await state.set_state(QuizState.cleanser)
            await message.answer("Чем вы умываетесь?", reply_markup=get_cleanser_keyboard())
        else:
            await state.set_state(QuizState.contact_name)
            await message.answer("Ваше имя?")

@dp.message(QuizState.cleanser)
async def process_cleanser(message: types.Message, state: FSMContext):
    await state.update_data(cleanser=message.text)
    await state.set_state(QuizState.skin_type)
    await message.answer("Тип кожи:", reply_markup=get_skin_type_keyboard())

@dp.message(QuizState.skin_type)
async def process_skin_type(message: types.Message, state: FSMContext):
    await state.update_data(skin_type=message.text.lower())
    await state.set_state(QuizState.skin_problems)
    await message.answer("Проблемы кожи:", reply_markup=get_skin_problems_keyboard())

@dp.message(QuizState.skin_problems)
async def process_skin_problems(message: types.Message, state: FSMContext):
    await state.update_data(skin_problems=[message.text.lower()])
    await state.set_state(QuizState.contact_name)
    await message.answer("Ваше имя?")

@dp.message(QuizState.contact_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(QuizState.contact_phone)
    await message.answer("Ваш номер телефона:", reply_markup=get_phone_keyboard())

@dp.message(QuizState.contact_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    
    answers = {
        "direction": data.get("direction"),
        "age": data.get("age"),
        "selected_zones": json.dumps(data.get("zones", [])),
        "problems": data.get("problems", []),
        "cleanser": data.get("cleanser"),
        "skin_type": data.get("skin_type"),
        "skin_problems": data.get("skin_problems", [])
    }
    
    rec = get_recommendations(answers)
    pdf = generate_pdf(message.from_user.id, data["name"], answers, rec)
    
    save_contact(message.from_user.id, data["name"], phone, message.from_user.username)
    await send_to_amocrm(message.from_user.id, data["name"], phone, message.from_user.username, answers, rec)
    
    await message.answer_document(types.BufferedInputFile(pdf.getvalue(), filename=f"PV_{data['name']}.pdf"))
    await message.answer("Спасибо! Скоро с вами свяжется администратор.", reply_markup=get_main_keyboard())
    await state.clear()

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())