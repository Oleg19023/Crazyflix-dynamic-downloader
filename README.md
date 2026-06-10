# 🤖 CrazyFlix Dynamic Downloader & Ecosystem

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Playwright-Chromium-brightgreen" alt="Playwright">
  <img src="https://img.shields.io/badge/Status-Stealth_Mode-red" alt="Stealth Mode">
  <img src="https://img.shields.io/badge/Tampermonkey-DB_Checker-purple" alt="Tampermonkey Support">
  <img src="https://img.shields.io/badge/Proxy-Supported-orange" alt="Proxy Support">
</p>

## 📜 Официальное Уведомление об Авторском Праве

### [RU] Информация о Программном Обеспечении

| Параметр | Значение |
| :--- | :--- |
| **ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ** | **CrazyFlix Downloader & Parser** |
| **ВЕРСИЯ** | **5.6.2** |
| **АВТОРСКИЕ ПРАВА** | **(C) 2026 CrazyFire. ВСЕ ПРАВА ЗАЩИЩЕНЫ.** |
| **Разработано** | Под эгидой CrazyFire |
| **Владелец/Разработчик** | W1zarD |
| **Тип системы** | Автоматизированный сбор данных (Data Mining Automation) |

### [ENG] Software Copyright Notice

| Parameter | Value |
| :--- | :--- |
| **SOFTWARE** | **CrazyFlix Downloader & Parser** |
| **VERSION** | **5.6.2** |
| **COPYRIGHT** | **(C) 2026 CrazyFire. ALL RIGHTS RESERVED.** |

---

## 🔄 Рабочий цикл CrazyFlix (Workflow)

Процесс добавления контента теперь полностью автоматизирован и разбит на 4 ключевых этапа:

### Этап 1: Селекция (Tampermonkey)
1. Откройте Rezka (или зеркало). Скрипт **CrazyFlix Rezka DB Checker** автоматически подсветит фильмы:
   - **Зеленая рамка**: Уже есть в базе CrazyFlix.
   - **Красная рамка**: Новинка, которой нет в системе.
2. Нажмите кнопку **«💾 Сохранить»** на красных карточках.
3. В меню **CrazyFlix Manager** (справа внизу) нажмите **«Выгрузить в .txt»** для получения списка ссылок.

### Этап 2: Обработка (Python Program)
1. Поместите список в папку с программой.
2. Запустите `dynamic_html_downloader.py`.
3. Программа имитирует действия человека: заходит на страницу, кликает «Смотреть трейлер» и извлекает код YouTube-плеера.
4. Результат: Готовые HTML-файлы в папке `downloaded_html`.

### Этап 3: Синхронизация (CrazyFlix Site)
1. Используйте функцию **Import** в админ-панели вашего сайта, выбрав скачанные HTML-файлы.
2. Сайт обновит внутреннюю базу и предложит скачать свежий файл **crazyflix-api.json**.

### Этап 4: Публикация (GitHub & CDN)
1. Обновите файл `crazyflix-api.json` в вашем репозитории на GitHub.
2. Скрипт Tampermonkey и программа моментально «увидят» изменения через jsDelivr, и добавленные фильмы станут **Зелеными** при следующем сканировании.

---

## 🛠️ Установка и компоненты

### 1. Python Downloader
- **Зависимости**: `playwright`, `colorama`, `tqdm`, `fake-useragent`, `aiohttp`.
- **Команда установки**:
  ```bash
  pip install -r requirements.txt
  playwright install chromium
  ```

### 2. Tampermonkey Script (DB Checker)
Установите расширение Tampermonkey и добавьте скрипт `crazyflix-checker.user.js`.
- **Функции**: Поиск дубликатов в реальном времени, экспорт ссылок, работа на зеркалах (hdrezka, rezka.ag).

---

## 🚀 Новые функции v5.0 – v5.6.2

- **Speedrun Parser (36 Links)**: Парсер больше не ждет полной загрузки страницы. Как только в DOM найдено 36 ссылок — он мгновенно переходит к следующей странице.
- **Smart Reload**: Если найдено меньше 36 ссылок, скрипт автоматически перезагружает страницу для дозагрузки элементов.
- **Trailer Retry System**: 3 попытки клика по кнопке трейлера с ожиданием появления кода плеера в коде (DOM).
- **Dual List Loading**: Программа автоматически считывает ссылки из `urls_to_download.txt` и `parser_urls.txt`.
- **Infinite Retry Mode**: Режим «До победного» в настройках позволяет программе бесконечно гонять неудачные ссылки до их полной загрузки.
- **Modern Fingerprinting**: Использование заголовков `Sec-Ch-Ua` и подмена `Referer` для обхода 403 ошибки на защищенных страницах.

---

## 📜 История последних обновлений

| Версия | Ключевые изменения |
| :--- | :--- |
| **v4.6 – v4.9** | **Logic Overhaul.** Внедрен пошаговый вывод логов на английском (INIT, NETWORK, SEARCH). Улучшена эмуляция кликов через `MouseEvent`. |
| **v5.0 – v5.3** | **Settings Update.** Добавлен переключатель `Use Proxy` и режим `Infinite Retry`. Встроена функция очистки списков через меню. |
| **v5.4 – v5.5** | **Parser Speedup.** Добавлен выбор диапазона страниц (например, со 100 по 200). Внедрен файл `parser_urls.txt` и мгновенный сбор 36 ссылок. |
| **v5.6.2** | **Full Stealth.** Добавлена имитация современных Chrome-заголовков, подмена Referer и автоматическая проверка статус-кодов (403/429). |

---

### 🛠️ Технические приемы Stealth Engine
- **JS Injection**: Удаление флагов автоматизации (`webdriver: undefined`).
- **Human Hover**: Обязательное наведение мыши на элементы перед взаимодействием.
- **Random Cooldown**: Задержки между загрузками страниц для размытия паттернов бота.
- **DOM Stability Check**: Ожидание именно кода плеера (`iframe`), а не просто визуального окна.
