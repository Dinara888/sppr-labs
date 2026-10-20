"""Лабораторная работа №3. Экспертная система на основе нечёткой логики
для анализа погодных условий городов России (Казань, Москва, Санкт-Петербург).

Запуск:  python main.py               - полный анализ (нужен ключ OpenWeatherMap)
         python main.py --history-only - только исторические данные и нормы
"""

import argparse
import configparser
import os
import sys
from datetime import datetime

import pandas as pd

import plots
from analysis import detect_anomaly, make_recommendations
from fuzzy_system import SeasonalFuzzySystem, comfort_label
from linguistic import numeric_to_linguistic
from weather_data import (CITIES, CITY_RU, SEASON_RU, annual_means, get_current_weather,
                          get_norm, get_season, load_history, seasonal_norms)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.ini")
    ap.add_argument("--history-only", action="store_true")
    args = ap.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.config if os.path.exists(args.config) else "config.ini.example", encoding="utf-8")
    out = cfg.get("output", "results_dir", fallback="results")
    os.makedirs(out, exist_ok=True)
    y1, y2 = cfg.getint("history", "year_from"), cfg.getint("history", "year_to")

    # ---- Этап 2. Исторические данные
    print("[1] Загрузка исторических данных (архив meteo.ru)...")
    hist = load_history(cfg.get("history", "data_file"))
    for city in CITIES:
        d = hist[hist.city == city]
        print(f"  ✓ {city}: {len(d)} записей ({d.date.min():%d.%m.%Y} – {d.date.max():%d.%m.%Y})")

    # ---- Этап 3. Сезонные нормы
    print(f"\n[2] Расчёт сезонных норм за {y1}–{y2} гг...")
    norms = seasonal_norms(hist, y1, y2)
    print(norms.to_string(index=False))
    norms.to_csv(os.path.join(out, "seasonal_norms.csv"), index=False, encoding="utf-8-sig")
    plots.save_table_png(norms.assign(city=norms.city.map(CITY_RU), season=norms.season.map(SEASON_RU)),
                         os.path.join(out, "table_norms.png"), f"Сезонные нормы {y1}–{y2}")
    plots.plot_seasonal_profiles(norms, os.path.join(out, "seasonal_profiles.png"))
    print("\n  Тренды среднегодовой температуры:")
    plots.plot_trends(annual_means(hist), os.path.join(out, "trends.png"))

    season = get_season(datetime.now().month)
    if args.history_only:
        for city in CITIES:
            fs = SeasonalFuzzySystem(city, season, get_norm(norms, city, season))
            plots.plot_memberships(fs, os.path.join(out, f"mf_{city.replace(' ', '_')}.png"))
        print(f"\nГотово (только история). Графики в папке '{out}'.")
        return 0

    # ---- Этап 1. Текущие данные
    api_key = cfg.get("openweathermap", "api_key", fallback="")
    if not api_key or api_key.startswith("ВСТАВЬТЕ"):
        print("\nНе указан API-ключ OpenWeatherMap в config.ini - текущий анализ невозможен.")
        return 1
    print("\n[3] Получение текущих данных (OpenWeatherMap)...")
    print(f"Текущий сезон: {season} ({SEASON_RU[season]})")
    current = {}
    for city in CITIES:
        w = get_current_weather(city, api_key)
        if w:
            current[city] = w
            print(f"  {city}: {w['temperature']:.2f}°C, {w['description']}, влажность {w['humidity']}%, "
                  f"ветер {w['wind_speed']} м/с")
    if not current:
        print("Не удалось получить текущие данные ни для одного города.")
        return 1

    # ---- Этапы 4–6. Лингвистические переменные, нечёткий вывод, аномалии, рекомендации
    rows = []
    for city, w in current.items():
        norm = get_norm(norms, city, season)
        fs = SeasonalFuzzySystem(city, season, norm)
        comfort = fs.evaluate(w["temperature"], w["humidity"], w["wind_speed"])
        anomaly = detect_anomaly(w["temperature"], norm)
        rec = make_recommendations(city, season, w, comfort, anomaly)
        ling = {v: numeric_to_linguistic(w[k], v, city, season)
                for v, k in [("temperature", "temperature"), ("humidity", "humidity"), ("wind", "wind_speed")]}

        print(f"\n--- Анализ для {city} ({CITY_RU[city]}) ---")
        print(f"Температура: {w['temperature']:.1f}°C, Влажность: {w['humidity']}%, Ветер: {w['wind_speed']} м/с")
        print(f"Норма сезона: {norm['temperature_mean']}°C ± {norm['temperature_std']}°C")
        print(f"Лингвистически: температура «{ling['temperature']}», влажность «{ling['humidity']}», "
              f"ветер «{ling['wind']}»")
        print(f"Фаззификация температуры: {fs.memberships(w['temperature'])}")
        print(f"Аномалия: {anomaly['text']} (отклонение {anomaly['deviation']:+.1f}°C, z = {anomaly['z']})")
        print(f"Уровень комфорта: {comfort:.1f} / 100 ({comfort_label(comfort)})")
        print("Рекомендации:")
        for r in rec:
            print(f"  • {r}")

        plots.plot_memberships(fs, os.path.join(out, f"mf_{city.replace(' ', '_')}.png"), w["temperature"])
        rows.append({"city": city, "temperature": w["temperature"], "humidity": w["humidity"],
                     "wind": w["wind_speed"], "description": w["description"],
                     "norm": f"{norm['temperature_mean']} ± {norm['temperature_std']}",
                     "deviation": anomaly["deviation"], "anomaly": anomaly["text"],
                     "temp_term": ling["temperature"], "comfort": round(comfort, 1),
                     "comfort_label": comfort_label(comfort), "recommendations": "; ".join(rec)})

    # ---- Этап 7. Итоговая таблица и графики
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(out, "results.csv"), index=False, encoding="utf-8-sig")
    short = res[["city", "temperature", "humidity", "wind", "norm", "deviation", "temp_term", "comfort",
                 "comfort_label"]].copy()
    short["city"] = short["city"].map(CITY_RU)
    short.columns = ["Город", "T, °C", "Влажн., %", "Ветер, м/с", "Норма, °C", "Откл., °C",
                     "Терм T", "Комфорт", "Оценка"]
    print("\n[4] Итоговая таблица:")
    print(short.to_string(index=False))
    plots.save_table_png(short, os.path.join(out, "table_results.png"),
                         f"Результаты анализа на {datetime.now():%d.%m.%Y %H:%M}")
    plots.plot_current_vs_norm(rows, norms, season, os.path.join(out, "current_vs_norm.png"))
    best = res.loc[res.comfort.idxmax()]
    print(f"\nНаиболее комфортная погода сейчас: {CITY_RU[best.city]} ({best.comfort})")
    print(f"Все результаты сохранены в папку '{out}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
