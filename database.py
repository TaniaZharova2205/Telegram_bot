import pyodbc

# Функция для подключения к SQL Server
def get_connection():
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=LAPTOP-IM3H6O47;"  # Замените на имя вашего сервера
        "Database=slay_bot;"  # Замените на имя вашей базы данных
        "Trusted_Connection=yes;"
    )

# Функция для сохранения данных в базу
async def save_to_database(data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # SQL-запрос для вставки или обновления данных
        query = """
        MERGE user_profiles AS target
        USING (SELECT ? AS user_id) AS source
        ON target.user_id = source.user_id
        WHEN MATCHED THEN
            UPDATE SET
                weight = ?,
                height = ?,
                age = ?,
                activity_level = ?,
                city = ?,
                calorie_goal = ?
        WHEN NOT MATCHED THEN
            INSERT (user_id, weight, height, age, activity_level, city, calorie_goal)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        # Выполняем запрос
        cursor.execute(
            query,
            data["user_id"],  # Для проверки существования
            data["weight"], data["height"], data["age"], data["activity_level"], data["city"], data["calorie_goal"],
            data["user_id"], data["weight"], data["height"], data["age"], data["activity_level"], data["city"], data["calorie_goal"]
        )

        # Сохраняем изменения
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
        query = "SELECT * FROM [dbo].[user_profiles] WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        conn.close()

# Функция для обновления логов воды
async def update_logged_water(user_id, water_goal, logged_water):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = "UPDATE [dbo].[user_profiles] SET logged_water = ?, water_goal = ? WHERE user_id = ?"
        cursor.execute(query, (logged_water, water_goal, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при обновлении логов воды. User ID: {user_id}, Logged Water: {logged_water}. Ошибка: {e}")
        raise
    finally:
        conn.close()

# Функция для логирования калорий
async def log_calories(user_id, calories):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = """
        UPDATE [dbo].[user_profiles]
        SET logged_calories = COALESCE(logged_calories, 0) + ?
        WHERE user_id = ?
        """
        cursor.execute(query, (calories, user_id))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при логировании калорий. User ID: {user_id}, Calories: {calories}. Ошибка: {e}")
        raise
    finally:
        conn.close()
