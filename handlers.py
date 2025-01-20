from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form, FoodLogState
from database import save_to_database, get_user_data, update_logged_water, update_log_calories, get_workout, update_burned_calories, update_water_goal
from calculation import calculate_calorie_goal, calculate_water_goal, get_food_info, calculate_workout_effect
from decimal import Decimal
import matplotlib.pyplot as plt
import io
from aiogram.types import BufferedInputFile

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
        "/set_profile - Создание анкеты\n"
        "/view_profile - Просмотр анкеты\n"
        "/log_water - Количество воды\n"
        "/log_food - Количество каллорий\n"
        "/log_workout - Тренировки\n"
        "/check_progress - Прогресс по воде и калориям\n"
        "/progress_chart - График прогресса",
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
        activity_level = int(data["activity_level"])
        city = data["city"]
    except KeyError as e:
        await message.reply("Некоторые данные отсутствуют. Попробуйте начать заново.")
        await state.clear()
        return
    except ValueError:
        await message.reply("Пожалуйста, введите корректные данные.")
        return

    # Расчёт цели калорий
    if user_input == "нет":
        calorie_goal = calculate_calorie_goal(weight, height, age, activity_level)
    else:
        try:
            calorie_goal = float(user_input)
        except ValueError:
            await message.reply("Пожалуйста, введите число для цели калорий или 'нет'.")
            return 

    # Обновляем состояние
    await state.update_data(calorie_goal=calorie_goal)
    water_goal = calculate_water_goal(weight, activity_level, city)
    # Сохраняем данные в базу
    user_id = message.from_user.id
    data_to_save = {
        "user_id": user_id,
        "weight": weight,
        "height": height,
        "age": age,
        "activity_level": activity_level,
        "city": city,
        "calorie_goal": calorie_goal,
        "water_goal": water_goal
    }

    try:
        await save_to_database(data_to_save)
        await message.reply(
            f"Ваши данные успешно сохранены в базу данных!\n"
            f"Цель калорий: {calorie_goal} ккал.\n"
        )
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка при сохранении в базу данных: {e}")
    await state.clear()

@router.message(Command("view_profile"))
async def view_profile(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_data = await get_user_data(user_id)

        if not user_data:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return
        await message.reply(
                f"Ваш профиль:\n"
                f"⚖️Вес: {user_data['weight']} кг.\n"
                f"📈Рост: {user_data['height']} см.\n"
                f"🧓Возраст: {user_data['age']} лет.\n"
                f"🌆Город: {user_data['city']}.\n"
                f"🥐Цель калорий: {user_data['calorie_goal']} ккал.\n"
                f"💧Цель воды: {user_data['water_goal']} мл.\n"
            )
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")

@router.message(Command("log_water"))
async def log_water(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        amount = int(message.text.split(" ")[1])  # Получаем количество воды из команды
        user_data = await get_user_data(user_id)

        if not user_data:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return
        
        water_goal =  user_data.get("water_goal", 0)
        current_logged = user_data.get("logged_water", 0)
        new_logged = current_logged + amount
        remaining_water = max(0, water_goal - new_logged)

        # Обновляем данные в базе
        await update_logged_water(user_id, new_logged)

        await message.reply(
            f"Записано: {amount} мл воды. Всего выпито: {new_logged} мл. Осталось: {remaining_water} мл до выполнения нормы."
        )
    except (IndexError, ValueError):
        await message.reply("Пожалуйста, используйте формат команды: /log_water <количество в мл>")
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    try:
        # Получаем информацию о продукте
        product_name = message.text.split(" ", 1)[1]  # Берём всё после команды
        amount = get_food_info(product_name)

        if not amount:
            await message.reply("Продукт не найден. Попробуйте снова!")
            return

        # Сохраняем информацию о продукте в состоянии
        await state.update_data(product=amount)

        # Спрашиваем у пользователя, сколько граммов он съел
        await message.reply(
            f"{amount['name']} содержит {amount['calories']} ккал на 100 г.\nСколько грамм вы съели?"
        )
        await state.set_state(FoodLogState.waiting_for_food_amount)

    except IndexError:
        await message.reply("Пожалуйста, используйте формат команды: /log_food <название продукта>")
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")


@router.message(FoodLogState.waiting_for_food_amount)
async def process_food_amount(message: Message, state: FSMContext):
    try:
        # Получаем данные из состояния
        user_data = await state.get_data()
        product = user_data.get("product")

        # Проверяем, что введено число
        grams = int(message.text)
        if grams <= 0:
            await message.reply("Количество грамм должно быть положительным числом. Попробуйте снова!")
            return

        # Рассчитываем калории
        calories = (Decimal(product['calories']) / Decimal(100)) * Decimal(grams)

        # Получаем данные пользователя
        user_id = message.from_user.id
        user_profile = await get_user_data(user_id)

        if not user_profile:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return

        # Обновляем данные калорий
        calorie_goal = Decimal(user_profile.get("calorie_goal", 0))
        current_logged = Decimal(user_profile.get("logged_calories", 0))
        new_logged = current_logged + calories
        remaining_calories = max(Decimal(0), calorie_goal - new_logged)

        await update_log_calories(user_id, float(new_logged))  # Сохраняем как float, если нужно

        # Отправляем ответ пользователю
        await message.reply(
            f"Вы съели {grams} г {product['name']}, это {calories:.2f} ккал.\n"
            f"Всего за сегодня: {new_logged:.2f} ккал. Осталось до нормы: {remaining_calories:.2f} ккал."
        )

    except ValueError:
        await message.reply("Пожалуйста, введите число (граммы). Попробуйте снова!")
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")
    await state.clear()

@router.message(Command("log_workout"))
async def log_workout(message: Message, state: FSMContext):
    try:
        # Проверяем правильность команды
        command_parts = message.text.split(" ", 2)
        if len(command_parts) < 3:
            await message.reply("Пожалуйста, используйте формат команды: /log_workout <тип тренировки> <время (мин)>")
            return

        workout_type = command_parts[1].lower()  # Тип тренировки
        try:
            workout_time = int(command_parts[2])  # Время в минутах
        except ValueError:
            await message.reply("Пожалуйста, укажите время в формате числа (минуты).")
            return

        if workout_time <= 0:
            await message.reply("Время тренировки должно быть больше нуля.")
            return

        # Получаем пользователя из базы
        user_id = message.from_user.id
        user_profile = await get_user_data(user_id)
        workout = await get_workout(workout_type)
        if not user_profile:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return
        if not workout:
            await message.reply("Тренировка не найдена. Попробуйте другую.")
            return
        # Получаем вес пользователя (для расчёта калорий)
        weight = int(user_profile["weight"])

        # Расчёт сожжённых калорий и воды
        calories_burned, additional_water = calculate_workout_effect(workout_time, weight, workout["calorie_rates"], workout["water_rate_per_30_min"])

        # Обновляем данные пользователя
        current_burned_calories = Decimal(user_profile.get("burned_calories", 0))
        current_logged_water = Decimal(user_profile.get("water_goal", 0))

        new_burned_calories = current_burned_calories + calories_burned
        new_logged_water = current_logged_water + additional_water

        # Сохраняем в базе данных
        await update_burned_calories(user_id, float(new_burned_calories))  # Обновляем сожжённые калории
        await update_water_goal(user_id, float(new_logged_water))    # Обновляем воду

        # Отправляем пользователю результат
        await message.reply(
            f"💪 {workout_type.capitalize()} {workout_time} минут — {calories_burned:.2f} ккал.\n"
            f"💧 Дополнительно выпейте {additional_water} мл воды."
        )

    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")


@router.message(Command("check_progress"))
async def check_progress(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_data = await get_user_data(user_id)

        if not user_data:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
            return
        current_logged = user_data.get("logged_water", 0)
        remaining_water = max(0, user_data["water_goal"] - current_logged)
        remaining_callories = max(0, user_data["logged_calories"] - user_data["burned_calories"])
        await message.reply(
                f"📊 Прогресс:\n"
                f"Вода:\n"
                f"- Выпито: {user_data['logged_water']} мл из {user_data['water_goal']} мл.\n"
                f"- Осталось: {remaining_water} мл.\n"
                f"Калории:\n"
                f"- Потреблено: {user_data['logged_calories']} ккал из {user_data['calorie_goal']} ккал.\n"
                f"- Сожжено: {user_data['burned_calories']} ккал.\n"
                f"- Баланс: {remaining_callories} ккал.\n"
            )
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка: {e}")

async def generate_progress_chart(user_id):
    user_data = await get_user_data(user_id)
    if not user_data:
        return None

    # Данные для графика
    water_goal = user_data["water_goal"]
    logged_water = user_data["logged_water"]
    calorie_goal = user_data["calorie_goal"]
    logged_calories = user_data["logged_calories"]
    burned_calories = user_data["burned_calories"]

    # График
    fig, axs = plt.subplots(2, 1, figsize=(6, 8))
    fig.suptitle('Прогресс пользователя', fontsize=16)

    # График воды
    axs[0].bar(['Выпито', 'Цель'], [logged_water, water_goal], color=['blue', 'lightblue'])
    axs[0].set_title('Прогресс по воде')
    axs[0].set_ylabel('мл')
    axs[0].set_ylim(0, max(water_goal, logged_water) + 500)

    # График калорий
    axs[1].bar(['Потреблено', 'Сожжено', 'Цель'], [logged_calories, burned_calories, calorie_goal],
               color=['orange', 'red', 'lightgreen'])
    axs[1].set_title('Прогресс по калориям')
    axs[1].set_ylabel('ккал')
    axs[1].set_ylim(0, max(calorie_goal, logged_calories, burned_calories) + 500)

    # Сохранение графика в буфер
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return BufferedInputFile(buf.read(), filename='progress.png')

@router.message(Command("progress_chart"))
async def send_progress_chart(message: Message):
    try:
        user_id = message.from_user.id
        chart = await generate_progress_chart(user_id)

        if chart:
            await message.answer_photo(chart, caption="📊 Ваш прогресс по воде и калориям.")
        else:
            await message.reply("Ваш профиль не найден. Используйте команду /set_profile для его создания.")
    except Exception as e:
        await message.reply(f"⚠️Произошла ошибка при создании графика: {e}")


# Функция для подключения обработчиков
def setup_handlers(dp):
    dp.include_router(router)
