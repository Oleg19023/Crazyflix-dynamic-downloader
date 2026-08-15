@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title CrazyFlix Broken Files Checker

:MENU
cls
echo ========================================================
echo      CrazyFlix Checker (Поиск битых файлов ^< 50KB)
echo ========================================================
echo 1. Переместить HTML меньше 50КБ в папку "broken"
echo 2. Сгенерировать ссылки из файлов в "broken" в "retry_urls.txt"
echo 3. Выход
echo ========================================================
set /p choice="Выберите действие (1-3): "

if "%choice%"=="1" goto MOVE_FILES
if "%choice%"=="2" goto GENERATE_URLS
if "%choice%"=="3" exit
goto MENU

:MOVE_FILES
echo.
if not exist "broken" mkdir "broken"
set count=0
for %%F in (*.html) do (
    rem 51200 байт = ровно 50 КБ
    if %%~zF LSS 51200 (
        echo [Перемещен] %%F ^(Размер: %%~zF байт^)
        move "%%F" "broken\" >nul
        set /a count+=1
    )
)
echo.
echo ========================================================
echo Готово! Перемещено "битых" файлов: !count!
echo ========================================================
pause
goto MENU

:GENERATE_URLS
echo.
set out_file=broken\retry_urls.txt
if exist "%out_file%" del "%out_file%"

if not exist "broken\*.html" (
    echo Папка "broken" пуста или не существует! Нет файлов для обработки.
    pause
    goto MENU
)

set count=0
for %%F in (broken\*.html) do (
    rem Генерируем универсальную ссылку на основе названия файла
    echo https://rezka.ag/films/%%~nxF >> "%out_file%"
    set /a count+=1
)

echo.
echo ========================================================
echo Обработано файлов в папке broken: !count!
echo Ссылки успешно созданы и сохранены в файл: %out_file%
echo.
echo ПРИМЕЧАНИЕ: Скрипт подставил универсальную категорию /films/. 
echo Сайт Rezka сам автоматически перенаправит программу 
echo на нужную категорию по ID фильма.
echo ========================================================
pause
goto MENU