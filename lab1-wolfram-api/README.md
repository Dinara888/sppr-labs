# Лабораторная работа №1. Интеграция Wolfram|Alpha через API

Программа на Python подключается к Wolfram|Alpha Full Results API, выполняет
15 запросов (10 обязательных и 5 дополнительных), выводит ответы в консоль и
сохраняет результаты в файлы.

## Структура проекта

| Файл | Назначение |
|------|------------|
| `config.ini.example` | шаблон конфигурации (AppID, адрес API, таймауты) |
| `config.py` | модуль конфигурации: чтение `config.ini` |
| `queries.py` | список запросов |
| `client.py` | HTTP GET-запросы к API, повторы при сетевых ошибках |
| `processor.py` | разбор JSON-ответа, извлечение интерпретации и ответа |
| `main.py` | точка входа: последовательное выполнение, логирование, сохранение |

## Как получить AppID

1. Зарегистрироваться на https://account.wolfram.com/wolframid.
2. Открыть https://developer.wolframalpha.com/, войти и нажать **Get an AppID**.
3. Указать название приложения и выбрать тип **Full Results API**.
4. Скопировать AppID.

## Запуск

```bash
pip install -r requirements.txt
cp config.ini.example config.ini      # в Windows: copy config.ini.example config.ini
# открыть config.ini и вписать свой AppID в строку app_id = ...
python main.py                        # все 15 запросов
python main.py --only-required        # только 10 обязательных
```

## Результаты

* `results/raw/NN.json`: полный JSON-ответ на запрос NN;
* `results/extracted.json`: извлечённые данные (категория, запрос, интерпретация, ответ, все pod'ы);
* `results/summary.txt`: удобочитаемый отчёт;
* `wolfram.log`: журнал выполнения.

## Обработка ошибок

* нет `config.ini` или пустой AppID: программа сообщает об этом и завершается;
* неверный AppID (ошибка API): работа прекращается после первого запроса;
* сетевые ошибки и таймауты: до 3 повторов с паузой 2, 4 и 8 секунд;
* запрос, который Wolfram|Alpha не понял, отмечается как неуспешный, и программа переходит к следующему.
