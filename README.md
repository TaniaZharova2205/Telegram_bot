## Разработка Telegram-бота с использованием aiogram 3.x

### 1. Скрипт SQL для Postresql
```sql
CREATE TABLE user_profiles (
    user_id BIGINT PRIMARY KEY,
    weight INT NOT NULL,
    height INT NOT NULL,
    age INT NOT NULL,
    activity_level INT NOT NULL,
    city VARCHAR(50) NOT NULL,
    calorie_goal INT NOT NULL,
    water_goal INT NOT NULL DEFAULT 0,
    logged_water INT NOT NULL DEFAULT 0,
    logged_calories INT NOT NULL DEFAULT 0,
    burned_calories INT NOT NULL DEFAULT 0
);

CREATE TABLE workout (
    id SERIAL PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    calorie_rates NUMERIC(4, 2) NOT NULL,
    water_rate_per_30_min NUMERIC(7, 2) NOT NULL DEFAULT 0
);

INSERT INTO workout (id, title, calorie_rates, water_rate_per_30_min)
VALUES
    (1, 'бег', 0.12, 300),
    (2, 'ходьба', 0.05, 150),
    (3, 'велосипед', 0.09, 250),
    (4, 'плавание', 0.1, 400),
    (5, 'йога', 0.03, 100);
```

### 2. Скриншоты выполнения команд

![1 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/1.png)

![2 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/2.png)

![3 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/3.png)

![4 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/4.png)

### 3. Деплой бота

Логи бота

![5 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/5.png)

![6 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/6.png)

Логи базы данных

![7 картинка](https://github.com/TaniaZharova2205/Telegram_bot/blob/main/image/7.png)
