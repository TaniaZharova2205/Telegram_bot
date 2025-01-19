from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    weight = State()
    height =State()
    age = State()
    activity_level = State()
    city = State()
    calorie_goal = State()
    water_goal = State()
    logged_water = State()
    logged_calories = State()
    burned_calories = State()
