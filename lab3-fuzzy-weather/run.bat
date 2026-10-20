@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Установка библиотек...
python -m pip install -r requirements.txt
echo.
echo Запуск программы...
python main.py
if errorlevel 1 (echo. & echo ОШИБКА: пришлите скриншот этого окна) else (echo. & echo Готово. Результаты в папке results.)
pause
