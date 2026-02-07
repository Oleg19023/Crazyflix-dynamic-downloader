"""
------------------------------------------------------------------------------
ПРОГРАММНОЕ ОБЕСПЕЧЕНИЕ: CrazyFlix Downloader HTML
ВЕРСИЯ: 1.7

АВТОРСКИЕ ПРАВА (C) 2026 CrazyFire. ВСЕ ПРАВА ЗАЩИЩЕНЫ.

Разработано и поддерживается под эгидой CrazyFire.
Ведущий разработчик и владелец: W1zarD

Данный программный код является интеллектуальной собственностью CrazyFire
и предназначен исключительно для внутренних нужд экосистемы CrazyFlix.
Любое несанкционированное копирование, модификация, распространение
или использование алгоритмов без письменного согласия W1zarD строго запрещено.

Система автоматизированного сбора данных (Data Mining Automation).
------------------------------------------------------------------------------
"""

import asyncio
import re
import os
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm

init(autoreset=True)

DOWNLOAD_DIR = "downloaded_html"
URL_FILE = "urls_to_download.txt"
MAX_CONCURRENT_TASKS = 2

# --- УТИЛИТАРНЫЕ ФУНКЦИИ ---
def clean_filename(url: str) -> str:
    path = urlparse(url).path
    filename_base = path.split('/')[-1]
    
    if not filename_base:
        filename_base = path.split('/')[-2] if len(path.split('/')) > 1 else 'index'
    
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', filename_base)
    
    if not safe_name.lower().endswith('.html'):
        safe_name += '.html'
        
    return safe_name

def load_urls_from_file() -> list:
    urls = []
    try:
        with open(URL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    urls.append(stripped_line)
    except FileNotFoundError:
        print(f"{Fore.RED}[ERROR] Файл '{URL_FILE}' не найден. Пожалуйста, создайте его.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Произошла ошибка при чтении файла '{URL_FILE}': {e}{Style.RESET_ALL}")
        
    return urls

# --- ОСНОВНАЯ ЛОГИКА ЗАГРУЗКИ ---
async def download_html(browser, url: str, semaphore: asyncio.Semaphore):
    async with semaphore:
        tqdm.write(f"\n{Fore.BLUE}[INFO]{Style.RESET_ALL} Начинаю обработку: {url}")
        
        file_name = os.path.join(DOWNLOAD_DIR, clean_filename(url))
        
        context = await browser.new_context(
            locale='ru-RU',
            timezone_id='Europe/Moscow' 
        )

        try:
            page = await context.new_page()
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            tqdm.write(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} [{url}] Основная страница загружена.")
            
            trailer_button_selector = 'a.b-sidelinks__link.show-trailer'
            
            try:
                await page.wait_for_selector(trailer_button_selector, state='visible', timeout=5000)
                tqdm.write(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} [{url}] Найдена кнопка 'Смотреть трейлер'. Выполняю клик...")
                
                await page.click(trailer_button_selector)
                
                await asyncio.sleep(2)
                tqdm.write(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} [{url}] Блок трейлера должен был загрузиться в HTML.")

            except TimeoutError:
                tqdm.write(f"[{url}] {Fore.YELLOW}[WARNING]{Style.RESET_ALL} Кнопка 'Смотреть трейлер' не найдена на странице.")
            except Exception:
                pass

            html_content = await page.content()
            
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            tqdm.write(f"{Fore.GREEN}[Done]{Style.RESET_ALL} [{url}] HTML-код сохранен в файл: {os.path.abspath(file_name)}")

        except TimeoutError:
            tqdm.write(f"{Fore.RED}[Failed]{Style.RESET_ALL} [{url}] Не удалось загрузить страницу за отведенное время (30 секунд).")
        except Exception as e:
            tqdm.write(f"{Fore.RED}[Failed]{Style.RESET_ALL} [{url}] Произошла непредвиденная ошибка: {e}")
        finally:
            if 'page' in locals():
                await page.close()
            await context.close()

# --- ГЛАВНАЯ ФУНКЦИЯ ---

async def main():
    print(f"\n{Fore.CYAN}--- CrazyFlix Downloader HTML by W1zarD v1.7 ---{Style.RESET_ALL}")

    urls_to_download = load_urls_from_file()

    if not urls_to_download:
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Список URL пуст или файл не найден. Завершение работы.")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Файлы будут сохранены в папку: '{DOWNLOAD_DIR}'")
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Всего найдено URL для загрузки: {len(urls_to_download)}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Ограничение одновременных загрузок: {MAX_CONCURRENT_TASKS}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Виртуальный браузер Chromium запущен в фоновом режиме.")
        
        tasks = [download_html(browser, url, semaphore) for url in urls_to_download]
            
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Запускаю загрузку {len(tasks)} страниц конвейерно...")
        
        await tqdm.gather(*tasks, desc="Обработка ссылок")
        
        await browser.close()
        print(f"\n{Fore.BLUE}[INFO]{Style.RESET_ALL} Все задачи завершены. Браузер закрыт. Выход из программы.")

if __name__ == "__main__":
    asyncio.run(main())