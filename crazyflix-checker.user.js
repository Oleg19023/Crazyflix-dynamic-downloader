// ==UserScript==
// @name         CrazyFlix Rezka DB Checker
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Сканирует Rezka.ag, подсвечивает фильмы по базе CrazyFlix и позволяет собирать недостающие ссылки.
// @author       W1zarD
// @match        *://rezka.ag/*
// @match        *://*.rezka.ag/*
// @match        *://hdrezka.*/*
// @match        *://*.hdrezka.*/*
// @match        *://rezka.*/*
// @updateURL    https://raw.githubusercontent.com/Oleg19023/Crazyflix-dynamic-downloader/main/crazyflix-checker.user.js
// @downloadURL  https://raw.githubusercontent.com/Oleg19023/Crazyflix-dynamic-downloader/main/crazyflix-checker.user.js
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      cdn.jsdelivr.net
// ==/UserScript==

(function() {
    'use strict';

    const DB_URL = "https://cdn.jsdelivr.net/gh/Oleg19023/crazyflix-api.json@main/crazyflix-api.json";
    const STORE_KEY = 'crazyflix_saved_urls';

    let knownIds = new Set();

    // ==========================================
    // СТИЛИ (CSS)
    // ==========================================
    GM_addStyle(`
        .cf-card-green { border: 3px solid #4caf50 !important; border-radius: 5px; box-sizing: border-box; position: relative; }
        .cf-card-red { border: 3px solid #ff4d4d !important; border-radius: 5px; box-sizing: border-box; position: relative; }

        .cf-save-btn {
            position: absolute; top: 5px; left: 5px; z-index: 99;
            background: #ff4d4d; color: white; border: none; border-radius: 3px;
            padding: 5px 8px; font-size: 12px; font-weight: bold; cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.5); transition: 0.2s;
        }
        .cf-save-btn:hover { background: #ff1a1a; transform: scale(1.05); }
        .cf-save-btn.saved { background: #4caf50; pointer-events: none; }

        #cf-manager-btn {
            position: fixed; bottom: 20px; right: 20px; z-index: 9999;
            background: #00bcd4; color: white; border: none; border-radius: 50px;
            padding: 10px 20px; font-size: 14px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: 0.3s;
        }
        #cf-manager-btn:hover { background: #0097a7; box-shadow: 0 6px 8px rgba(0,0,0,0.5); }

        #cf-modal {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 10000; justify-content: center; align-items: center;
        }
        #cf-modal-content {
            background: #222; color: #fff; width: 600px; max-width: 90%; max-height: 80%;
            border-radius: 8px; padding: 20px; display: flex; flex-direction: column;
            box-shadow: 0 0 20px rgba(0,188,212,0.5); border: 1px solid #00bcd4;
        }
        #cf-modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; padding-bottom: 10px; margin-bottom: 10px; }
        #cf-modal-header h2 { margin: 0; font-size: 20px; color: #00bcd4; }
        #cf-close-modal { background: none; border: none; color: #ff4d4d; font-size: 24px; cursor: pointer; }

        #cf-url-list { flex-grow: 1; overflow-y: auto; background: #111; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
        .cf-url-item { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid #333; }
        .cf-url-text { word-break: break-all; font-size: 13px; color: #bbb; padding-right: 10px; }
        .cf-delete-item { background: #ff4d4d; color: white; border: none; border-radius: 3px; padding: 3px 8px; cursor: pointer; font-size: 12px; }
        .cf-delete-item:hover { background: #ff1a1a; }

        .cf-modal-footer { display: flex; gap: 10px; flex-wrap: wrap; }
        .cf-action-btn { flex: 1; padding: 10px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; color: white; }
        .cf-btn-copy { background: #4caf50; } .cf-btn-copy:hover { background: #388e3c; }
        .cf-btn-export { background: #2196f3; } .cf-btn-export:hover { background: #1976d2; }
        .cf-btn-clear { background: #f44336; } .cf-btn-clear:hover { background: #d32f2f; }
    `);

    // ==========================================
    // ЛОГИКА РАБОТЫ С ДАННЫМИ
    // ==========================================
    function getSavedUrls() {
        return JSON.parse(GM_getValue(STORE_KEY, '[]'));
    }

    function saveUrl(url) {
        let urls = getSavedUrls();
        if (!urls.includes(url)) {
            urls.push(url);
            GM_setValue(STORE_KEY, JSON.stringify(urls));
        }
    }

    function removeUrl(url) {
        let urls = getSavedUrls();
        urls = urls.filter(u => u !== url);
        GM_setValue(STORE_KEY, JSON.stringify(urls));
        renderModalList();
    }

    function clearAllUrls() {
        if(confirm("Точно удалить все сохраненные ссылки?")) {
            GM_setValue(STORE_KEY, '[]');
            renderModalList();
        }
    }

    // Универсальный извлекатель ID из ссылок Резки (например, из "12345-film.html" достает "12345")
    function extractIdFromUrl(url) {
        const match = url.match(/\/(\d+)-[a-zA-Z0-9_-]+\.html/);
        return match ? match[1] : null;
    }

    // Загрузка базы CrazyFlix
    function fetchDatabase() {
        console.log("[CrazyFlix] Загрузка базы данных...");
        GM_xmlhttpRequest({
            method: "GET",
            url: DB_URL,
            onload: function(response) {
                if (response.status === 200) {
                    const text = response.responseText;
                    // Ищем все вхождения ID в JSON, чтобы не зависеть от структуры файла
                    const regex = /(\d+)-[a-zA-Z0-9_-]+\.html/g;
                    let match;
                    while ((match = regex.exec(text)) !== null) {
                        knownIds.add(match[1]);
                    }
                    console.log(`[CrazyFlix] База загружена. Найдено уникальных ID: ${knownIds.size}`);
                    processCards(); // Запускаем проверку после загрузки
                } else {
                    console.error("[CrazyFlix] Ошибка загрузки БД:", response.status);
                }
            }
        });
    }

    // ==========================================
    // ЛОГИКА ОБРАБОТКИ КАРТОЧЕК
    // ==========================================
    function processCards() {
        // Находим все карточки на странице
        const cards = document.querySelectorAll('.b-content__inline_item');

        cards.forEach(card => {
            // Если карточка уже обработана, пропускаем
            if (card.classList.contains('cf-processed')) return;

            const linkElement = card.querySelector('.b-content__inline_item-link a');
            if (!linkElement) return;

            const url = linkElement.href;
            const id = extractIdFromUrl(url);

            if (id) {
                if (knownIds.has(id)) {
                    // Фильм ЕСТЬ в базе
                    card.classList.add('cf-card-green');
                } else {
                    // Фильма НЕТ в базе
                    card.classList.add('cf-card-red');

                    // Создаем кнопку сохранения
                    const saveBtn = document.createElement('button');
                    saveBtn.className = 'cf-save-btn';
                    saveBtn.innerHTML = '💾 Сохранить';

                    // Если ссылка уже была сохранена в локальное хранилище ранее
                    const currentSaved = getSavedUrls();
                    if (currentSaved.includes(url)) {
                        saveBtn.innerHTML = '✔️ Сохранено';
                        saveBtn.classList.add('saved');
                    }

                    saveBtn.onclick = (e) => {
                        e.preventDefault(); // Чтобы не переходило по ссылке
                        e.stopPropagation();
                        saveUrl(url);
                        saveBtn.innerHTML = '✔️ Сохранено';
                        saveBtn.classList.add('saved');
                    };

                    // Вставляем кнопку внутрь обертки постера, чтобы она красиво висела
                    const coverWrap = card.querySelector('.b-content__inline_item-cover');
                    if(coverWrap) {
                        coverWrap.style.position = 'relative'; // на всякий случай
                        coverWrap.appendChild(saveBtn);
                    }
                }
            }
            card.classList.add('cf-processed'); // Помечаем как проверенную
        });
    }

    // ==========================================
    // ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС (UI)
    // ==========================================
    function createUI() {
        // Плавающая кнопка
        const managerBtn = document.createElement('button');
        managerBtn.id = 'cf-manager-btn';
        managerBtn.innerText = '⚙️ CrazyFlix Manager';
        document.body.appendChild(managerBtn);

        // Модальное окно
        const modal = document.createElement('div');
        modal.id = 'cf-modal';
        modal.innerHTML = `
            <div id="cf-modal-content">
                <div id="cf-modal-header">
                    <h2>📥 Сохраненные ссылки (<span id="cf-count">0</span>)</h2>
                    <button id="cf-close-modal">✖</button>
                </div>
                <div id="cf-url-list"></div>
                <div class="cf-modal-footer">
                    <button id="cf-btn-copy" class="cf-action-btn cf-btn-copy">📋 Копировать все</button>
                    <button id="cf-btn-export" class="cf-action-btn cf-btn-export">💾 Выгрузить в .txt</button>
                    <button id="cf-btn-clear" class="cf-action-btn cf-btn-clear">🗑 Очистить базу</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // События кнопок модалки
        managerBtn.onclick = () => {
            renderModalList();
            modal.style.display = 'flex';
        };
        document.getElementById('cf-close-modal').onclick = () => modal.style.display = 'none';
        modal.onclick = (e) => { if(e.target === modal) modal.style.display = 'none'; };

        document.getElementById('cf-btn-clear').onclick = clearAllUrls;

        document.getElementById('cf-btn-copy').onclick = () => {
            const urls = getSavedUrls().join('\n');
            if(!urls) return alert("Список пуст!");
            navigator.clipboard.writeText(urls).then(() => {
                const btn = document.getElementById('cf-btn-copy');
                btn.innerText = "✔️ Скопировано!";
                setTimeout(() => btn.innerText = "📋 Копировать все", 2000);
            });
        };

        document.getElementById('cf-btn-export').onclick = () => {
            const urls = getSavedUrls().join('\n');
            if(!urls) return alert("Список пуст!");
            const blob = new Blob([urls], { type: 'text/plain' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'urls_to_download.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        };
    }

    // Отрисовка списка внутри модального окна
    function renderModalList() {
        const listDiv = document.getElementById('cf-url-list');
        const countSpan = document.getElementById('cf-count');
        const urls = getSavedUrls();

        listDiv.innerHTML = '';
        countSpan.innerText = urls.length;

        if (urls.length === 0) {
            listDiv.innerHTML = '<div style="text-align:center; color:#777; margin-top: 20px;">Нет сохраненных ссылок</div>';
            return;
        }

        urls.forEach(url => {
            const item = document.createElement('div');
            item.className = 'cf-url-item';

            const text = document.createElement('div');
            text.className = 'cf-url-text';
            text.innerText = url;

            const delBtn = document.createElement('button');
            delBtn.className = 'cf-delete-item';
            delBtn.innerText = 'Удалить';
            delBtn.onclick = () => removeUrl(url);

            item.appendChild(text);
            item.appendChild(delBtn);
            listDiv.appendChild(item);
        });
    }

    // ==========================================
    // ЗАПУСК И НАБЛЮДАТЕЛЬ (MutationObserver)
    // ==========================================

    // Запускаем сборку интерфейса
    createUI();

    // Запускаем получение БД (после загрузки вызовет processCards)
    fetchDatabase();

    // Наблюдатель за DOM (Следит за AJAX-подгрузкой новых фильмов при прокрутке страницы или переключении фильтров)
    const observer = new MutationObserver((mutations) => {
        let shouldProcess = false;
        for (const mutation of mutations) {
            if (mutation.addedNodes.length > 0) {
                shouldProcess = true;
                break;
            }
        }
        if (shouldProcess && knownIds.size > 0) {
            processCards();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

})();