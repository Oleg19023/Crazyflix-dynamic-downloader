// ==UserScript==
// @name         CrazyFlix Rezka DB Checker
// @namespace    http://tampermonkey.net/
// @version      2.7
// @description  Сканер Rezka.ag: Мгновенная загрузка (Кеш) + Кнопка ручного обновления БД.
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
// @connect      github.com
// @connect      githubusercontent.com
// ==/UserScript==

(function() {
    'use strict';

    const DB_URL = "https://github.com/Oleg19023/crazyflix-api.json/releases/download/v1.0.0/crazyflix-api.json";
    const STORE_KEY = 'crazyflix_saved_urls';
    const CACHE_KEY = 'crazyflix_db_cache';
    const CACHE_TIME = 60 * 60 * 1000; // Кеш живет 1 час (если не нажать кнопку "Обновить")

    let knownIds = new Set();
    let hideKnownMode = GM_getValue('cf_hide_known', false);
    let dbLoaded = false; 

    // ==========================================
    // СТИЛИ (CSS) 
    // ==========================================
    GM_addStyle(`
        .b-content__inline_item { 
            border: 3px solid transparent !important; 
            box-sizing: border-box !important; 
            position: relative !important;
            transition: border-color 0.3s;
        }
        
        .b-content__inline_item.cf-card-green { border-color: #4caf50 !important; opacity: 0.9; }
        .b-content__inline_item.cf-card-red { border-color: #ff4d4d !important; }
        
        .cf-hide-known .cf-card-green { display: none !important; }

        .cf-save-btn {
            position: absolute !important; 
            top: 5px !important; 
            right: 5px !important;
            z-index: 999 !important;
            background: #ff4d4d; 
            color: white; 
            border: none; 
            border-radius: 4px;
            padding: 4px 8px; 
            font-size: 11px; 
            font-weight: bold; 
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.6); 
            transition: 0.2s;
        }
        .cf-save-btn:hover { background: #ff1a1a; transform: scale(1.1); }
        .cf-save-btn.saved { background: #4caf50; }

        #cf-manager-btn {
            position: fixed; bottom: 20px; right: 20px; z-index: 10000;
            background: #00bcd4; color: white; border: none; border-radius: 50px;
            padding: 10px 20px; font-size: 14px; font-weight: bold; cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            display: flex; align-items: center; gap: 8px;
        }
        #cf-manager-badge { background: white; color: #00bcd4; border-radius: 10px; padding: 1px 6px; font-size: 11px; }

        #cf-modal {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 20000; justify-content: center; align-items: center;
        }
        #cf-modal-content {
            background: #1a1a1a; color: #fff; width: 600px; max-width: 95%; max-height: 85%;
            border-radius: 10px; padding: 20px; display: flex; flex-direction: column;
            border: 2px solid #00bcd4;
        }
        #cf-url-list { flex-grow: 1; overflow-y: auto; background: #000; padding: 10px; border-radius: 5px; margin: 15px 0; border: 1px solid #333; }
        .cf-url-item { font-size: 12px; padding: 5px 0; border-bottom: 1px solid #222; color: #00bcd4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .cf-modal-footer { display: flex; gap: 10px; flex-wrap: wrap; }
        .cf-action-btn { flex: 1; padding: 12px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; color: white; }
        .cf-btn-copy { background: #4caf50; } 
        .cf-btn-export { background: #2196f3; }
        .cf-btn-clear { background: #f44336; }
        .cf-btn-save-all { background: #ff9800; width: 100%; margin-bottom: 10px; }
        .cf-btn-sync { background: #673ab7; width: 100%; margin-bottom: 10px; }
    `);

    // ==========================================
    // ЛОГИКА ДАННЫХ
    // ==========================================
    
    function getSavedUrls() {
        return JSON.parse(GM_getValue(STORE_KEY, '[]'));
    }

    function updateBadge() {
        const badge = document.getElementById('cf-manager-badge');
        if(badge) badge.innerText = getSavedUrls().length;
    }

    function saveUrl(url) {
        let urls = getSavedUrls();
        const cleanUrl = url.split('?')[0].split('#')[0];
        if (!urls.includes(cleanUrl)) {
            urls.push(cleanUrl);
            GM_setValue(STORE_KEY, JSON.stringify(urls));
            updateBadge();
        }
    }

    // Загрузка базы с УМНЫМ КЕШИРОВАНИЕМ
    function fetchDatabase(forceRefresh = false) {
        const managerBtn = document.getElementById('cf-manager-btn');
        
        // Если не просили принудительно обновить, проверяем кеш
        if (!forceRefresh) {
            const cached = GM_getValue(CACHE_KEY, null);
            if (cached && (Date.now() - cached.time < CACHE_TIME)) {
                console.log("[CrazyFlix] БД мгновенно загружена из кеша браузера.");
                knownIds = new Set(cached.data);
                dbLoaded = true;
                if(managerBtn) managerBtn.innerHTML = `⚙️ Manager <span id="cf-manager-badge">${getSavedUrls().length}</span>`;
                applyMode();
                processCards();
                return;
            }
        }

        // Если кеш устарел или нажата кнопка "Обновить"
        if(managerBtn) managerBtn.innerHTML = `⏳ Скачивание БД...`;
        console.log("[CrazyFlix] Скачивание свежей БД из GitHub Releases...");

        GM_xmlhttpRequest({
            method: "GET",
            url: DB_URL + (forceRefresh ? "?t=" + Date.now() : ""), // Обход кеша провайдера
            nocache: true,
            onload: function(response) {
                dbLoaded = true; 
                
                if (response.status === 200 || response.status === 304) {
                    const text = response.responseText;
                    const regex = /(\d+)-[^\/"]+\.html/g;
                    let match;
                    knownIds.clear();
                    const idsArray = [];
                    while ((match = regex.exec(text)) !== null) {
                        knownIds.add(match[1]);
                        idsArray.push(match[1]);
                    }
                    
                    // Сохраняем новую базу в кеш браузера
                    GM_setValue(CACHE_KEY, { time: Date.now(), data: idsArray });
                    
                    console.log(`[CrazyFlix] Синхронизировано: ${knownIds.size} фильмов.`);
                    if(managerBtn) managerBtn.innerHTML = `⚙️ Manager <span id="cf-manager-badge">${getSavedUrls().length}</span>`;
                } else {
                    console.error("[CrazyFlix] Ошибка загрузки БД:", response.status);
                    if(managerBtn) managerBtn.innerHTML = `❌ Ошибка БД (${response.status}) <span id="cf-manager-badge">${getSavedUrls().length}</span>`;
                }
                
                applyMode();
                processCards(); 
            },
            onerror: function(err) {
                dbLoaded = true;
                console.error("[CrazyFlix] Сетевая ошибка при загрузке БД:", err);
                if(managerBtn) managerBtn.innerHTML = `❌ Нет сети <span id="cf-manager-badge">${getSavedUrls().length}</span>`;
                applyMode();
                processCards(); 
            }
        });
    }

    function applyMode() {
        if (hideKnownMode) document.body.classList.add('cf-hide-known');
        else document.body.classList.remove('cf-hide-known');
    }

    function extractIdFromUrl(url) {
        const match = url.match(/\/(\d+)-[^\/]+\.html/);
        return match ? match[1] : null;
    }

    function processCards() {
        const cards = document.querySelectorAll('.b-content__inline_item');
        const currentSaved = getSavedUrls();

        cards.forEach(card => {
            const linkElement = card.querySelector('.b-content__inline_item-link a');
            if (!linkElement || card.classList.contains('cf-processed')) return;

            const url = linkElement.href;
            const id = extractIdFromUrl(url);

            if (id) {
                if (knownIds.has(id)) {
                    card.classList.add('cf-card-green');
                } else {
                    card.classList.add('cf-card-red');
                    const cover = card.querySelector('.b-content__inline_item-cover');
                    if (cover) {
                        const btn = document.createElement('button');
                        btn.className = 'cf-save-btn';
                        const isAlreadySaved = currentSaved.includes(url.split('?')[0]);
                        btn.innerHTML = isAlreadySaved ? '✔️' : '💾 Save';
                        if (isAlreadySaved) btn.classList.add('saved');
                        
                        btn.onclick = (e) => {
                            e.preventDefault(); e.stopPropagation();
                            saveUrl(url);
                            btn.innerHTML = '✔️'; btn.classList.add('saved');
                        };
                        cover.appendChild(btn);
                    }
                }
            }
            card.classList.add('cf-processed');
        });
    }

    function createUI() {
        const managerBtn = document.createElement('button');
        managerBtn.id = 'cf-manager-btn';
        managerBtn.innerHTML = `⚙️ Manager <span id="cf-manager-badge">0</span>`;
        document.body.appendChild(managerBtn);

        const modal = document.createElement('div');
        modal.id = 'cf-modal';
        modal.innerHTML = `
            <div id="cf-modal-content">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h2 style="margin:0; color:#00bcd4; font-size:20px;">CrazyFlix Panel</h2>
                    <button id="cf-close" style="background:none; border:none; color:#ff4d4d; font-size:30px; cursor:pointer;">&times;</button>
                </div>
                <div style="margin: 15px 0; font-size: 14px; background:#333; padding:10px; border-radius:5px;">
                    <input type="checkbox" id="cf-hide-known-chk" ${hideKnownMode ? 'checked' : ''}>
                    <label for="cf-hide-known-chk" style="cursor:pointer; user-select:none;">Скрывать то, что уже есть в базе</label>
                </div>
                <div id="cf-url-list"></div>
                <button id="cf-save-all" class="cf-action-btn cf-btn-save-all">⚡ Сохранить всё красное со страницы</button>
                <button id="cf-sync-db" class="cf-action-btn cf-btn-sync">🔄 Обновить базу данных с GitHub</button>
                <div class="cf-modal-footer">
                    <button id="cf-copy" class="cf-action-btn cf-btn-copy">📋 Копировать</button>
                    <button id="cf-export" class="cf-action-btn cf-btn-export">💾 .TXT</button>
                    <button id="cf-clear" class="cf-action-btn cf-btn-clear">🗑 Очистить</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        managerBtn.onclick = () => { renderList(); modal.style.display = 'flex'; };
        document.getElementById('cf-close').onclick = () => modal.style.display = 'none';
        
        document.getElementById('cf-hide-known-chk').onchange = (e) => {
            hideKnownMode = e.target.checked;
            GM_setValue('cf_hide_known', hideKnownMode);
            applyMode();
        };

        // Кнопка обновления БД вручную
        document.getElementById('cf-sync-db').onclick = () => {
            fetchDatabase(true); // Запускаем принудительное скачивание
            modal.style.display = 'none'; // Закрываем окно, чтобы видеть процесс на кнопке
        };

        document.getElementById('cf-save-all').onclick = () => {
            const redCards = document.querySelectorAll('.cf-card-red');
            let added = 0;
            redCards.forEach(card => {
                const link = card.querySelector('.b-content__inline_item-link a');
                const btn = card.querySelector('.cf-save-btn');
                if(link && btn && !btn.classList.contains('saved')) {
                    saveUrl(link.href);
                    btn.innerHTML = '✔️'; btn.classList.add('saved');
                    added++;
                }
            });
            renderList();
            updateBadge();
        };

        document.getElementById('cf-clear').onclick = () => {
            if(confirm("Очистить список сохраненных ссылок?")) {
                GM_setValue(STORE_KEY, '[]');
                renderList();
                updateBadge();
                document.querySelectorAll('.cf-save-btn').forEach(b => {
                    b.innerHTML = '💾 Save';
                    b.classList.remove('saved');
                });
            }
        };

        document.getElementById('cf-copy').onclick = () => {
            const text = getSavedUrls().join('\n');
            navigator.clipboard.writeText(text).then(() => alert("Скопировано в буфер!"));
        };

        document.getElementById('cf-export').onclick = () => {
            const text = getSavedUrls().join('\n');
            if(!text) return alert("Список пуст!");
            const blob = new Blob([text], {type: 'text/plain'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'urls_to_download.txt';
            a.click();
        };

        updateBadge();
    }

    function renderList() {
        const list = document.getElementById('cf-url-list');
        const urls = getSavedUrls();
        list.innerHTML = urls.length ? '' : '<p style="text-align:center; color:#777;">Список пуст</p>';
        urls.forEach(url => {
            const item = document.createElement('div');
            item.className = 'cf-url-item';
            item.innerText = url;
            list.appendChild(item);
        });
    }

    createUI();
    fetchDatabase();

    const observer = new MutationObserver(() => {
        if (dbLoaded) processCards();
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();