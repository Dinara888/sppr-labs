"""Модуль конфигурации: чтение API-ключа и настроек из config.ini."""

import configparser
import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Ошибка конфигурации (нет файла, нет ключа и т.п.)."""


@dataclass
class Settings:
    app_id: str
    api_url: str
    timeout: int
    delay: float
    results_dir: str
    log_file: str


def load_settings(path: str = "config.ini") -> Settings:
    """Читает config.ini и возвращает объект Settings.

    Ключ можно также передать через переменную окружения WOLFRAM_APPID -
    она имеет приоритет над файлом.
    """
    if not os.path.exists(path):
        raise ConfigError(
            f"Файл конфигурации '{path}' не найден. "
            "Скопируйте config.ini.example в config.ini и впишите AppID."
        )

    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")

    app_id = os.environ.get("WOLFRAM_APPID") or parser.get("wolfram", "app_id", fallback="")
    if not app_id or app_id.startswith("ВСТАВЬТЕ"):
        raise ConfigError("В config.ini не указан app_id (AppID Wolfram|Alpha).")

    return Settings(
        app_id=app_id.strip(),
        api_url=parser.get("wolfram", "api_url",
                           fallback="https://api.wolframalpha.com/v2/query"),
        timeout=parser.getint("wolfram", "timeout", fallback=30),
        delay=parser.getfloat("wolfram", "delay", fallback=1.0),
        results_dir=parser.get("output", "results_dir", fallback="results"),
        log_file=parser.get("output", "log_file", fallback="wolfram.log"),
    )
