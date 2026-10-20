"""Модуль запросов: список запросов к Wolfram|Alpha (10 обязательных + 5 своих)."""

# Каждый запрос: (категория, текст запроса на английском)
REQUIRED_QUERIES = [
    ("Математический расчёт",   "integrate x^2 sin^3 x dx"),
    ("Фактологический запрос",  "population of Russia 2024"),
    ("Химический расчёт",       "molar mass of H2SO4"),
    ("Физический расчёт",       "kinetic energy of 5kg object at 10m/s"),
    ("Географический запрос",   "distance between Moscow and Saint Petersburg"),
    ("Финансовый запрос",       "100 USD to RUB"),
    ("Временной запрос",        "current time in Kazan"),
    ("Астрономический запрос",  "distance to Mars"),
    ("Медицинский запрос",      "body mass index 180cm 75kg"),
    ("Лингвистический запрос",  "translate hello to Russian"),
]

# 5 дополнительных запросов на выбор
EXTRA_QUERIES = [
    ("Решение уравнения",       "solve x^2 - 5x + 6 = 0"),
    ("Производная",             "derivative of x^3 * ln(x)"),
    ("Статистика",              "mean and standard deviation of {4, 8, 15, 16, 23, 42}"),
    ("Физическая константа",    "speed of light in km/s"),
    ("Географический факт",     "population of Kazan"),
]

ALL_QUERIES = REQUIRED_QUERIES + EXTRA_QUERIES
