# 🤖 CrazyFlix Dynamic Downloader & Ecosystem

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/Playwright-Chromium-brightgreen" alt="Playwright">
  <img src="https://img.shields.io/badge/Status-Stealth_Mode-red" alt="Stealth Mode">
  <img src="https://img.shields.io/badge/Tampermonkey-DB_Checker-purple" alt="Tampermonkey Support">
  <img src="https://img.shields.io/badge/API-Verification_Web-yellow" alt="Web Verification">
</p>

## 📖 Documentation / Документация

> [!IMPORTANT]
> **Подробная пошаговая инструкция** по эксплуатации всей экосистемы CrazyFlix со скриншотами и описанием каждого этапа доступна в файле:
> ### 📂 [**CRAZYFLIX_MANUAL.PDF**](./crazyflix_manual.pdf)

---

## 📜 Официальное Уведомление

| Параметр | Значение |
| :--- | :--- |
| **ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ** | **CrazyFlix Downloader & Parser** |
| **ВЕРСИЯ** | **5.6.2** |
| **АВТОРСКИЕ ПРАВА** | **(C) 2026 CrazyFire. ВСЕ ПРАВА ЗАЩИЩЕНЫ.** |
| **Разработчик** | W1zarD |

---

## 🔄 Рабочий цикл CrazyFlix (Workflow)

Процесс добавления контента теперь полностью автоматизирован и включает 5 ключевых этапов:

1.  **Селекция (Tampermonkey)**: [👉 УСТАНОВИТЬ СКРИПТ](https://raw.githubusercontent.com/Oleg19023/Crazyflix-dynamic-downloader/main/crazyflix-checker.user.js). Скрипт подсвечивает новинки на Rezka (**Красная рамка** — нет в базе, **Зеленая** — есть).
2.  **Обработка (Python Downloader)**: Программа имитирует действия человека, извлекая код плеера и сохраняя HTML.
3.  **Импорт (CrazyFlix CMS)**: Загрузка HTML-файлов в админ-панель вашего сайта.
4.  **Верификация (Web DB Checker)**: Проверка сгенерированного JSON-файла на ошибки через [CrazyFlix DB Checker](https://crazyflix-db-checker-218958038563.us-west1.run.app).
5.  **Публикация (GitHub)**: Обновление `crazyflix-api.json` в репозитории для синхронизации всей сети.

---

## 🛠️ Основные компоненты

*   **CrazyFlix Rezka DB Checker**: JS-скрипт для браузера. Сравнение базы в реальном времени.
*   **CrazyFlix Downloader HTML**: Python-утилита. Работа с динамическим контентом, обход 403 ошибок, работа через прокси.
*   **CrazyFlix DB Checker (Web)**: Веб-интерфейс для глубокого анализа структуры API и поиска дубликатов.

---

## 🚀 Ключевые фишки v5.6.2

*   **Speedrun Parser**: Моментальный переход к следующей странице при нахождении 36 ссылок.
*   **Smart Reload**: Авто-перезагрузка страниц при неполной подгрузке контента.
*   **Full Stealth Engine**: Подмена Referer, использование современных заголовков `Sec-Ch-Ua` и эмуляция `MouseEvent`.
*   **Infinite Retry**: Режим "До победного" — программа будет циклично обрабатывать ошибки до полного успеха.
*   **Proxy Management**: Быстрое переключение между Local IP и списком прокси прямо в настройках.

---

### 🛠️ Установка
```bash
pip install -r requirements.txt
playwright install chromium
python dynamic_html_downloader.py
```

*Разработано для внутренней экосистемы CrazyFlix. Владелец: W1zarD.*
