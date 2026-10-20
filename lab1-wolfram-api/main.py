"""Лабораторная работа №1. Интеграция экспертной системы Wolfram|Alpha через API.

Запуск:  python main.py            (все 15 запросов)
         python main.py --only-required   (только 10 обязательных)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

from client import WolframAPIError, WolframClient
from config import ConfigError, load_settings
from processor import extract, format_readable
from queries import ALL_QUERIES, REQUIRED_QUERIES


def setup_logging(log_file: str) -> None:
    """Логирование одновременно в файл и в консоль."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"),
                  logging.StreamHandler(sys.stderr)],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Запросы к Wolfram|Alpha API")
    ap.add_argument("--config", default="config.ini")
    ap.add_argument("--only-required", action="store_true", help="только 10 обязательных запросов")
    args = ap.parse_args()

    try:
        settings = load_settings(args.config)
    except ConfigError as e:
        print(f"Ошибка конфигурации: {e}")
        return 1

    setup_logging(settings.log_file)
    log = logging.getLogger("wolfram.main")

    raw_dir = os.path.join(settings.results_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    client = WolframClient(settings.app_id, settings.api_url, settings.timeout)
    queries = REQUIRED_QUERIES if args.only_required else ALL_QUERIES
    log.info("Начало работы, запросов: %d", len(queries))

    results = []
    for i, (category, text) in enumerate(queries, start=1):
        try:
            raw = client.query(text)
            # Полный ответ сохраняем в отдельный файл
            with open(os.path.join(raw_dir, f"{i:02d}.json"), "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)
            item = extract(text, category, raw)
            log.info("Готово: %s -> success=%s", text, item["success"])
        except (WolframAPIError, ConnectionError) as e:
            log.error("Запрос '%s' не выполнен: %s", text, e)
            item = {"category": category, "query": text, "success": False,
                    "interpretation": "", "answer": "", "pods": [], "error": str(e)}
            if isinstance(e, WolframAPIError) and "appid" in str(e).lower():
                print(format_readable(item, i))
                return 2                    # неверный ключ - продолжать нет смысла
        results.append(item)
        print(format_readable(item, i))
        time.sleep(settings.delay)

    # Извлечённые данные: JSON и удобочитаемый текст
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(settings.results_dir, "extracted.json"), "w", encoding="utf-8") as f:
        json.dump({"timestamp": stamp, "results": results}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(settings.results_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"Результаты запросов к Wolfram|Alpha ({stamp})\n")
        for i, item in enumerate(results, start=1):
            f.write(format_readable(item, i) + "\n")

    ok = sum(1 for r in results if r["success"])
    print("=" * 70)
    print(f"Успешно: {ok} из {len(results)}. Результаты сохранены в папку '{settings.results_dir}'.")
    log.info("Завершено: успешно %d из %d", ok, len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
