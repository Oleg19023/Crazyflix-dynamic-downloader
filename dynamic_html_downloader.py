"""
------------------------------------------------------------------------------
SOFTWARE: CrazyFlix Downloader HTML
VERSION: 4.5

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
    "fast_load": True
}

BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--window-position=10000,10000',
    '--window-size=1,1',
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars'
]

CURRENT_ACTIVE_PROXY = None
STOP_PROCESS = False

# ==========================================
#       СИСТЕМНЫЕ ФУНКЦИИ (ФАЙЛЫ) - В НАЧАЛЕ
# ==========================================

def load_urls_from_file() -> list:
    if not os.path.exists(URL_FILE): return []
    with open(URL_FILE, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]

def save_urls_to_file(new_urls: list):
    if not new_urls: return
    existing = set()
    if os.path.exists(URL_FILE):
        with open(URL_FILE, 'r', encoding='utf-8') as f:
            for line in f: existing.add(line.strip())
    added = 0
    with open(URL_FILE, 'a', encoding='utf-8') as f:
        for url in new_urls:
            u = url.strip()
            if u and u not in existing:
                f.write(u + "\n"); existing.add(u); added += 1
    print(f"\n{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} Добавлено уникальных ссылок: {added}")

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
    print(f"\n{Fore.CYAN}{Style.BRIGHT}--- CrazyFlix Downloader HTML by W1zarD v4.5 ---{Style.RESET_ALL}")
    print(f"{Fore.CYAN}--- Powered by CrazyFire ---{Style.RESET_ALL}")
    
    st_val = f"{Fore.GREEN}ON" if CONFIG['stealth'] else f"{Fore.RED}OFF"
    ad_val = f"{Fore.GREEN}ON" if CONFIG['adblock'] else f"{Fore.RED}OFF"
    fs_val = f"{Fore.GREEN}ON" if CONFIG['fast_load'] else f"{Fore.RED}OFF"
    
    print(f"{Fore.YELLOW}Stealth: {st_val} {Fore.WHITE}| {Fore.YELLOW}AdBlock: {ad_val} {Fore.WHITE}| {Fore.YELLOW}FastLoad: {fs_val}{Style.RESET_ALL}\n")

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
            idx = interactive_menu(["Продолжить работу", "Завершить и выйти в главное меню"], "[ПАУЗА]:", False)
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
                print(f"{Fore.GREEN}[Done] Список очищен.")
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
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            tqdm.write(f"{Fore.MAGENTA}[Skip]{Style.RESET_ALL} [{url}]")
            return (url, True)

        if not CURRENT_ACTIVE_PROXY and proxy_list: CURRENT_ACTIVE_PROXY = random.choice(proxy_list)
        p_display = f"(Proxy: {CURRENT_ACTIVE_PROXY})" if CURRENT_ACTIVE_PROXY else "(Local IP)"
        context = await browser.new_context(
            user_agent=UserAgent().random if CONFIG['stealth'] else None,
            proxy={"server": f"http://{CURRENT_ACTIVE_PROXY}"} if CURRENT_ACTIVE_PROXY else None,
            locale='ru-RU', timezone_id='Europe/Moscow'
        )

        async def block_ads(route):
            if any(ad in route.request.url for ad in AD_BLOCK_LIST): await route.abort()
            else: await route.continue_()

        try:
            page = await context.new_page()
            if CONFIG['adblock']: await page.route("**/*", block_ads)
            await page.add_init_script("window.open = () => { return null; }; Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
            if STOP_PROCESS: return (url, False)
            w_state = 'domcontentloaded' if CONFIG['fast_load'] else 'networkidle'
            await page.goto(url, wait_until=w_state, timeout=45000)
            try:
                btn = 'a.b-sidelinks__link.show-trailer'
                await page.wait_for_selector(btn, state='visible', timeout=8000)
                if not STOP_PROCESS: await page.click(btn); await asyncio.sleep(1.5)
            except: pass
            if not STOP_PROCESS:
                content = await page.content()
                with open(file_name, 'w', encoding='utf-8') as f: f.write(content)
                tqdm.write(f"{Fore.GREEN}[Done]{Style.RESET_ALL} {p_display} [{url}]")
                return (url, True)
            return (url, False)
        except Exception as e:
            err = str(e).split('\n')[0][:50]
            tqdm.write(f"{Fore.RED}[Failed]{Style.RESET_ALL} {p_display} [{url}] Error: {err}")
            CURRENT_ACTIVE_PROXY = None 
            return (url, False)
        finally: await context.close()

async def run_html_downloader():
    global STOP_PROCESS
    STOP_PROCESS = False
    urls, raw_proxies = load_urls_from_file(), load_proxies()
    if not urls: return
    favs = load_favorites()
    proxies = favs if favs else raw_proxies
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ЗАПУСК СКАЧИВАНИЯ ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[Нажмите ПРОБЕЛ для паузы или отмены]{Style.RESET_ALL}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        sem = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
        to_do, loop_cnt = urls, 1
        while to_do and not STOP_PROCESS:
            tasks = [download_html_task(browser, u, sem, proxies) for u in to_do]
            res = await tqdm.gather(*tasks, desc=f"Загрузка (Круг {loop_cnt})")
            if STOP_PROCESS: break
            failed = [u for u, s in res if not s]
            if not failed: break
            if loop_cnt >= 2:
                idx = interactive_menu(["Повторить попытку", "Выход"], f"Завершено. Ошибок: {len(failed)}", False)
                if idx == 1: break
            to_do, loop_cnt = failed, loop_cnt + 1
        await browser.close()
    
    # ФИКС: Пауза после завершения
    if not STOP_PROCESS:
        print(f"\n{Fore.GREEN}[COMPLETE] Процесс скачивания завершен успешно!{Style.RESET_ALL}")
        print(f"Нажмите любую клавишу для возврата в меню...")
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
    
    print(f"\n{Fore.GREEN}Введите количество страниц: {Style.RESET_ALL}", end="", flush=True)
    p_input = ""
    while True:
        char = msvcrt.getch()
        if char == b'\r': break
        if char.isdigit(): p_input += char.decode(); print(char.decode(), end="", flush=True)
    if not p_input: return
    p_num = int(p_input)
    
    favs = load_favorites()
    proxies = favs if favs else load_proxies()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ЗАПУСК ПАРСИНГА ССЫЛОК ---{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[Нажмите ПРОБЕЛ для паузы или отмены]{Style.RESET_ALL}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        all_l = []
        for i in range(1, p_num + 1):
            if STOP_PROCESS or check_interrupt(): break
            if not CURRENT_ACTIVE_PROXY and proxies: CURRENT_ACTIVE_PROXY = random.choice(proxies)
            p_display = f"(Proxy: {CURRENT_ACTIVE_PROXY})" if CURRENT_ACTIVE_PROXY else "(Local IP)"
            context = await browser.new_context(proxy={"server": f"http://{CURRENT_ACTIVE_PROXY}"} if CURRENT_ACTIVE_PROXY else None)
            try:
                page = await context.new_page()
                await page.goto(f"{BASE_URL}{cats[c_idx][1]}" + (f"page/{i}/" if i > 1 else ""), wait_until='domcontentloaded', timeout=25000)
                links = await page.locator('.b-content__inline_item-link a').evaluate_all("els => els.map(e => e.href)")
                all_l.extend(links)
                print(f"{Fore.GREEN}[Done]{Style.RESET_ALL} {p_display} Стр {i}/{p_num}")
            except Exception as e:
                err = str(e).split('\n')[0][:30]
                print(f"{Fore.RED}[Failed]{Style.RESET_ALL} {p_display} Стр {i} Error: {err}")
                CURRENT_ACTIVE_PROXY = None
            finally: await context.close()
        await browser.close()
    
    if all_l and not STOP_PROCESS: 
        save_urls_to_file(all_l)
        print(f"\n{Fore.GREEN}[COMPLETE] Парсинг завершен!{Style.RESET_ALL}")
        print("Нажмите любую клавишу для возврата...")
        msvcrt.getch()
    elif not STOP_PROCESS:
        print(f"\n{Fore.YELLOW}[INFO] Ссылки не найдены.{Style.RESET_ALL}")
        msvcrt.getch()

async def run_franchise_parser():
    global STOP_PROCESS
    print(f"\n{Fore.GREEN}Вставьте ссылку на франшизу: {Style.RESET_ALL}", end="", flush=True)
    url = input().strip()
    if not url: return
    favs = load_favorites()
    proxies = favs if favs else load_proxies()
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}--- ЗАПУСК ПАРСИНГА ФРАНШИЗЫ ---{Style.RESET_ALL}\n")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=BROWSER_ARGS)
        if not CURRENT_ACTIVE_PROXY and proxies: CURRENT_ACTIVE_PROXY = random.choice(proxies)
        ctx = await browser.new_context(proxy={"server": f"http://{CURRENT_ACTIVE_PROXY}"} if CURRENT_ACTIVE_PROXY else None)
        try:
            page = await ctx.new_page()
            await page.goto(url, wait_until='domcontentloaded')
            links = await page.locator('.b-post__partcontent_item .td.title a').evaluate_all("els => els.map(e => e.href)")
            if links: save_urls_to_file(links)
        except: pass
        await browser.close()
    
    print(f"\n{Fore.GREEN}[COMPLETE] Готово! Нажмите любую клавишу...{Style.RESET_ALL}")
    msvcrt.getch()

# ==========================================
#       МЕНЮ НАСТРОЕК
# ==========================================

async def settings_menu():
    while True:
        s_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['stealth'] else f"{Fore.RED}[ОТКЛ]"
        a_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['adblock'] else f"{Fore.RED}[ОТКЛ]"
        f_mode = f"{Fore.GREEN}[ВКЛ]" if CONFIG['fast_load'] else f"{Fore.RED}[ОТКЛ]"
        idx = interactive_menu([f"Stealth Mode  {s_mode}", f"AdBlock       {a_mode}", f"Fast Load     {f_mode}", "Справка", "Назад"], "НАСТРОЙКИ:", True)
        if idx == 0: CONFIG['stealth'] = not CONFIG['stealth']
        elif idx == 1: CONFIG['adblock'] = not CONFIG['adblock']
        elif idx == 2: CONFIG['fast_load'] = not CONFIG['fast_load']
        elif idx == 3:
            os.system('cls'); print(f"{Fore.CYAN}--- СПРАВКА ---\n\nСтрелки - Навигация\nEnter - Выбор (Toggle для Избранного)\nПробел - Пауза/Отмена во время работы\n\nИзбранные имеют приоритет и защищены от удаления."); msvcrt.getch()
        elif idx == 4: break

async def main_menu():
    global STOP_PROCESS
    while True:
        STOP_PROCESS = False
        idx = interactive_menu(["Парсинг ссылок для списка", "Скачивание HTML из списка", "Менеджер Прокси", "Настройки", "Выход"], "ГЛАВНОЕ МЕНЮ:", show_nav=False)
        if idx == 0:
            sub = interactive_menu(["Категории", "Франшизы", "Назад"], "ТИП ПАРСИНГА:", True)
            if sub == 0: await run_category_parser()
            elif sub == 1: await run_franchise_parser()
        elif idx == 1: await run_html_downloader()
        elif idx == 2: await run_proxy_manager()
        elif idx == 3: await settings_menu()
        elif idx == 4: sys.exit()

if __name__ == "__main__":
    try: asyncio.run(main_menu())
    except KeyboardInterrupt: pass