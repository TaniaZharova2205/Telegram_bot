import psycopg2
from config import DATABASE
def get_connection():
    return psycopg2.connect(
        DATABASE
    )


# Функция для сохранения данных в базу
async def save_to_database(data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Используем INSERT ... ON CONFLICT для upsert
        query = """
        INSERT INTO user_profiles (
            user_id, weight, height, age, activity_level, city, calorie_goal, water_goal, logged_water, logged_calories, burned_calories
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            weight = EXCLUDED.weight,
            height = EXCLUDED.height,
            age = EXCLUDED.age,
            activity_level = EXCLUDED.activity_level,
            city = EXCLUDED.city,
            calorie_goal = EXCLUDED.calorie_goal,
            water_goal = EXCLUDED.water_goal,
            logged_water = EXCLUDED.logged_water,
            logged_calories = EXCLUDED.logged_calories,
            burned_calories = EXCLUDED.burned_calories;
        """
        cursor.execute(query, (
            data["user_id"], data["weight"], data["height"], data["age"], data["activity_level"],
            data["city"], data["calorie_goal"], data["water_goal"], 0, 0, 0
        ))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при сохранении данных. Данные: {data}. Ошибка: {e}")
        raise
    finally:
        conn.close()


# Функция для получения данных пользователя
async def get_user_data(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM user_profiles WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]  # Получаем имена колонок
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()


# Функция для обновления логов воды
async def update_logged_water(user_id, logged_water):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE user_profiles SET logged_water = %s WHERE user_id = %s"
        cursor.execute(query, (logged_water, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении логов воды. User ID: {user_id}, Logged Water: {logged_water}. Ошибка: {e}")
        raise
    finally:
        conn.close()


# Функция для логирования калорий
async def update_log_calories(user_id, calories):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE user_profiles SET logged_calories = %s WHERE user_id = %s"
        cursor.execute(query, (calories, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при логировании калорий. User ID: {user_id}, Calories: {calories}. Ошибка: {e}")
        raise
    finally:
        conn.close()


# Функция для обновления сожженных калорий
async def update_burned_calories(user_id, calories):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE user_profiles SET burned_calories = %s WHERE user_id = %s"
        cursor.execute(query, (calories, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при логировании сожжённых калорий. User ID: {user_id}, Calories: {calories}. Ошибка: {e}")
        raise
    finally:
        conn.close()


# Функция для обновления логов воды
async def update_water_goal(user_id, water_goal):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE user_profiles SET water_goal = %s WHERE user_id = %s"
        cursor.execute(query, (water_goal, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении цели воды. User ID: {user_id}, Water Goal: {water_goal}. Ошибка: {e}")
        raise
    finally:
        conn.close()


# Функция для получения данных пользователя
async def get_workout(title):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM workout WHERE title = %s"
        cursor.execute(query, (title,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()

