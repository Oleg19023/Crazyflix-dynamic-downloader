"""
------------------------------------------------------------------------------
SOFTWARE: CrazyFlix Downloader HTML
VERSION: 2.3

COPYRIGHT (C) 2026 CrazyFire. ALL RIGHTS RESERVED.

Developed and supported under the auspices of CrazyFire.
Lead developer and owner: W1zarD

This software code is the intellectual property of CrazyFire
and is intended solely for the internal needs of the CrazyFlix ecosystem.
Any unauthorized copying, modification, distribution,
or use of the algorithms without the written consent of W1zarD is strictly prohibited.

Automated Data Collection System (Data Mining Automation).

------------------------------------------------------------------------------
"""

# Убедитесь, что у вас установлены следующие библиотеки:
import asyncio
import re
import os
import sys
import random # Для случайных пауз
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm
from fake_useragent import UserAgent

init(autoreset=True)

# --- КОНФИГУРАЦИЯ ---
DOWNLOAD_DIR = "downloaded_html"
URL_FILE = "urls_to_download.txt"
MAX_CONCURRENT_TASKS = 1 # Важно: при Stealth режиме лучше 1 поток, максимум 2, если прокси хорошие
BASE_URL = "https://rezka.ag"

# ==========================================
#       ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{Fore.CYAN}{Style.BRIGHT}--- CrazyFlix Downloader & Parser by W1zarD v2.3 ---{Style.RESET_ALL}")
    print(f"{Fore.CYAN}--- Powered by CrazyFire Corp ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[STEALTH MODE ACTIVATED]{Style.RESET_ALL}\n")

def clean_filename(url: str) -> str:
    path = urlparse(url).path
    filename_base = path.split('/')[-1]
    if not filename_base:
        filename_base = path.split('/')[-2] if len(path.split('/')) > 1 else 'index'
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', filename_base)
    if not safe_name.lower().endswith('.html'):
        safe_name += '.html'
    return safe_name

def save_urls_to_file(new_urls: list):
    if not new_urls:
        print(f"{Fore.YELLOW}[WARNING] Нет ссылок для сохранения.{Style.RESET_ALL}")
        return

    existing_urls = set()
    if os.path.exists(URL_FILE):
        try:
            with open(URL_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    existing_urls.add(line.strip())
        except Exception:
            pass

    added_count = 0
    with open(URL_FILE, 'a', encoding='utf-8') as f:
        for url in new_urls:
            clean_url = url.strip()
            if clean_url and clean_url not in existing_urls:
                f.write(clean_url + "\n")
                existing_urls.add(clean_url)
                added_count += 1
    
    print(f"{Fore.GREEN}[SUCCESS] Добавлено {added_count} новых ссылок в {URL_FILE}.{Style.RESET_ALL}")

def load_urls_from_file() -> list:
    urls = []
    try:
        with open(URL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    urls.append(stripped_line)
    except FileNotFoundError:
        print(f"{Fore.RED}[ERROR] Файл '{URL_FILE}' не найден.{Style.RESET_ALL}")
    return urls

# ==========================================
#       РЕЖИМ 1: ПАРСИНГ ССЫЛОК
# ==========================================

async def parse_category_page(page, url):
    try:
        # Случайная задержка перед загрузкой (имитация человека)
        await asyncio.sleep(random.uniform(2, 5))
        
        await page.goto(url, wait_until='domcontentloaded', timeout=40000)
        links = await page.locator('.b-content__inline_item-link a').evaluate_all("els => els.map(e => e.href)")
        return links
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Ошибка парсинга {url}: {e}{Style.RESET_ALL}")
        return []

async def run_category_parser():
    print(f"\n{Fore.YELLOW}>>> Выбран режим: Парсинг категорий HDrezka{Style.RESET_ALL}")
    
    categories = {
        "1": ("Фильмы", "/films/"),
        "2": ("Сериалы", "/series/"),
        "3": ("Мультфильмы", "/cartoons/"),
        "4": ("Аниме", "/animation/"),
        "5": ("Новинки", "/new/"),
        "6": ("Анонсы", "/announce/")
    }

    print("Выберите категорию:")
    for key, val in categories.items():
        print(f"{key}. {val[0]}")
    
    cat_choice = input(f"{Fore.GREEN}Ваш выбор (цифра): {Style.RESET_ALL}").strip()
    if cat_choice not in categories: return

    base_cat_url = BASE_URL + categories[cat_choice][1]
    try:
        pages_count = int(input(f"{Fore.GREEN}Сколько страниц сканировать?: {Style.RESET_ALL}"))
    except ValueError: return

    print(f"{Fore.BLUE}[INFO] Начинаю сканирование...{Style.RESET_ALL}")
    collected_urls = []
    
    # ЗАПУСК БРАУЗЕРА В ВИДИМОМ РЕЖИМЕ (HEADLESS=FALSE)
    async with async_playwright() as p:
        ua = UserAgent()
        browser = await p.chromium.launch(
            headless=False, # Видимый браузер
            args=['--disable-blink-features=AutomationControlled'] # Скрытие автоматизации
        )
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()
        
        for i in range(1, pages_count + 1):
            target_url = base_cat_url if i == 1 else f"{base_cat_url}page/{i}/"
            print(f"Обработка страницы {i}/{pages_count}...", end='\r')
            links = await parse_category_page(page, target_url)
            collected_urls.extend(links)
        
        await browser.close()

    print(f"\n{Fore.BLUE}[INFO] Найдено всего ссылок: {len(collected_urls)}{Style.RESET_ALL}")
    save_urls_to_file(collected_urls)

async def run_franchise_parser():
    print(f"\n{Fore.YELLOW}>>> Выбран режим: Парсинг франшизы{Style.RESET_ALL}")
    url = input(f"{Fore.GREEN}Вставьте ссылку на франшизу: {Style.RESET_ALL}").strip()
    if not url: return

    print(f"{Fore.BLUE}[INFO] Загружаю страницу франшизы...{Style.RESET_ALL}")
    async with async_playwright() as p:
        ua = UserAgent()
        browser = await p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(user_agent=ua.random)
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            selector = '.b-post__partcontent_item .td.title a'
            try: await page.wait_for_selector(selector, timeout=10000)
            except: pass
            links = await page.locator(selector).evaluate_all("els => els.map(e => e.href)")
            print(f"{Fore.BLUE}[INFO] Найдено фильмов: {len(links)}{Style.RESET_ALL}")
            save_urls_to_file(links)
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Ошибка: {e}{Style.RESET_ALL}")
        await browser.close()

# ==========================================
#       РЕЖИМ 2: СКАЧИВАНИЕ HTML (CORE)
# ==========================================

async def download_html_task(browser, url: str, semaphore: asyncio.Semaphore) -> tuple:
    async with semaphore:
        file_name = os.path.join(DOWNLOAD_DIR, clean_filename(url))
        
        if os.path.exists(file_name):
            if os.path.getsize(file_name) > 0:
                tqdm.write(f"{Fore.MAGENTA}[Skip]{Style.RESET_ALL} [{url}] Файл уже существует.")
                return (url, True)

        tqdm.write(f"\n{Fore.BLUE}[INFO]{Style.RESET_ALL} Начинаю обработку: {url}")
        
        # Генерируем случайный User-Agent для каждого запроса
        ua = UserAgent()
        random_ua = ua.random

        # Настройки контекста для маскировки
        context = await browser.new_context(
            locale='ru-RU', 
            timezone_id='Europe/Moscow',
            user_agent=random_ua,
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Добавляем скрипт для скрытия webdriver флага
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page = await context.new_page()
            
            # СЛУЧАЙНАЯ ЗАДЕРЖКА перед переходом (Анти-бан)
            delay = random.uniform(2, 6)
            await asyncio.sleep(delay)

            await page.goto(url, wait_until='networkidle', timeout=40000)
            
            trailer_btn = 'a.b-sidelinks__link.show-trailer'
            
            try:
                await page.wait_for_selector(trailer_btn, state='visible', timeout=5000)
                tqdm.write(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} [{url}] Клик по кнопке трейлера...")
                await page.click(trailer_btn)
                
                # Рандомная задержка после клика (имитация просмотра)
                await asyncio.sleep(random.uniform(2, 4))
                tqdm.write(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} [{url}] HTML трейлера подгружен.")
            except TimeoutError:
                tqdm.write(f"[{url}] {Fore.YELLOW}[WARNING]{Style.RESET_ALL} Кнопка трейлера не найдена.")
            except Exception:
                pass

            html_content = await page.content()
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(html_content)
            
            tqdm.write(f"{Fore.GREEN}[Done]{Style.RESET_ALL} [{url}] Saved.")
            return (url, True) 

        except TimeoutError:
            tqdm.write(f"{Fore.RED}[Failed]{Style.RESET_ALL} [{url}] Timeout (40s).")
            return (url, False)
        except Exception as e:
            tqdm.write(f"{Fore.RED}[Failed]{Style.RESET_ALL} [{url}] Error: {e}")
            return (url, False) 
        finally:
            if 'page' in locals(): await page.close()
            await context.close()

async def run_html_downloader():
    print(f"\n{Fore.YELLOW}>>> Выбран режим: Скачивание HTML из списка{Style.RESET_ALL}")
    
    all_urls = load_urls_from_file()
    if not all_urls: return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    urls_to_process = all_urls
    attempt = 1

    # ВАЖНО: При Stealth режиме лучше 1 поток, максимум 2, если прокси хорошие
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

    async with async_playwright() as p:
        # ЗАПУСК БРАУЗЕРА В ВИДИМОМ РЕЖИМЕ С АРГУМЕНТАМИ
        browser = await p.chromium.launch(
            headless=False, # ОКНА БУДУТ ОТКРЫВАТЬСЯ - ЭТО НОРМАЛЬНО
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--start-maximized'
            ]
        )
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Браузер запущен (Stealth Mode). Потоков: {MAX_CONCURRENT_TASKS}")
        
        while urls_to_process:
            if attempt > 1:
                print(f"\n{Fore.YELLOW}--- Попытка №{attempt} (Повторная обработка ошибок) ---{Style.RESET_ALL}")
                print(f"Осталось загрузить: {len(urls_to_process)} файлов")
                await asyncio.sleep(5) 

            tasks = [download_html_task(browser, url, semaphore) for url in urls_to_process]
            results = await tqdm.gather(*tasks, desc=f"Загрузка (Круг {attempt})")
            failed_urls = [url for url, success in results if not success]
            
            if not failed_urls:
                print(f"\n{Fore.GREEN}[COMPLETE] Все файлы успешно загружены!{Style.RESET_ALL}")
                break
            else:
                print(f"\n{Fore.RED}[ATTENTION] Не удалось загрузить {len(failed_urls)} файлов.{Style.RESET_ALL}")
                
                if attempt >= 2:
                    print(f"{Fore.YELLOW}>>> Автоматические попытки исчерпаны.{Style.RESET_ALL}")
                    ask = input(f"{Fore.CYAN}Хотите попробовать загрузить оставшиеся файлы еще раз? (y/n): {Style.RESET_ALL}").strip().lower()
                    if ask != 'y':
                        print(f"{Fore.RED}[STOP] Загрузка завершена с ошибками.{Style.RESET_ALL}")
                        break
                
                urls_to_process = failed_urls
                attempt += 1
        
        await browser.close()

# ==========================================
#       ГЛАВНОЕ МЕНЮ И ЗАПУСК
# ==========================================

async def main_menu():
    while True:
        print_header()
        print(f"{Fore.WHITE}Выберите режим работы:{Style.RESET_ALL}")
        print("1. Парсинг ссылок (Создание списка)")
        print("2. Скачивание HTML (Из списка)")
        print("0. Выход")
        
        choice = input(f"\n{Fore.CYAN}Введите номер режима: {Style.RESET_ALL}").strip()

        if choice == "1":
            print(f"\n{Fore.WHITE}Выберите тип парсинга:{Style.RESET_ALL}")
            print("1. Парсинг категории")
            print("2. Парсинг франшизы")
            print("0. Назад")
            sub = input(f"\n{Fore.CYAN}Ваш выбор: {Style.RESET_ALL}").strip()
            if sub == "1": await run_category_parser()
            elif sub == "2": await run_franchise_parser()
            input(f"\n{Fore.WHITE}Нажмите Enter...{Style.RESET_ALL}")

        elif choice == "2":
            await run_html_downloader()
            input(f"\n{Fore.WHITE}Нажмите Enter...{Style.RESET_ALL}")

        elif choice == "0":
            sys.exit()

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Принудительная остановка.{Style.RESET_ALL}")