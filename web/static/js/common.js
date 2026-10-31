// Umumiy yordamchilar: web sayt ham, admin panel ham foydalanadi
const tg = (window.Telegram && window.Telegram.WebApp) || null;
if (tg) { try { tg.ready(); tg.expand(); tg.setHeaderColor && tg.setHeaderColor('#060a13'); tg.setBackgroundColor && tg.setBackgroundColor('#060a13'); } catch (e) {} }

const $ = (id) => document.getElementById(id);

const store = {
    get(k, d = null) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    sget(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    sset(k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} },
};

// ---- HTML xavfsizligi: foydalanuvchi/admin kiritgan har qanday matn esc() orqali chiqadi
function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ---- Custom ikonlar (SVG sprite, Telegram stikeri emas)
function icon(name, cls = '') {
    return `<svg class="ic ${cls}" aria-hidden="true"><use href="/static/img/icons.svg#i-${name}"/></svg>`;
}
function categoryIcon(name) {
    const n = String(name || '').toLowerCase();
    if (/choy|чай|tea|ichimlik|напит|drink/.test(n)) return 'tea';
    if (/plov|osh|плов|pilaf/.test(n)) return 'plov';
    return 'menu';
}

// ---- Til
let LANG = 'uz';
let DICT = {};
const t = (k) => DICT[k] || k;
async function loadLang(lang) {
    LANG = ['uz', 'ru', 'en'].includes(lang) ? lang : 'uz';
    try { DICT = await (await fetch(`/api/i18n/${LANG}`)).json(); } catch (e) { DICT = {}; }
    store.set('cp_lang', LANG);
    document.documentElement.lang = LANG;
    applyI18n();
}
function applyI18n(root = document) {
    root.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    root.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
}
function guessLang() {
    const saved = store.get('cp_lang');
    if (saved) return saved;
    const code = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.language_code) || navigator.language || 'uz';
    const c = code.slice(0, 2).toLowerCase();
    return ['uz', 'ru', 'en'].includes(c) ? c : (['be', 'kk', 'uk', 'ky', 'tg'].includes(c) ? 'ru' : 'en');
}

// ---- Format
const nf = new Intl.NumberFormat('ru-RU');
const fmt = (n) => nf.format(Math.round(Number(n) || 0));
const money = (n) => `${fmt(n)} ${t('w_currency')}`;
function parseDate(s) { return new Date(String(s).replace(' ', 'T') + 'Z'); }
function fmtDate(s) {
    const d = parseDate(s);
    if (isNaN(d)) return s || '';
    const opts = LANG === 'en'
        ? { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }
        : { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    return d.toLocaleString(LANG === 'en' ? 'en-GB' : 'ru-RU', opts);   // uz va ru: 25.10.2026, 17:42
}

// ---- API
const devUser = new URLSearchParams(location.search).get('dev_user');
if (devUser) store.sset('cp_dev_user', devUser);

async function api(path, { method = 'GET', body, formData } = {}) {
    const headers = { 'X-Init-Data': (tg && tg.initData) || '' };
    const du = store.sget('cp_dev_user');
    if (du) headers['X-Dev-User'] = du;
    const at = store.sget('cp_admin_token');
    if (at) headers['X-Admin-Token'] = at;
    let payload;
    if (formData) payload = formData;
    else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }
    const res = await fetch(path, { method, headers, body: payload });
    let data = null;
    try { data = await res.json(); } catch (e) {}
    if (!res.ok) {
        const err = new Error((data && data.detail) || res.statusText);
        err.status = res.status;
        throw err;
    }
    return data;
}

// ---- Toast
function toast(msg, type = 'ok') {
    let wrap = document.getElementById('toasts');
    if (!wrap) { wrap = document.createElement('div'); wrap.id = 'toasts'; wrap.className = 'toast-wrap'; document.body.appendChild(wrap); }
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `${icon(type === 'ok' ? 'check' : 'x')}<span>${esc(msg)}</span>`;
    wrap.appendChild(el);
    if (tg && tg.HapticFeedback) { try { tg.HapticFeedback.notificationOccurred(type === 'ok' ? 'success' : 'error'); } catch (e) {} }
    setTimeout(() => el.remove(), 2400);
}

// Rasm yoki placeholder
function imgTag(url, alt = '') {
    return url ? `<img src="${esc(url)}" alt="${esc(alt)}" loading="lazy" onerror="this.style.display='none'">`
               : `<div class="ph">${icon('plov', 'xl')}</div>`;
}

// ============================================================ sheet
function openSheet(html, { flush = false } = {}) {
    closeSheet();
    const root = $('sheet-root');
    root.innerHTML = `<div class="overlay" id="overlay"><div class="sheet ${flush ? 'flush' : ''}" role="dialog" aria-modal="true">
        <button class="sheet-close" aria-label="Close">${icon('x')}</button>${html}</div></div>`;
    const ov = $('overlay');
    ov.onclick = (e) => { if (e.target === ov) closeSheet(); };
    ov.querySelector('.sheet-close').onclick = closeSheet;
    document.body.style.overflow = 'hidden';
    return ov.querySelector('.sheet');
}
function closeSheet() {
    $('sheet-root').innerHTML = '';
    document.body.style.overflow = '';
}


// iOS Safari: pinch-zoom va "double-tap zoom" ni o'chirish
['gesturestart', 'gesturechange', 'gestureend'].forEach(ev => document.addEventListener(ev, e => e.preventDefault(), { passive: false }));
