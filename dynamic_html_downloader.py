"""
------------------------------------------------------------------------------
SOFTWARE: CrazyFlix Downloader HTML
VERSION: 5.6

АВТОРСКИЕ ПРАВА (C) 2026 CrazyFire. ВСЕ ПРАВА ЗАЩИЩЕНЫ.

Разработано и поддерживается под эгидой CrazyFire.
Ведущий разработчик и владелец: W1zarD

Данный программный код является интеллектуальной собственностью CrazyFire
и предназначен исключительно для внутренних нужд экосистемы CrazyFlix.
------------------------------------------------------------------------------
"""

import asyncio
import re
import os
import sys
import random
import time
import aiohttp
import msvcrt
from playwright.async_api import async_playwright, TimeoutError
from urllib.parse import urlparse
from colorama import Fore, Style, init
from tqdm.asyncio import tqdm
from fake_useragent import UserAgent

init(autoreset=True)

# --- КОНФИГУРАЦИЯ ---
DOWNLOAD_DIR = "downloaded_html"
URL_FILE = "urls_to_download.txt"
PARSER_FILE = "parser_urls.txt"   
PROXY_FILE = "proxies.txt"
FAVORITES_FILE = "favorites_proxies.txt"
MAX_CONCURRENT_TASKS = 1 
MAX_CHECKER_CONCURRENT = 50 
BASE_URL = "https://rezka.ag"

AD_BLOCK_LIST = [
    "google-analytics.com", "googletagmanager.com", "yandex.ru", "doubleclick.net",
    "adservice", "analytics", "adskeeper", "mgid.com", "ad-maven", "popads",
    "onclickads", "bet365", "1xbet", "mostbet", "parimatch", "traffic", "asg.franecki.net"
]

CONFIG = {
    "stealth": True,
    "adblock": True,
    "fast_load": True,
    "use_proxy": True,
    "infinite_retry": False
}

BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--window-position=10000,10000',
    '--window-size=1920,1080',
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars'
]

CURRENT_ACTIVE_PROXY = None
STOP_PROCESS = False

# ==========================================
#       СИСТЕМНЫЕ ФУНКЦИИ
# ==========================================

def load_urls_from_file() -> list:
    urls = []
    for file in [URL_FILE, PARSER_FILE]:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                urls.extend([l.strip() for l in f if l.strip() and not l.startswith('#')])
    
    seen = set()
    return [x for x in urls if not (x in seen or seen.add(x))]

def append_to_parser_file(new_urls: list):
    if not new_urls: return 0
    existing = set()
    if os.path.exists(PARSER_FILE):
        with open(PARSER_FILE, 'r', encoding='utf-8') as f:
            for line in f: existing.add(line.strip())
    added = 0
    with open(PARSER_FILE, 'a', encoding='utf-8') as f:
        for url in new_urls:
            u = url.strip()
            if u and u not in existing:
                f.write(u + "\n")
                existing.add(u)
                added += 1
    return added

def clear_url_file():
    print(f"\n{Fore.YELLOW}Вы уверены, что хотите очистить все списки ссылок (Y/N)?: {Style.RESET_ALL}", end="", flush=True)
    
    raw_char = msvcrt.getch()
    try:
        confirm = raw_char.decode('cp866').lower() 
    except:
        confirm = raw_char.decode('utf-8', errors='ignore').lower()

    if confirm == 'y' or confirm == 'г':
        if os.path.exists(URL_FILE):
            with open(URL_FILE, 'w', encoding='utf-8') as f: f.write("")
        if os.path.exists(PARSER_FILE):
            with open(PARSER_FILE, 'w', encoding='utf-8') as f: f.write("")
        print(f"\n{Fore.GREEN}[DONE]{Style.RESET_ALL} Списки ссылок очищены.")
    else:
        print(f"\n{Fore.CYAN}[SKIP]{Style.RESET_ALL} Отмена операции.")
    time.sleep(1)

def load_proxies() -> list:
    if not os.path.exists(PROXY_FILE): return []
    with open(PROXY_FILE, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]

def load_favorites() -> list:
    if not os.path.exists(FAVORITES_FILE): return []
    with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]

def save_favorites(fav_list: list):
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        for p in fav_list: f.write(p + "\n")

def clean_filename(url: str) -> str:
    path = urlparse(url).path
    filename_base = path.split('/')[-1]
    if not filename_base: filename_base = path.split('/')[-2] if len(path.split('/')) > 1 else 'index'
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', filename_base)
    if not safe_name.lower().endswith('.html'): safe_name += '.html'
    return safe_name

# ==========================================
#       ИНТЕРФЕЙСНЫЕ ФУНКЦИИ
# ==========================================

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\n{Fore.CYAN}{Style.BRIGHT}--- CrazyFlix Downloader HTML by W1zarD v5.6 ---{Style.RESET_ALL}")
    print(f"{Fore.CYAN}--- Powered by CrazyFire ---{Style.RESET_ALL}")
    
    st_val = f"{Fore.GREEN}ON" if CONFIG['stealth'] else f"{Fore.RED}OFF"
    ad_val = f"{Fore.GREEN}ON" if CONFIG['adblock'] else f"{Fore.RED}OFF"
    fs_val = f"{Fore.GREEN}ON" if CONFIG['fast_load'] else f"{Fore.RED}OFF"
    pr_val = f"{Fore.GREEN}ON" if CONFIG['use_proxy'] else f"{Fore.RED}OFF"
    ir_val = f"{Fore.GREEN}ON" if CONFIG['infinite_retry'] else f"{Fore.RED}OFF"
    
    print(f"{Fore.YELLOW}Stealth: {st_val} | {Fore.YELLOW}AdBlock: {ad_val} | {Fore.YELLOW}FastLoad: {fs_val}")
    print(f"{Fore.YELLOW}Use Proxy: {pr_val} | {Fore.YELLOW}Infinite Retry: {ir_val}{Style.RESET_ALL}\n")

def interactive_menu(options, title="Выберите пункт:", show_nav=True, start_pos=0):
    current_idx = start_pos
    visible_count = 15 
    while True:
        print_header()
        if show_nav:
            print(f"{Fore.WHITE}[Стрелки: Навигация | Enter: Выбрать]{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{title}{Style.RESET_ALL}")
        
        start_view = max(0, current_idx - visible_count // 2)
        end_view = min(len(options), start_view + visible_count)
        
        if start_view > 0: print("    ...")
        for i in range(start_view, end_view):
            if i == current_idx:
                print(f"{Fore.CYAN}  > {Style.BRIGHT}{options[i]}{Style.RESET_ALL}")
            else:
                print(f"    {options[i]}")
        if end_view < len(options): print("    ...")
        
        while not msvcrt.kbhit(): time.sleep(0.05)
        key = msvcrt.getch()
        
        if key == b'\r': return current_idx
        elif key == b'\xe0':
            key = msvcrt.getch()
            if key == b'H': current_idx = (current_idx - 1) % len(options)
            elif key == b'P': current_idx = (current_idx + 1) % len(options)
        elif key == b'\x1b': return -1

def check_interrupt():
    global STOP_PROCESS
    if msvcrt.kbhit():
        if msvcrt.getch() == b' ':
            os.system('cls' if os.name == 'nt' else 'clear')
            idx = interactive_menu(["Продолжить работу", "Завершить и выйти в меню"], "[ПАУЗА]:", False)
            if idx == 1:
                STOP_PROCESS = True
                return True
            else:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{Fore.GREEN}--- Возврат к выполнению задачи ---{Style.RESET_ALL}")
    return False

# ==========================================
#       РЕЖИМ 3: ПРОКСИ
# ==========================================

async def check_single_proxy(session, p_addr, semaphore):
    async with semaphore:
        try:
            async with session.get("http://www.google.com", proxy=f"http://{p_addr}", timeout=10) as r:
                if r.status == 200: return p_addr, True
        except: pass
        return p_addr, False

async def run_proxy_manager():
    while True:
        idx = interactive_menu([
            "Загрузить 100 СВЕЖИХ прокси", 
            "Проверить текущий список", 
            "Управление Избранным (Toggle)",
            "Очистить список Избранного",
            "Назад"
        ], "МЕНЕДЖЕР ПРОКСИ:", True)
        
        if idx == 0:
            print(f"{Fore.BLUE}[INFO] Сбор данных...{Style.RESET_ALL}")
            s1, s2 = [], []
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                try:
                    await page.goto("https://free-proxy-list.net/", timeout=30000)
                    all_s1 = await page.evaluate("""() => {
                        const rows = Array.from(document.querySelectorAll('table.table tbody tr'));
                        return rows.map(row => {
                            const cells = row.querySelectorAll('td');
                            return cells.length > 1 ? cells[0].innerText + ':' + cells[1].innerText : null;
                        }).filter(p => p !== null);
                    }""")
                    s1 = all_s1[:50]
                except: pass
                finally: await browser.close()
            try:
                url2 = "https://proxylist.geonode.com/api/proxy-list?limit=50&page=1&sort_by=lastChecked&sort_type=desc"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url2, timeout=15) as resp:
                        if resp.status == 200:
                            json_data = await resp.json()
                            s2 = [f"{i['ip']}:{i['port']}" for i in json_data.get('data', [])]
            except: pass
            combined = list(set(s1 + s2))
            if combined:
                with open(PROXY_FILE, 'w', encoding='utf-8') as f:
                    for p in combined: f.write(p + "\n")
                print(f"{Fore.GREEN}[SUCCESS] Сохранено {len(combined)} прокси.")
            input("\nEnter...")

        elif idx == 1:
            proxies = load_proxies()
            favs = load_favorites()
            if not proxies: continue
            print(f"Тестирование {len(proxies)} шт...")
            sem = asyncio.Semaphore(MAX_CHECKER_CONCURRENT)
            async with aiohttp.ClientSession() as session:
                tasks = [check_single_proxy(session, p, sem) for p in proxies]
                results = await tqdm.gather(*tasks, desc="Тестирование")
                working = [addr for addr, ok in results if ok]
            to_keep = list(set(working + favs))
            dead_cleaned = len(proxies) - len(to_keep)
            print(f"\n{Fore.GREEN}Рабочие: {len(working)} | {Fore.YELLOW}Избранные (защищены): {len(favs)}")
            if dead_cleaned > 0 and input(f"Удалить {dead_cleaned} нерабочих? (y/n): ").lower() == 'y':
                with open(PROXY_FILE, 'w') as f:
                    for p in to_keep: f.write(p + "\n")
                print(f"{Fore.GREEN}[DONE] Список очищен.")
            input("\nEnter...")

        elif idx == 2:
            curr_p = 0
            while True:
                proxies = load_proxies()
                if not proxies: break
                favs = set(load_favorites())
                menu_list = [f"{p} {'[*]' if p in favs else ''}" for p in proxies]
                p_idx = interactive_menu(menu_list + ["Назад"], "УПРАВЛЕНИЕ ИЗБРАННЫМ (Enter - Toggle):", True, curr_p)
                if p_idx == -1 or p_idx == len(proxies): break
                curr_p = p_idx
                selected = proxies[p_idx]
                if selected in favs: favs.remove(selected)
                else: favs.add(selected)
                save_favorites(list(favs))

        elif idx == 3:
            if os.path.exists(FAVORITES_FILE): os.remove(FAVORITES_FILE)
            print(f"{Fore.RED}Избранное очищено.")
            time.sleep(1)

        elif idx == 4: break

# ==========================================
#       РЕЖИМ 2: СКАЧИВАНИЕ
# ==========================================

async def download_html_task(browser, url, semaphore, proxy_list):
    global CURRENT_ACTIVE_PROXY, STOP_PROCESS
    if STOP_PROCESS: return (url, False)
    
    async with semaphore:
        if check_interrupt() or STOP_PROCESS: return (url, False)
        
        file_name = os.path.join(DOWNLOAD_DIR, clean_filename(url))
        
        tqdm.write(f"\n{Fore.BLUE}{Style.BRIGHT}=== [ TASK START ] ==={Style.RESET_ALL}")
        tqdm.write(f"{Fore.WHITE}URL: {url}{Style.RESET_ALL}")
        
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            tqdm.write(f"{Fore.MAGENTA}[SKIP]{Style.RESET_ALL} Файл уже скачан.")
            return (url, True)

        proxy_config = None
        if CONFIG["use_proxy"] and proxy_list:
            if not CURRENT_ACTIVE_PROXY: CURRENT_ACTIVE_PROXY = random.choice(proxy_list)
            proxy_config = {"server": f"http://{CURRENT_ACTIVE_PROXY}"}
            p_display = f"{CURRENT_ACTIVE_PROXY}"
        else:
            CURRENT_ACTIVE_PROXY = None
            p_display = "Local IP"
        
        tqdm.write(f"{Fore.CYAN}[INIT]{Style.RESET_ALL} Настройка сессии... Proxy: {p_display}")
        
        context = await browser.new_context(
            user_agent=UserAgent().random if CONFIG['stealth'] else None,
            proxy=proxy_config,
            locale='ru-RU', timezone_id='Europe/Moscow'
        )

        async def block_ads(route):
            if any(ad in route.request.url for ad in AD_BLOCK_LIST): await route.abort()
            else: await route.continue_()

        try:
            page = await context.new_page()
            if CONFIG['adblock']: await page.route("**/*", block_ads)
            await page.add_init_script("window.open = () => { return null; }; Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            
            w_state = 'domcontentloaded' if CONFIG['fast_load'] else 'networkidle'
            tqdm.write(f"{Fore.CYAN}[NETWORK]{Style.RESET_ALL} Загрузка контента...")
            await page.goto(url, wait_until=w_state, timeout=45000)
            
            # --- ТРЕЙЛЕР ---
            try:
                tqdm.write(f"{Fore.CYAN}[SEARCH]{Style.RESET_ALL} Поиск кнопки трейлера...")
                try: await page.wait_for_load_state('networkidle', timeout=5000); await asyncio.sleep(1)
                except: pass

                btn = page.locator('a.b-sidelinks__link.show-trailer').first
                
                if await btn.count() > 0 and await btn.is_visible():
                    trailer_opened = False
                    for attempt in range(1, 4):
                        if STOP_PROCESS: break
                        tqdm.write(f"  {Fore.YELLOW}[TRAILER]{Style.RESET_ALL} Попытка {attempt}/3...")
                        try:
                            await btn.hover(timeout=3000)
                            await btn.click(force=True, timeout=3000)
                            await btn.evaluate("""node => {
                                const e = new MouseEvent('click', {view:window, bubbles:true, cancelable:true});
                                node.dispatchEvent(e);
                            }""")
                            await page.wait_for_selector('iframe[src*="youtube"], iframe[src*="google"], .mfp-wrap', state='attached', timeout=4000)
                            tqdm.write(f"  {Fore.GREEN}[TRAILER]{Style.RESET_ALL} Плеер обнаружен в коде.")
                            await asyncio.sleep(1.5)
                            trailer_opened = True
                            break 
                        except:
                            tqdm.write(f"  {Fore.RED}[TRAILER]{Style.RESET_ALL} Ссылка не найдена.")
                    
                    if not trailer_opened and not STOP_PROCESS:
                        tqdm.write(f"  {Fore.RED}[ERROR]{Style.RESET_ALL} Не удалось найти плеер. Отмена.")
                        return (url, False) 
                else:
                    tqdm.write(f"  {Fore.MAGENTA}[TRAILER]{Style.RESET_ALL} Трейлер отсутствует.")
            except Exception as e: 
                tqdm.write(f"  {Fore.RED}[ERROR]{Style.RESET_ALL} Ошибка: {str(e).splitlines()[0][:40]}")
                return (url, False)
            # ---------------

            if not STOP_PROCESS:
                tqdm.write(f"{Fore.CYAN}[SAVE]{Style.RESET_ALL} Сохранение HTML...")
                content = await page.content()
                with open(file_name, 'w', encoding='utf-8') as f: f.write(content)
                tqdm.write(f"{Fore.GREEN}[DONE]{Style.RESET_ALL} Завершено: {clean_filename(url)}")
                return (url, True)
            return (url, False)
            
        except Exception as e:
            tqdm.write(f"{Fore.RED}[FAILED]{Style.RESET_ALL} Ошибка: {str(e).splitlines()[0][:50]}")
            CURRENT_ACTIVE_PROXY = None 
            return (url, False)
        finally: await context.close()

async def run_html_downloader():
    global STOP_PROCESS
    STOP_PROCESS = False
    urls, raw_proxies = load_urls_from_file(), load_proxies()
    if not urls: 
        print(f"\n{Fore.YELLOW}[INFO] Список ссылок пуст!{Style.RESET_ALL}")
        time.sleep(2)
        return
        
    favs = load_favorites()
    proxies = favs if favs else raw_proxies
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ЗАПУСК СКАЧИВАНИЯ ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[ПРОБЕЛ - Пауза/Отмена]{Style.RESET_ALL}\n")
    print(f"{Fore.WHITE}Всего ссылок в очереди: {len(urls)}{Style.RESET_ALL}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        to_do, loop_cnt = urls, 1
        
        while to_do and not STOP_PROCESS:
            tasks = [download_html_task(browser, u, sem, proxies) for u in to_do]
            res = await tqdm.gather(*tasks, desc=f"Круг {loop_cnt}")
            if STOP_PROCESS: break
            failed = [u for u, s in res if not s]
            
            if not failed: break
            
            if CONFIG["infinite_retry"]:
                tqdm.write(f"\n{Fore.YELLOW}[RETRY]{Style.RESET_ALL} Режим 'До победного' активен. Начинаем круг {loop_cnt+1}...")
                to_do, loop_cnt = failed, loop_cnt + 1
                continue

            if loop_cnt >= 2:
                idx = interactive_menu(["Повторить еще раз", "Выход"], f"Завершено. Ошибок: {len(failed)}", False)
                if idx == 1: break
            
            to_do, loop_cnt = failed, loop_cnt + 1
        await browser.close()
    
    if not STOP_PROCESS:
        print(f"\n{Fore.GREEN}[SUCCESS] Работа завершена!{Style.RESET_ALL}")
        msvcrt.getch()

# ==========================================
#       РЕЖИМ 1: ПАРСЕР
# ==========================================

async def run_category_parser():
    global CURRENT_ACTIVE_PROXY, STOP_PROCESS
    STOP_PROCESS = False
    cats = [("Фильмы", "/films/"), ("Сериалы", "/series/"), ("Мультфильмы", "/cartoons/"), 
            ("Аниме", "/animation/"), ("Новинки", "/new/"), ("Анонсы", "/announce/")]
    c_idx = interactive_menu([c[0] for c in cats] + ["Назад"], "КАТЕГОРИЯ:", True)
    if c_idx == 6: return
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- НАСТРОЙКА ПАРСИНГА ---{Style.RESET_ALL}\n")
    
    try:
        start_p = int(input(f"{Fore.GREEN}Введите начальную страницу (например, 1): {Style.RESET_ALL}").strip())
        end_p = int(input(f"{Fore.GREEN}Введите конечную страницу (например, 50): {Style.RESET_ALL}").strip())
    except ValueError:
        print(f"\n{Fore.RED}[ERROR] Необходимо вводить только цифры! Возврат в меню.{Style.RESET_ALL}")
        time.sleep(2)
        return

    if start_p < 1: start_p = 1
    if end_p < start_p: end_p = start_p
    
    favs = load_favorites()
    proxies = favs if favs else load_proxies()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ПАРСИНГ (Стр. {start_p} - {end_p}) ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[ПРОБЕЛ - Пауза/Отмена]{Style.RESET_ALL}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        
        pages_to_parse = list(range(start_p, end_p + 1))
        loop_cnt = 1
        
        while pages_to_parse and not STOP_PROCESS:
            failed_pages = []
            
            for i in pages_to_parse:
                if STOP_PROCESS or check_interrupt(): break
                
                proxy_config = None
                if CONFIG["use_proxy"] and proxies:
                    if not CURRENT_ACTIVE_PROXY: CURRENT_ACTIVE_PROXY = random.choice(proxies)
                    proxy_config = {"server": f"http://{CURRENT_ACTIVE_PROXY}"}
                    p_display = f"{CURRENT_ACTIVE_PROXY}"
                else:
                    p_display = "Local IP"

                context = await browser.new_context(proxy=proxy_config)
                try:
                    page = await context.new_page()
                    url_to_parse = f"{BASE_URL}{cats[c_idx][1]}" + (f"page/{i}/" if i > 1 else "")
                    
                    links = []
                    
                    # Делаем 2 попытки (обычная загрузка + перезагрузка если не дотянули до 36)
                    for attempt in range(1, 3):
                        if STOP_PROCESS: break
                        try: 
                            if attempt == 1:
                                await page.goto(url_to_parse, wait_until='domcontentloaded', timeout=15000)
                            else:
                                print(f"  {Fore.YELLOW}[RELOAD]{Style.RESET_ALL} Найдено {len(links)}/36. Перезагрузка...")
                                await page.reload(wait_until='domcontentloaded', timeout=15000)
                        except: pass 

                        poll_start = time.time()
                        last_count = 0
                        stable_time = time.time()
                        
                        while time.time() - poll_start < 12:
                            try:
                                links = await page.locator('.b-content__inline_item-link a').evaluate_all("els => els.map(e => e.href)")
                                if len(links) >= 36:
                                    break
                                    
                                # Проверка на зависание (если счетчик не меняется 3 секунды - идем дальше)
                                if len(links) != last_count:
                                    last_count = len(links)
                                    stable_time = time.time()
                                elif len(links) > 0 and time.time() - stable_time > 3:
                                    break
                            except: pass
                            await asyncio.sleep(0.5)
                            
                        # Если набрали 36, выходим из цикла попыток и не перезагружаем
                        if len(links) >= 36:
                            break

                    if len(links) > 0:
                        added = append_to_parser_file(links)
                        print(f"{Fore.GREEN}[DONE]{Style.RESET_ALL} {p_display} Стр {i}/{end_p} | Найдено: {len(links)} | Новых: {added}")
                    else:
                        raise Exception("Ссылки не найдены")
                        
                except Exception as e:
                    print(f"{Fore.RED}[FAILED]{Style.RESET_ALL} Стр {i} Error: {str(e)[:30]}")
                    CURRENT_ACTIVE_PROXY = None
                    failed_pages.append(i)
                finally: 
                    await context.close()
            
            if STOP_PROCESS or not failed_pages: break
            
            if CONFIG["infinite_retry"]:
                print(f"\n{Fore.YELLOW}[RETRY]{Style.RESET_ALL} Повтор неудачных страниц. Круг {loop_cnt+1}...")
                pages_to_parse = failed_pages
                loop_cnt += 1
                time.sleep(1)
            else:
                idx = interactive_menu(["Повторить неудачные страницы", "Завершить"], f"Ошибок парсинга: {len(failed_pages)}", False)
                if idx == 1: break
                pages_to_parse = failed_pages
                loop_cnt += 1

        await browser.close()
    
    if not STOP_PROCESS:
        print(f"\n{Fore.GREEN}[SUCCESS] Парсинг завершен! Данные сохранены в {PARSER_FILE}{Style.RESET_ALL}")
        msvcrt.getch()

async def run_franchise_parser():
    global STOP_PROCESS, CURRENT_ACTIVE_PROXY
    STOP_PROCESS = False
    print(f"\n{Fore.GREEN}Ссылка на франшизу: {Style.RESET_ALL}", end="", flush=True)
    url = input().strip()
    if not url: return
    favs = load_favorites()
    proxies = favs if favs else load_proxies()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ПАРСИНГ ---{Style.RESET_ALL}\n")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        
        proxy_config = None
        if CONFIG["use_proxy"] and proxies:
            if not CURRENT_ACTIVE_PROXY: CURRENT_ACTIVE_PROXY = random.choice(proxies)
            proxy_config = {"server": f"http://{CURRENT_ACTIVE_PROXY}"}

        ctx = await browser.new_context(proxy=proxy_config)
        try:
            page = await ctx.new_page()
            await page.goto(url, wait_until='domcontentloaded')
            links = await page.locator('.b-post__partcontent_item .td.title a').evaluate_all("els => els.map(e => e.href)")
            if links: 
                added = append_to_parser_file(links)
                print(f"{Fore.GREEN}[DONE]{Style.RESET_ALL} Добавлено {added} ссылок.")
        except: pass
        await browser.close()
    print(f"\n{Fore.GREEN}[SUCCESS] Готово! Данные в {PARSER_FILE}{Style.RESET_ALL}")
    msvcrt.getch()

# ==========================================
#       МЕНЮ НАСТРОЕК
# ==========================================

async def settings_menu():
    while True:
        s_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['stealth'] else f"{Fore.RED}[ОТКЛ]"
        a_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['adblock'] else f"{Fore.RED}[ОТКЛ]"
        f_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['fast_load'] else f"{Fore.RED}[ОТКЛ]"
        p_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['use_proxy'] else f"{Fore.RED}[ОТКЛ]"
        i_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['infinite_retry'] else f"{Fore.RED}[ОТКЛ]"
        
        idx = interactive_menu([
            f"Stealth Mode      {s_mode}", 
            f"AdBlock           {a_mode}", 
            f"Fast Load         {f_mode}", 
            f"Use Proxy         {p_mode}", 
            f"Infinite Retry    {i_mode}",
            "Назад"
        ], "НАСТРОЙКИ:", True)
        
        if idx == 0: CONFIG['stealth'] = not CONFIG['stealth']
        elif idx == 1: CONFIG['adblock'] = not CONFIG['adblock']
        elif idx == 2: CONFIG['fast_load'] = not CONFIG['fast_load']
        elif idx == 3: CONFIG['use_proxy'] = not CONFIG['use_proxy']
        elif idx == 4: CONFIG['infinite_retry'] = not CONFIG['infinite_retry']
        elif idx == 5: break

async def main_menu():
    global STOP_PROCESS
    while True:
        STOP_PROCESS = False
        idx = interactive_menu([
            "Парсинг ссылок (Сбор)", 
            "Скачивание HTML (Загрузка)", 
            "Менеджер Прокси", 
            "Настройки программы", 
            "Очистить списки ссылок",
            "Выход"
        ], "ГЛАВНОЕ МЕНЮ:", show_nav=False)
        
        if idx == 0:
            sub = interactive_menu(["Категории", "Франшизы", "Назад"], "ТИП ПАРСИНГА:", True)
            if sub == 0: await run_category_parser()
            elif sub == 1: await run_franchise_parser()
        elif idx == 1: await run_html_downloader()
        elif idx == 2: await run_proxy_manager()
        elif idx == 3: await settings_menu()
        elif idx == 4: clear_url_file()
        elif idx == 5: sys.exit()

if __name__ == "__main__":
    try: asyncio.run(main_menu())
    except KeyboardInterrupt: pass