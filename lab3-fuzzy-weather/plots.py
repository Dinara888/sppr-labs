"""Этап 7: визуализация - функции принадлежности, сезонные профили,
тренды, таблица результатов."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from weather_data import CITY_RU, SEASON_RU

COLORS = {"Kazan": "#2a6fdb", "Moscow": "#d1495b", "Saint Petersburg": "#2e9e6b"}
SEASONS = ["winter", "spring", "summer", "autumn"]


def plot_memberships(fs, path, current_value=None):
    """Функции принадлежности всех переменных одной нечёткой системы."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, var, title in zip(axes.flat,
                              [fs.temperature, fs.humidity, fs.wind, fs.comfort],
                              ["Температура, °C", "Влажность, %", "Скорость ветра, м/с", "Комфорт, баллы"]):
        for term, mf in var.terms.items():
            ax.plot(var.universe, mf.mf, linewidth=2, label=term)
        ax.set_title(title)
        ax.set_ylim(-0.02, 1.05)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    if current_value is not None:
        axes[0, 0].axvline(current_value, color="black", linestyle="--", label="текущее")
        axes[0, 0].legend(fontsize=8)
    fig.suptitle(f"Функции принадлежности: {CITY_RU[fs.city]}, {SEASON_RU[fs.season]}", fontsize=14)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_seasonal_profiles(norms, path):
    """Средняя температура (±σ) и сезонная сумма осадков по городам."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(SEASONS))
    width = 0.26
    for i, city in enumerate(COLORS):
        d = norms[norms["city"] == city].set_index("season").loc[SEASONS]
        ax1.bar(x + (i - 1) * width, d["temperature_mean"], width, yerr=d["temperature_std"],
                capsize=3, color=COLORS[city], label=CITY_RU[city])
        ax2.bar(x + (i - 1) * width, d["precip_season_mm"], width, color=COLORS[city], label=CITY_RU[city])
    for ax, title, yl in [(ax1, "Средняя температура по сезонам (±σ)", "°C"),
                          (ax2, "Средняя сумма осадков за сезон", "мм")]:
        ax.set_xticks(x, [SEASON_RU[s] for s in SEASONS])
        ax.set_title(title)
        ax.set_ylabel(yl)
        ax.axhline(0, color="gray", linewidth=0.8)
        ax.grid(axis="y", alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_trends(annual, path):
    """Многолетний тренд среднегодовой температуры (скользящее среднее 10 лет)."""
    fig, ax = plt.subplots(figsize=(13, 5))
    for city, color in COLORS.items():
        d = annual[annual["city"] == city].sort_values("year")
        ax.plot(d["year"], d["temperature"], color=color, alpha=0.25, linewidth=1)
        ax.plot(d["year"], d["temperature"].rolling(10, center=True).mean(), color=color,
                linewidth=2.2, label=f"{CITY_RU[city]} (скользящее среднее 10 лет)")
        k, b = np.polyfit(d["year"], d["temperature"], 1)
        print(f"  Линейный тренд {CITY_RU[city]}: {k * 100:+.2f} °C за 100 лет "
              f"({int(d['year'].min())}–{int(d['year'].max())})")
    ax.set_title("Среднегодовая температура воздуха (архив meteo.ru)")
    ax.set_xlabel("Год")
    ax.set_ylabel("°C")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_current_vs_norm(rows, norms, season, path):
    """Текущая температура на фоне сезонной нормы и уровень комфорта."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    cities = [r["city"] for r in rows]
    x = np.arange(len(cities))
    mu = [norms[(norms.city == c) & (norms.season == season)]["temperature_mean"].iloc[0] for c in cities]
    sd = [norms[(norms.city == c) & (norms.season == season)]["temperature_std"].iloc[0] for c in cities]
    ax1.bar(x, mu, 0.5, yerr=sd, capsize=6, color="#cccccc", label="норма (μ ± σ)")
    ax1.scatter(x, [r["temperature"] for r in rows], s=120, zorder=3,
                color=[COLORS[c] for c in cities], label="текущая")
    ax1.set_xticks(x, [CITY_RU[c] for c in cities])
    ax1.set_title(f"Текущая температура и норма ({SEASON_RU[season]})")
    ax1.set_ylabel("°C")
    ax1.grid(axis="y", alpha=0.3)
    ax1.legend()
    ax2.bar(x, [r["comfort"] for r in rows], 0.5, color=[COLORS[c] for c in cities])
    for xi, r in zip(x, rows):
        ax2.text(xi, r["comfort"] + 2, f"{r['comfort']:.1f}", ha="center")
    ax2.set_xticks(x, [CITY_RU[c] for c in cities])
    ax2.set_ylim(0, 100)
    ax2.set_title("Уровень комфорта (нечёткий вывод Мамдани)")
    ax2.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def save_table_png(df, path, title):
    """Таблица pandas в виде картинки (для отчёта)."""
    fig, ax = plt.subplots(figsize=(min(2 + 1.6 * len(df.columns), 20), 0.8 + 0.4 * len(df)))
    ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1, 1.4)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)
