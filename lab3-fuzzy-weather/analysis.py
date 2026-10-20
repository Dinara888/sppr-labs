"""Этапы 6–7 (часть 1): сравнение с сезонными нормами (аномалии)
и формирование рекомендаций."""


def detect_anomaly(temp: float, norm: dict) -> dict:
    """Сравнение текущей температуры с сезонной нормой по z-оценке.

    z = (T − μ) / σ;  |z| < 1 - норма; 1 ≤ |z| < 2 - умеренная аномалия;
    |z| ≥ 2 - сильная аномалия. Отдельно отмечается выход за исторический
    диапазон [min; max] суточных средних за период нормы.
    """
    mu, sigma = float(norm["temperature_mean"]), float(norm["temperature_std"])
    z = (temp - mu) / sigma if sigma > 0 else 0.0
    side = "теплее" if z > 0 else "холоднее"
    if abs(z) < 1:
        text = "в пределах нормы"
    elif abs(z) < 2:
        text = f"умеренная аномалия: {side} нормы"
    else:
        text = f"сильная аномалия: значительно {side} нормы"
    if temp < norm["temperature_min"] or temp > norm["temperature_max"]:
        text += " (за пределами исторического диапазона)"
    return {"deviation": round(temp - mu, 1), "z": round(z, 2), "text": text}


def make_recommendations(city: str, season: str, w: dict, comfort: float, anomaly: dict) -> list[str]:
    """Рекомендации на основе нечёткой оценки, аномалий и экспертных знаний."""
    temp, hum, wind = w["temperature"], w["humidity"], w["wind_speed"]
    rec = []

    # По итоговому уровню комфорта
    if comfort < 35:
        rec.append("Низкий комфорт: сократите время пребывания на улице")
    elif comfort < 65:
        rec.append("Средний комфорт: одевайтесь по погоде, возможны неудобства")
    else:
        rec.append("Комфортная погода: подходящее время для прогулок")

    # По аномалии
    if abs(anomaly["z"]) >= 2:
        rec.append(f"Погода аномальна для сезона ({anomaly['deviation']:+.1f} °C от нормы): следите за прогнозом")
    elif abs(anomaly["z"]) >= 1:
        rec.append(f"Отклонение от сезонной нормы {anomaly['deviation']:+.1f} °C: учитывайте при выборе одежды")

    # По температуре
    if temp < -20:
        rec.append("Сильный мороз: закрывайте лицо и руки, риск обморожения")
    elif temp < 0:
        rec.append("Мороз: тёплая куртка, шапка, перчатки; возможна гололедица")
    elif temp < 10:
        rec.append("Прохладно: куртка или пальто")
    elif temp > 28:
        rec.append("Жара: пейте больше воды, избегайте солнца с 12 до 16 часов")

    # Специфические рекомендации по городам (экспертные знания)
    if city == "Kazan":
        if season == "winter" and temp < -15 and wind < 2:
            rec.append("Тихая морозная погода: в низинах и «очагах холода» города может быть на 5 °C холоднее")
        if season == "summer" and temp > 30:
            rec.append("Континентальная жара: ищите тень и зелёные зоны")
    elif city == "Moscow":
        if season == "summer" and temp > 23:
            rec.append("Признак волны жары: в историческом центре теплее из-за малого количества зелени")
        if wind > 12:
            rec.append("Риск шквалистого ветра: держитесь подальше от деревьев и рекламных конструкций")
    elif city == "Saint Petersburg":
        if hum > 85 and temp < 5:
            rec.append("Сыро и холодно: непромокаемая одежда обязательна")
        if wind > 10:
            rec.append("Сильный ветер: в прибрежных районах ветер сильнее")

    # Общие рекомендации
    if wind > 15:
        rec.append("Очень сильный ветер: уберите лёгкие вещи с балкона")
    if hum < 30:
        rec.append("Низкая влажность: увлажняйте кожу, пейте воду")
    if hum > 85:
        rec.append("Высокая влажность: возможны осадки")
    return rec
