"""Этап 5: система нечёткого вывода Мамдани (scikit-fuzzy) с учётом сезона.

Входы (антецеденты): температура, влажность, скорость ветра.
Выход (консеквент): уровень комфорта 0..100.
Функции принадлежности температуры зависят от сезона, а терм «норма»
строится по климатической норме города: [μ − σ; μ; μ + σ].
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

T_MIN, T_MAX = -30, 40


class SeasonalFuzzySystem:
    def __init__(self, city: str, season: str, norm: dict):
        self.city = city
        self.season = season
        mean_temp = float(norm["temperature_mean"])
        std_temp = float(norm["temperature_std"])

        # Антецеденты
        self.temperature = ctrl.Antecedent(np.arange(T_MIN, T_MAX + 1, 1), "temperature")
        self.humidity = ctrl.Antecedent(np.arange(0, 101, 1), "humidity")
        self.wind = ctrl.Antecedent(np.arange(0, 31, 1), "wind")
        # Консеквент; дефаззификация - метод центра тяжести
        self.comfort = ctrl.Consequent(np.arange(0, 101, 1), "comfort", defuzzify_method="centroid")

        u = self.temperature.universe
        normal = [mean_temp - std_temp, mean_temp, mean_temp + std_temp]

        # Функции принадлежности температуры (адаптивные к сезону)
        if season == "winter":
            self.temp_terms = ["extremely_cold", "cold", "normal", "warm_for_winter"]
            self.temperature["extremely_cold"] = fuzz.trapmf(u, [T_MIN, T_MIN, -25, -20])
            self.temperature["cold"] = fuzz.trimf(u, [-22, -15, -8])
            self.temperature["normal"] = fuzz.trimf(u, normal)
            self.temperature["warm_for_winter"] = fuzz.trapmf(u, [-5, 0, T_MAX, T_MAX])
        elif season == "summer":
            self.temp_terms = ["cool", "normal", "warm", "hot"]
            self.temperature["cool"] = fuzz.trapmf(u, [T_MIN, T_MIN, 12, 18])
            self.temperature["normal"] = fuzz.trimf(u, normal)
            self.temperature["warm"] = fuzz.trimf(u, [21, 25, 29])
            self.temperature["hot"] = fuzz.trapmf(u, [27, 32, T_MAX, T_MAX])
        else:  # весна и осень - переходные сезоны
            self.temp_terms = ["cold", "cool", "normal", "warm"]
            self.temperature["cold"] = fuzz.trapmf(u, [T_MIN, T_MIN, -8, 0])
            self.temperature["cool"] = fuzz.trimf(u, [-4, 2, 8])
            self.temperature["normal"] = fuzz.trimf(u, normal)
            self.temperature["warm"] = fuzz.trapmf(u, [12, 18, T_MAX, T_MAX])

        # Влажность (общая для всех городов)
        h = self.humidity.universe
        self.humidity["low"] = fuzz.trapmf(h, [0, 0, 25, 45])
        self.humidity["normal"] = fuzz.trimf(h, [35, 57, 80])
        self.humidity["high"] = fuzz.trapmf(h, [70, 88, 100, 100])

        # Скорость ветра, м/с
        w = self.wind.universe
        self.wind["calm"] = fuzz.trapmf(w, [0, 0, 2, 5])
        self.wind["moderate"] = fuzz.trimf(w, [3, 7, 11])
        self.wind["windy"] = fuzz.trapmf(w, [9, 14, 30, 30])

        # Уровень комфорта
        c = self.comfort.universe
        self.comfort["bad"] = fuzz.trapmf(c, [0, 0, 20, 40])
        self.comfort["satisfactory"] = fuzz.trimf(c, [30, 50, 70])
        self.comfort["good"] = fuzz.trapmf(c, [60, 80, 100, 100])

        self.rules = self._build_rules()
        self.system = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.system)

    # ------------------------------------------------------------ правила
    def _build_rules(self):
        T, H, W, C = self.temperature, self.humidity, self.wind, self.comfort
        rules = []

        # Базовые правила по температуре (покрывают весь универсум)
        if self.season == "winter":
            rules += [
                ctrl.Rule(T["extremely_cold"], C["bad"]),
                ctrl.Rule(T["cold"] & W["calm"], C["satisfactory"]),
                ctrl.Rule(T["cold"] & (W["moderate"] | W["windy"]), C["bad"]),
                ctrl.Rule(T["normal"] & W["calm"], C["good"]),
                ctrl.Rule(T["normal"] & W["moderate"], C["satisfactory"]),
                ctrl.Rule(T["warm_for_winter"] & H["high"], C["satisfactory"]),  # слякоть
                ctrl.Rule(T["warm_for_winter"] & ~H["high"], C["good"]),
            ]
        elif self.season == "summer":
            rules += [
                ctrl.Rule(T["cool"], C["satisfactory"]),
                ctrl.Rule(T["normal"] & ~H["high"], C["good"]),
                ctrl.Rule(T["normal"] & H["high"], C["satisfactory"]),
                ctrl.Rule(T["warm"] & H["normal"], C["good"]),
                ctrl.Rule(T["warm"] & H["high"], C["satisfactory"]),
                ctrl.Rule(T["warm"] & H["low"], C["satisfactory"]),
                ctrl.Rule(T["hot"], C["bad"]),
            ]
        else:
            rules += [
                ctrl.Rule(T["cold"], C["bad"]),
                ctrl.Rule(T["cool"] & W["calm"], C["satisfactory"]),
                ctrl.Rule(T["cool"] & ~W["calm"], C["bad"]),
                ctrl.Rule(T["normal"] & H["normal"], C["good"]),
                ctrl.Rule(T["normal"] & ~H["normal"], C["satisfactory"]),
                ctrl.Rule(T["warm"], C["good"]),
            ]

        # Общие правила для ветра
        rules += [
            ctrl.Rule(W["windy"], C["bad"]),
            ctrl.Rule(W["calm"] & H["normal"], C["good"]),
        ]

        # Специфические правила для Санкт-Петербурга: сырость + ветер
        if self.city == "Saint Petersburg":
            rules.append(ctrl.Rule(H["high"] & W["windy"], C["bad"]))
            rules.append(ctrl.Rule(H["high"] & W["moderate"], C["satisfactory"]))
        # Москва: волна жары при высокой влажности (летние «тропические ливни»)
        if self.city == "Moscow" and self.season == "summer":
            rules.append(ctrl.Rule(T["hot"] & H["high"], C["bad"]))
        # Казань: в морозную тихую погоду образуются «очаги холода» (до −5 °C)
        if self.city == "Kazan" and self.season == "winter":
            rules.append(ctrl.Rule(T["cold"] & W["calm"] & H["high"], C["bad"]))
        return rules

    # ------------------------------------------------------------ вывод
    def evaluate(self, temperature: float, humidity: float, wind: float) -> float:
        """Нечёткий вывод: возвращает чёткое значение комфорта 0..100."""
        self.simulation.input["temperature"] = float(np.clip(temperature, T_MIN, T_MAX))
        self.simulation.input["humidity"] = float(np.clip(humidity, 0, 100))
        self.simulation.input["wind"] = float(np.clip(wind, 0, 30))
        self.simulation.compute()
        return float(self.simulation.output["comfort"])

    def memberships(self, temperature: float) -> dict:
        """Степени принадлежности температуры к каждому терму (фаззификация)."""
        t = float(np.clip(temperature, T_MIN, T_MAX))
        return {term: round(float(fuzz.interp_membership(self.temperature.universe,
                                                         self.temperature[term].mf, t)), 2)
                for term in self.temp_terms}


def comfort_label(score: float) -> str:
    if score < 35:
        return "плохо"
    if score < 65:
        return "удовлетворительно"
    return "хорошо"
