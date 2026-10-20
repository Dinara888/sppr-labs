"""Этапы 1–3: получение текущих данных (OpenWeatherMap), загрузка исторических
данных (архив meteo.ru) и расчёт климатических норм по сезонам."""

from datetime import datetime

import pandas as pd
import requests

# Три города: название для OpenWeatherMap -> индекс станции ВМО в архиве meteo.ru
CITIES = {
    "Kazan": 27595,             # Казань
    "Moscow": 27612,            # Москва, ВДНХ
    "Saint Petersburg": 26063,  # Санкт-Петербург
}
CITY_RU = {"Kazan": "Казань", "Moscow": "Москва", "Saint Petersburg": "Санкт-Петербург"}
SEASON_RU = {"winter": "зима", "spring": "весна", "summer": "лето", "autumn": "осень"}


def get_season(month: int) -> str:
    """Определение сезона по номеру месяца."""
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


# ---------------------------------------------------------------- Этап 1
def get_current_weather(city: str, api_key: str) -> dict | None:
    """Получение текущих погодных данных для города из OpenWeatherMap."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "ru"}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return {
            "city": city,
            "timestamp": datetime.now(),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "wind_gust": data["wind"].get("gust", 0),
            "description": data["weather"][0]["description"],
            "precipitation_1h": data.get("rain", {}).get("1h", 0) + data.get("snow", {}).get("1h", 0),
        }
    except Exception as e:
        print(f"Ошибка получения данных для {city}: {e}")
        return None


# ---------------------------------------------------------------- Этап 2
def load_history(path: str) -> pd.DataFrame:
    """Загрузка суточных данных из архива meteo.ru.

    Формат строки: индекс ВМО; год; месяц; день; средняя температура; осадки.
    """
    df = pd.read_csv(path, sep=";", header=None, skipinitialspace=True,
                     names=["station", "year", "month", "day", "temperature", "precipitation"])
    df = df.dropna(subset=["temperature"])
    station_to_city = {v: k for k, v in CITIES.items()}
    df["city"] = df["station"].map(station_to_city)
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    df["season"] = df["month"].map(get_season)
    return df


# ---------------------------------------------------------------- Этап 3
def seasonal_norms(df: pd.DataFrame, year_from: int, year_to: int) -> pd.DataFrame:
    """Климатические нормы по сезонам за период [year_from; year_to].

    Для температуры: среднее, СКО, минимум, максимум суточных средних.
    Для осадков: средняя сумма осадков за сезон (мм) и доля дней с осадками.
    """
    part = df[(df["year"] >= year_from) & (df["year"] <= year_to)].copy()
    # Декабрь относим к зиме следующего года, чтобы зима не «разрывалась»
    part["season_year"] = part["year"] + (part["month"] == 12).astype(int)

    temp = part.groupby(["city", "season"])["temperature"].agg(
        temperature_mean="mean", temperature_std="std",
        temperature_min="min", temperature_max="max")

    precip_sum = (part.groupby(["city", "season", "season_year"])["precipitation"].sum()
                  .groupby(["city", "season"]).mean().rename("precip_season_mm"))
    wet_share = (part.assign(wet=part["precipitation"] >= 1.0)
                 .groupby(["city", "season"])["wet"].mean().mul(100).rename("wet_days_pct"))

    norms = temp.join(precip_sum).join(wet_share).reset_index()
    order = {"winter": 0, "spring": 1, "summer": 2, "autumn": 3}
    norms["_o"] = norms["season"].map(order)
    return norms.sort_values(["city", "_o"]).drop(columns="_o").round(1).reset_index(drop=True)


def annual_means(df: pd.DataFrame) -> pd.DataFrame:
    """Среднегодовая температура и годовая сумма осадков (только полные годы)."""
    g = df.groupby(["city", "year"])
    res = pd.DataFrame({"temperature": g["temperature"].mean(),
                        "precipitation": g["precipitation"].sum(),
                        "days": g.size()}).reset_index()
    return res[res["days"] >= 360]


def get_norm(norms: pd.DataFrame, city: str, season: str) -> dict:
    row = norms[(norms["city"] == city) & (norms["season"] == season)].iloc[0]
    return row.to_dict()
