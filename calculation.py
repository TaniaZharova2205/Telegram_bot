import requests
from decimal import Decimal
from config import KEY_WETHER

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
    try:
        data = response.json()
        products = data.get('products', [])
        if products:
            # Найдём продукт с самой низкой калорийностью
            lowest_calorie_product = min(
                products,
                key=lambda p: p.get('nutriments', {}).get('energy-kcal_100g', float('inf'))
            )
            return {
                'name': lowest_calorie_product.get('product_name', 'Неизвестно'),
                'calories': lowest_calorie_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
        return None
    except Exception as e:
        print(f"⚠️Ошибка: {response.status_code}")
        raise


def calculate_workout_effect(time_minutes: int, weight_kg: int, calorie_rate, water_rate):
    """
    Рассчитывает сожжённые калории и дополнительный расход воды на основе типа тренировки.
    """
    # Считаем калории
    calories_burned = calorie_rate * weight_kg * time_minutes
    # Считаем воду
    additional_water = (time_minutes // 30) * water_rate
    return Decimal(calories_burned), Decimal(additional_water)