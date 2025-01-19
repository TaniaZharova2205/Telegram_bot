from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form
import aiohttp
from database import save_to_database, get_user_data, update_logged_water, log_calories
from config import KEY_WETHER
import requests

def calculate_calorie_goal(weight, height, age, activity_minutes):
    # Основной метаболизм
    base_calories = 10 * weight + 6.25 * height - 5 * age

    # Дополнительные калории за активность
    if activity_minutes < 30:
        activity_calories = 200
    elif activity_minutes <= 60:
        activity_calories = 300
    else:
        activity_calories = 400

    # Итоговая цель калорий
    return base_calories + activity_calories

def calculate_water_goal(weight: int, activity_minutes: int, city: str) -> int:
    try:
        res_wether = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&APPID={KEY_WETHER}")
        temperature = res_wether.json()['main']['temp']
        base_water = weight * 30  # мл на кг веса
        activity_water = (activity_minutes // 30) * 500  # доп. вода за активность
        weather_water = 500 if temperature > 25 else 0  # доп. вода за жару
        return base_water + activity_water + weather_water
    except Exception as e:
        print(f"Ошибка при обновлении логов воды. В базе нет данного города: {city}. Ошибка: {e}")
        raise


def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    print(f"Ошибка: {response.status_code}")
    return None

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Добро пожаловать! Я ваш бот.\nВведите /help для списка команд.")

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Пример диалога\n"
        "/log_water - Количество воды\n"
        "/log_food - Еда\n"
    )

# FSM: диалог с пользователем
@router.message(Command("set_profile"))
async def start_set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity_level)

@router.message(Form.activity_level)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(activity_level=message.text)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.reply(
        "Хотите ли вы указать цель калорий вручную? Если да, напишите её в формате числа. Если нет, отправьте 'нет'."
    )
    await state.set_state(Form.calorie_goal)

@router.message(Form.calorie_goal)
async def process_calorie_goal(message: Message, state: FSMContext):
    user_input = message.text.lower()

    # Получаем данные из состояния
    data = await state.get_data()
    try:
        weight = int(data["weight"])
        height = int(data["height"])
        age = int(data["age"])
        activity_minutes = int(data["activity_level"])
        city = data["city"]  # Город уже должен быть в состоянии
    except KeyError as e:
        await message.reply("Некоторые данные отсутствуют. Попробуйте начать заново.")
        await state.clear()
        return
    except ValueError:
        await message.reply("Пожалуйста, введите корректные данные.")
        return

    # Расчёт цели калорий
    if user_input == "нет":
        calorie_goal = calculate_calorie_goal(weight, height, age, activity_minutes)
    else:
        try:
            calorie_goal = int(user_input)
        except ValueError:
            await message.reply("Пожалуйста, введите число для цели калорий или 'нет'.")
            return 

    # Обновляем состояние
    await state.update_data(calorie_goal=calorie_goal)

    # Сохраняем данные в базу
    user_id = message.from_user.id
    data_to_save = {
        "user_id": user_id,
        "weight": weight,
        "height": height,
        "age": age,
        "activity_level": activity_minutes,
        "city": city,
        "calorie_goal": calorie_goal
    }

    try:
        await save_to_database(data_to_save)
        await message.reply(
            f"Ваши данные успешно сохранены в базу данных!\n"
            f"Цель калорий: {calorie_goal} ккал.\n"
        )
    except Exception as e:
        await message.reply(f"Произошла ошибка при сохранении в базу данных: {e}")
    await state.clear()

@router.message(Command("log_water"))
async def log_water(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = int(message.text.split(" ")[1])  # Получаем количество воды из команды
        user_data = await get_user_data(user_id)

        if not user_data:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return
        
        # Расчёт цели воды
        water_goal = calculate_water_goal(user_data["weight"], user_data["activity_level"], user_data["city"])
        current_logged = user_data.get("logged_water", 0)
        new_logged = current_logged + amount
        remaining_water = max(0, water_goal - new_logged)

        # Обновляем данные в базе
        await update_logged_water(user_id, water_goal, new_logged)

        await message.reply(
            f"Записано: {amount} мл воды. Всего выпито: {new_logged} мл. Осталось: {remaining_water} мл до выполнения нормы."
        )
    except (IndexError, ValueError):
        await message.reply("Пожалуйста, используйте формат команды: /log_water <количество в мл>")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    try:
        product_name = " ".join(message.text.split(" ")[1:])  # Название продукта
        if not product_name:
            await message.reply("Пожалуйста, укажите название продукта. Например: /log_food банан")
            return

        # Используем API для получения данных о продукте
        product_info = await get_food_info(product_name)
        if not product_info:
            await message.reply(f"Не удалось найти информацию о продукте '{product_name}'. Попробуйте ещё раз.")
            return

        calories_per_100g = product_info["calories_per_100g"]
        await state.update_data(product_calories=calories_per_100g)
        await state.update_data(product_name=product_name)

        await message.reply(f"{product_name.capitalize()} — {calories_per_100g} ккал на 100 г. Сколько грамм вы съели?")
        await state.set_state(Form.food_amount)
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

@router.message(Form.food_amount)
async def log_food_amount(message: Message, state: FSMContext):
    try:
        grams = int(message.text)
        data = await state.get_data()
        product_name = data["product_name"]
        calories_per_100g = data["product_calories"]

        total_calories = (calories_per_100g * grams) / 100
        user_id = message.from_user.id

        # Обновляем базу данных
        await log_calories(user_id, total_calories)

        await message.reply(f"Записано: {total_calories:.1f} ккал ({grams} г {product_name}).")
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите корректное количество в граммах.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
