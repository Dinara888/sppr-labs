@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Установка библиотеки requests...
python -m pip install -r requirements.txt
echo.
echo Запуск программы...
python main.py
echo.
echo Готово. Результаты в папке results.
pause
