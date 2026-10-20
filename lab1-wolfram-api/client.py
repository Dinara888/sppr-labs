"""Модуль клиента: отправка HTTP GET-запросов к Wolfram|Alpha Full Results API."""

import logging
import time

import requests

log = logging.getLogger("wolfram.client")


class WolframAPIError(Exception):
    """Ошибка на стороне API (неверный AppID, запрос не понят и т.п.)."""


class WolframClient:
    def __init__(self, app_id: str, api_url: str, timeout: int = 30, retries: int = 3):
        self.app_id = app_id
        self.api_url = api_url
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def query(self, text: str) -> dict:
        """Выполняет запрос и возвращает разобранный JSON (поле queryresult).

        Сетевые ошибки повторяются до self.retries раз с паузой 2, 4, 8 секунд.
        """
        params = {
            "appid": self.app_id,
            "input": text,
            "output": "json",   # просим ответ в формате JSON
            "format": "plaintext",
            "units": "metric",
        }
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                log.info("Запрос (попытка %d): %s", attempt, text)
                resp = self.session.get(self.api_url, params=params, timeout=self.timeout)
                if resp.status_code in (401, 403):
                    raise WolframAPIError(f"Доступ запрещён (HTTP {resp.status_code}) - проверьте AppID")
                resp.raise_for_status()
                data = resp.json()
                result = data.get("queryresult", {})
                if result.get("error"):
                    err = result["error"]
                    msg = err.get("msg") if isinstance(err, dict) else str(err)
                    raise WolframAPIError(f"Ошибка API: {msg}")
                return result
            except WolframAPIError:
                raise                       # ошибки API повторять бессмысленно
            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
                log.warning("Сетевая ошибка: %s", e)
            except requests.HTTPError as e:
                last_error = e
                log.warning("HTTP-ошибка: %s", e)
            except ValueError as e:         # ответ не является JSON
                last_error = e
                log.warning("Некорректный JSON в ответе: %s", e)
            time.sleep(2 ** attempt)
        raise ConnectionError(f"Не удалось выполнить запрос '{text}': {last_error}")
