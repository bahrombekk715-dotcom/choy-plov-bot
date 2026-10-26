// Choy Plov — sayt (Telegram Web App). Umumiy yordamchilar common.js da.
const S = {
    me: { telegram: false },
    menu: { categories: [], products: [], addons: [], favorites: new Set() },
    cart: [],                                  // [{pid, qty, addons: [addonId...]}]
    cat: 'all',
    tab: 'menu',
    filter: { status: '', from: '', to: '' },
};
const view = $('view');

// ============================================================ ishga tushirish
(async function boot() {
    view.innerHTML = '<div class="skeleton" style="height:48px;margin:14px 0"></div><div class="pgrid"><div class="skeleton" style="height:220px"></div><div class="skeleton" style="height:220px"></div></div>';
    // profil va menyu bir vaqtda yuklanadi (ketma-ket emas) — sayt tezroq ochiladi
    const [me] = await Promise.all([api('/api/me').catch(() => ({ telegram: false })), loadMenu()]);
    S.me = me;
    await loadLang(S.me.language || guessLang());
    loadCart();
    pruneCart();
    bindShell();
    renderAll();
})();

async function loadMenu() {
    try {
        const m = await api('/api/menu');
        S.menu = { categories: m.categories, products: m.products, addons: m.addons, favorites: new Set(m.favorites) };
    } catch (e) { toast(t('w_error'), 'err'); }
}

function bindShell() {
    document.querySelectorAll('#tabs button[data-tab]').forEach(b => b.onclick = () => go(b.dataset.tab));
    $('cart-tab').onclick = openCart;
    $('lang-btn').onclick = openLangSheet;
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
}
function go(tab) { S.tab = tab; renderAll(); window.scrollTo({ top: 0 }); }
function renderAll() {
    document.querySelectorAll('#tabs button[data-tab]').forEach(b => b.classList.toggle('active', b.dataset.tab === S.tab));
    applyI18n();
    $('lang-code').textContent = LANG.toUpperCase();
    ({ menu: renderMenu, favorites: renderFavorites, orders: renderOrders, profile: renderProfile })[S.tab]();
    renderCartFab();
}

// ============================================================ yordamchilar
const product = (id) => S.menu.products.find(p => p.id === id);
const addon = (id) => S.menu.addons.find(a => a.id === id);
const addonOn = (id) => { const a = addon(id); return !!(a && a.is_available); };
const addonName = (a) => (a.code && DICT['w_addon_' + a.code]) || a.name;
const statusLabel = (s) => t('w_status_' + s);
const STATUS_ICON = { pending: 'clock', completed: 'check', delivered: 'check', cancelled: 'x' };
const statusBadge = (s) => `<span class="status ${esc(s)}">${esc(statusLabel(s))}</span>`;
const UNITS = { gr: { uz: 'gr', ru: 'г', en: 'g' }, dona: { uz: 'dona', ru: 'шт', en: 'pcs' } };
const unitText = (u) => String(u || '').replace(/gr|dona/, m => UNITS[m][LANG]);
const addonLabel = (a) => `${addonName(a)}${a.unit ? ' ' + unitText(a.unit) : ''}`;
// qo'shimchalar: [{id, qty}] — har biridan istalgancha porsiya
const addonsSum = (list) => list.reduce((s, x) => s + (addon(x.id) ? addon(x.id).price * x.qty : 0), 0);
const lineUnit = (p, list) => p.price + addonsSum(list);
const addonsKey = (list) => JSON.stringify([...list].sort((a, b) => a.id - b.id).map(x => [x.id, x.qty]));
const addonsText = (list) => list.filter(x => addon(x.id)).map(x => `${addonLabel(addon(x.id))} ×${x.qty}`).join(', ');

function gate() {
    // Telegramsiz yoki ro'yxatdan o'tmagan foydalanuvchi uchun xabar
    if (S.me.registered) return null;
    const msg = S.me.telegram ? t('w_need_register') : t('w_need_telegram');
    return `<div class="empty">${icon('user', 'xl')}<p>${esc(msg)}</p></div>`;
}
function requireUser() {
    if (S.me.registered) return true;
    toast(S.me.telegram ? t('w_need_register') : t('w_need_telegram'), 'err');
    return false;
}

// ============================================================ savat
function loadCart() {
    try { S.cart = JSON.parse(store.get('cp_cart', '[]')) || []; } catch (e) { S.cart = []; }
    // eski format (faqat id raqamlari) -> {id, qty}
    S.cart.forEach(i => { i.addons = (i.addons || []).map(x => typeof x === 'object' ? x : { id: x, qty: 1 }); });
}
function saveCart() { store.set('cp_cart', JSON.stringify(S.cart)); renderCartFab(); }
function pruneCart() {
    // menyuda yo'q yoki to'xtatilgan mahsulot, o'chirilgan qo'shimchalar savatdan olib tashlanadi
    S.cart = S.cart.filter(i => { const p = product(i.pid); return p && p.is_available && i.qty > 0; })
        .map(i => ({ ...i, addons: i.addons.filter(x => addonOn(x.id)) }));
    saveCart();
}
const cartCount = () => S.cart.reduce((s, i) => s + i.qty, 0);
const cartTotal = () => S.cart.reduce((s, i) => s + lineUnit(product(i.pid), i.addons) * i.qty, 0);
function renderCartFab() {
    const n = cartCount();
    $('cart-count').classList.toggle('hidden', n === 0);
    $('cart-count').textContent = n;
}
function addToCart(pid, qty, addons) {
    const key = addonsKey(addons);
    const ex = S.cart.find(i => i.pid === pid && addonsKey(i.addons) === key);
    if (ex) ex.qty = Math.min(50, ex.qty + qty); else S.cart.push({ pid, qty, addons: addons.map(x => ({ id: x.id, qty: x.qty })) });
    saveCart();
}

// ============================================================ menyu
function productCard(p) {
    const fav = S.menu.favorites.has(p.id);
    return `<div class="pcard ${p.is_available ? '' : 'off'}" data-pid="${p.id}" role="button" tabindex="0">
        <button class="fav-btn ${fav ? 'on' : ''}" data-fav="${p.id}" aria-label="${esc(t('w_favorites'))}">${icon(fav ? 'heart-fill' : 'heart')}</button>
        <div class="thumb">${imgTag(p.images[0] && p.images[0].url, p.name)}${p.is_available ? '' : `<span class="off-tag">${esc(t('w_unavailable'))}</span>`}</div>
        <div class="body"><h3>${esc(p.name)}</h3>
            <div class="row"><span class="price">${esc(money(p.price))}</span>${p.is_available ? `<span class="add">${icon('plus')}</span>` : ''}</div></div></div>`;
}
function bindCards(root) {
    root.querySelectorAll('.pcard').forEach(c => {
        const open = () => openProduct(+c.dataset.pid);
        c.onclick = open;
        c.onkeydown = (e) => { if (e.key === 'Enter') open(); };
    });
    root.querySelectorAll('[data-fav]').forEach(b => b.onclick = (e) => { e.stopPropagation(); toggleFav(+b.dataset.fav); });
}

function renderMenu() {
    const { categories, products } = S.menu;
    if (!categories.length) { view.innerHTML = `<div class="empty">${icon('menu', 'xl')}<p>${esc(t('w_no_categories'))}</p></div>`; return; }
    if (S.cat !== 'all' && !categories.some(c => c.id === S.cat)) S.cat = 'all';
    const list = S.cat === 'all' ? products : products.filter(p => p.category_id === S.cat);
    const name = (S.me.first_name || (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.first_name) || '').trim();
    view.innerHTML = `<section class="welcome"><div><h2>${esc(name ? t('w_welcome').replace('{name}', name) : t('w_welcome').replace(', {name}', ''))}</h2><p>${esc(t('w_welcome_sub'))}</p></div>${icon('plov', 'bg')}</section>
        <div class="chips" id="cats">
            <button class="chip ${S.cat === 'all' ? 'active' : ''}" data-c="all">${esc(t('w_all'))}</button>
            ${categories.map(c => `<button class="chip ${S.cat === c.id ? 'active' : ''}" data-c="${c.id}">${icon(categoryIcon(c.name))}${esc(c.name)}</button>`).join('')}</div>
        ${list.length ? `<div class="pgrid">${list.map(productCard).join('')}</div>` : `<div class="empty">${icon('plov', 'xl')}<p>${esc(t('w_no_products'))}</p></div>`}`;
    view.querySelectorAll('#cats .chip').forEach(b => b.onclick = () => { S.cat = b.dataset.c === 'all' ? 'all' : +b.dataset.c; renderMenu(); });
    bindCards(view);
}

async function toggleFav(pid) {
    if (!requireUser()) return;
    try {
        const r = await api(`/api/favorites/${pid}/toggle`, { method: 'POST' });
        r.favorite ? S.menu.favorites.add(pid) : S.menu.favorites.delete(pid);
        if (S.tab === 'favorites') renderFavorites();
        else if (S.tab === 'menu') renderMenu();
        const btn = document.querySelector('#sheet-root [data-fav]');
        if (btn) { btn.classList.toggle('on', r.favorite); btn.innerHTML = icon(r.favorite ? 'heart-fill' : 'heart'); }
    } catch (e) { toast(t('w_error'), 'err'); }
}

// ============================================================ galereya
function galleryHTML(images, pid) {
    const fav = S.menu.favorites.has(pid);
    const favBtn = `<button class="fav-btn on-gallery ${fav ? 'on' : ''}" data-fav="${pid}" aria-label="${esc(t('w_favorites'))}">${icon(fav ? 'heart-fill' : 'heart')}</button>`;
    if (!images.length) return `<div class="gallery"><div class="g-slide">${imgTag(null)}</div>${favBtn}</div>`;
    const many = images.length > 1;
    return `<div class="gallery"><div class="g-track" id="g-track">${images.map(i => `<div class="g-slide"><img src="${esc(i.url)}" alt="" loading="lazy"></div>`).join('')}</div>
        ${many ? `<button class="g-arrow l" data-dir="-1" aria-label="prev">${icon('chevron')}</button><button class="g-arrow r" data-dir="1" aria-label="next">${icon('chevron')}</button>
        <div class="g-dots" id="g-dots">${images.map((_, k) => `<i class="${k ? '' : 'on'}"></i>`).join('')}</div>` : ''}${favBtn}</div>
        ${many ? `<div class="g-thumbs" id="g-thumbs">${images.map((i, k) => `<button class="${k ? '' : 'on'}" data-k="${k}"><img src="${esc(i.url)}" alt=""></button>`).join('')}</div>` : ''}`;
}
function bindGallery(root) {
    const track = root.querySelector('#g-track');
    if (!track) return;
    const dots = root.querySelectorAll('#g-dots i'), thumbs = root.querySelectorAll('#g-thumbs button');
    const slideTo = (k) => track.scrollTo({ left: k * track.clientWidth, behavior: 'smooth' });
    track.addEventListener('scroll', debounce(() => {
        const k = Math.round(track.scrollLeft / track.clientWidth);
        dots.forEach((d, i) => d.classList.toggle('on', i === k));
        thumbs.forEach((b, i) => b.classList.toggle('on', i === k));
    }, 40));
    thumbs.forEach(b => b.onclick = () => slideTo(+b.dataset.k));
    root.querySelectorAll('.g-arrow').forEach(b => b.onclick = () => {
        const k = Math.round(track.scrollLeft / track.clientWidth) + +b.dataset.dir;
        slideTo(Math.max(0, Math.min(dots.length - 1, k)));
    });
}
function debounce(fn, ms) { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; }

// ============================================================ mahsulot oynasi
function openProduct(pid) {
    const p = product(pid);
    if (!p) return;
    let qty = 1;
    const chosen = new Map();                  // addonId -> porsiyalar soni
    const sh = openSheet(`${galleryHTML(p.images, pid)}
        <div class="p-head"><h2>${esc(p.name)}</h2><span class="p-price">${esc(money(p.price))}</span></div>
        ${p.description ? `<p class="p-desc">${esc(p.description)}</p>` : ''}
        ${S.menu.addons.length ? `<div class="block-title">${esc(t('w_addons'))}</div>
            ${S.menu.addons.map(a => a.is_available
                ? `<div class="addon" data-a="${a.id}">${a.code ? icon(a.code) : icon('plus')}<span>${esc(addonLabel(a))}<small>+${esc(money(a.price))}</small></span>
                <div class="mini-qty"><button data-ad="-1" aria-label="-">${icon('minus')}</button><b>0</b><button data-ad="1" aria-label="+">${icon('plus')}</button></div></div>`
                : `<div class="addon off">${a.code ? icon(a.code) : icon('plus')}<span>${esc(addonLabel(a))}<small>${esc(t('w_unavailable'))}</small></span></div>`).join('')}` : ''}
        <div class="buy-row"><div class="qty"><button data-q="-1" aria-label="-">${icon('minus')}</button><b id="q">1</b><button data-q="1" aria-label="+">${icon('plus')}</button></div>
            <button class="btn primary" id="add" ${p.is_available ? '' : 'disabled'}>${icon('cart')}<span id="add-label"></span></button></div>`, { flush: true });
    const list = () => [...chosen].map(([id, q]) => ({ id, qty: q }));
    const refresh = () => {
        $('q').textContent = qty;
        $('add-label').textContent = p.is_available ? `${t('w_add_to_cart')} · ${money(lineUnit(p, list()) * qty)}` : t('w_unavailable');
    };
    sh.querySelectorAll('[data-q]').forEach(b => b.onclick = () => { qty = Math.max(1, Math.min(50, qty + +b.dataset.q)); refresh(); });
    sh.querySelectorAll('.addon[data-a]').forEach(row => row.querySelectorAll('[data-ad]').forEach(b => b.onclick = () => {
        const id = +row.dataset.a, q = Math.max(0, Math.min(20, (chosen.get(id) || 0) + +b.dataset.ad));
        q ? chosen.set(id, q) : chosen.delete(id);
        row.querySelector('.mini-qty b').textContent = q;
        row.classList.toggle('on', q > 0); refresh();
    }));
    sh.querySelectorAll('[data-fav]').forEach(b => b.onclick = () => toggleFav(pid));
    $('add').onclick = () => { addToCart(pid, qty, list()); closeSheet(); toast(t('w_added')); };
    bindGallery(sh);
    refresh();
}

// ============================================================ savat oynasi
function openCart() {
    if (!S.cart.length) { toast(t('w_cart_empty'), 'err'); return; }
    const sh = openSheet(`<h2>${icon('cart')} ${esc(t('w_cart'))}</h2><div id="lines"></div>
        <div class="total-row"><span>${esc(t('w_total'))}</span><b id="c-total"></b></div>
        <button class="btn primary block" id="go" style="margin-top:16px">${esc(t('w_checkout'))}</button>`);
    const draw = () => {
        if (!S.cart.length) { closeSheet(); return; }
        $('lines').innerHTML = S.cart.map((i, k) => {
            const p = product(i.pid);
            return `<div class="cart-line"><div class="thumb-sm">${imgTag(p.images[0] && p.images[0].url, p.name)}</div>
                <div class="info"><b>${esc(p.name)}</b>${i.addons.length ? `<small>+ ${esc(addonsText(i.addons))}</small>` : ''}
                <div class="sum">${esc(money(lineUnit(p, i.addons) * i.qty))}</div></div>
                <div class="qty"><button data-k="${k}" data-d="-1" aria-label="-">${icon('minus')}</button><b>${i.qty}</b><button data-k="${k}" data-d="1" aria-label="+">${icon('plus')}</button></div>
                <button class="icon-btn" data-rm="${k}" aria-label="${esc(t('w_remove'))}">${icon('trash')}</button></div>`;
        }).join('');
        $('c-total').textContent = money(cartTotal());
        sh.querySelectorAll('[data-d]').forEach(b => b.onclick = () => {
            const it = S.cart[+b.dataset.k]; it.qty = Math.max(1, Math.min(50, it.qty + +b.dataset.d)); saveCart(); draw();
        });
        sh.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { S.cart.splice(+b.dataset.rm, 1); saveCart(); draw(); });
    };
    $('go').onclick = openCheckout;
    draw();
}

// ============================================================ buyurtma berish
async function openCheckout() {
    if (!requireUser()) return;
    let addrs = [];
    try { addrs = await api('/api/addresses'); } catch (e) {}
    const def = addrs.find(a => a.is_default) || addrs[0];
    const sh = openSheet(`<h2>${icon('orders')} ${esc(t('w_checkout'))}</h2>
        <div class="field"><label class="label" for="f-phone">${esc(t('w_phone'))}</label><input id="f-phone" type="tel" inputmode="tel" placeholder="+998 90 123 45 67" value="${esc(S.me.phone_number || '')}"></div>
        <span class="label">${esc(t('w_address'))}</span>
        ${addrs.length ? `<div class="addr-chips" id="addr-chips">${addrs.map(a => `<button class="chip sm ${def && def.id === a.id ? 'active' : ''}" data-aid="${a.id}">${icon('location')}${esc(a.title)}</button>`).join('')}</div>` : ''}
        <div class="field"><textarea id="f-addr" rows="2" placeholder="${esc(t('w_address_ph'))}" aria-label="${esc(t('w_address'))}">${esc(def ? def.address : '')}</textarea></div>
        <label class="check" style="margin:-4px 0 14px"><input type="checkbox" id="f-save"> ${esc(t('w_save_address'))}</label>
        <div class="field hidden" id="f-title-wrap"><input id="f-title" maxlength="40" placeholder="${esc(t('w_address_title'))}" aria-label="${esc(t('w_address_title'))}"></div>
        <div class="field"><label class="label" for="f-comment">${esc(t('w_comment'))}</label><textarea id="f-comment" rows="2" maxlength="500"></textarea></div>
        <div class="total-row"><span>${esc(t('w_total'))}</span><b>${esc(money(cartTotal()))}</b></div>
        <button class="btn primary block" id="place" style="margin-top:16px">${esc(t('w_place_order'))}</button>`);
    sh.querySelectorAll('[data-aid]').forEach(b => b.onclick = () => {
        sh.querySelectorAll('[data-aid]').forEach(x => x.classList.toggle('active', x === b));
        $('f-addr').value = addrs.find(a => a.id === +b.dataset.aid).address;
    });
    $('f-save').onchange = (e) => $('f-title-wrap').classList.toggle('hidden', !e.target.checked);
    $('place').onclick = async () => {
        const phone = $('f-phone').value.trim(), address = $('f-addr').value.trim();
        if (phone.replace(/\D/g, '').length < 9) { toast(t('w_fill_phone'), 'err'); return; }
        if (address.length < 3) { toast(t('w_fill_address'), 'err'); return; }
        $('place').disabled = true;
        try {
            const r = await api('/api/order', { method: 'POST', body: {
                phone, address, comment: $('f-comment').value.trim() || null,
                cart: S.cart.map(i => ({ product_id: i.pid, quantity: i.qty, addons: i.addons.map(x => ({ id: x.id, qty: x.qty })) })) } });
            if ($('f-save').checked && !addrs.some(a => a.address === address)) {
                try { await api('/api/addresses', { method: 'POST', body: { title: $('f-title').value.trim() || t('w_new_address'), address, is_default: !addrs.length } }); } catch (e) {}
            }
            S.cart = []; saveCart();
            orderDone(r.order_id);
        } catch (e) {
            $('place').disabled = false;
            if (e.message === 'unavailable' || e.message === 'bad_addon') { await loadMenu(); pruneCart(); closeSheet(); toast(t('w_unavailable'), 'err'); renderAll(); }
            else toast(t('w_error'), 'err');
        }
    };
}
function orderDone(id) {
    const sh = openSheet(`<div class="success"><div class="big">${icon('check')}</div><h2>${esc(t('w_order_done'))}</h2>
        <p>${esc(t('w_order_number'))}</p><div class="num">#${id}</div><p>${esc(t('w_order_done_hint'))}</p>
        <button class="btn primary block" id="ok" style="margin-top:18px">${esc(t('w_ok'))}</button></div>`);
    $('ok').onclick = () => { closeSheet(); go('orders'); };
    sh.querySelector('.sheet-close').onclick = () => { closeSheet(); renderAll(); };
}

// ============================================================ sevimlilar
async function renderFavorites() {
    const g = gate();
    if (g) { view.innerHTML = `<h1 class="page-title">${esc(t('w_favorites'))}</h1>${g}`; return; }
    view.innerHTML = `<h1 class="page-title">${esc(t('w_favorites'))}</h1><div class="skeleton" style="height:200px"></div>`;
    try {
        const items = await api('/api/favorites');
        S.menu.favorites = new Set(items.map(p => p.id));
        // eng so'nggi mavjudlik holati menyudan olinadi
        const list = items.map(p => product(p.id) || p);
        view.innerHTML = `<h1 class="page-title">${esc(t('w_favorites'))}</h1>` + (list.length
            ? `<div class="pgrid" style="margin-top:0">${list.map(productCard).join('')}</div>`
            : `<div class="empty">${icon('heart', 'xl')}<p>${esc(t('w_no_favorites'))}</p></div>`);
        bindCards(view);
    } catch (e) { view.innerHTML = `<div class="empty">${icon('x', 'xl')}<p>${esc(t('w_error'))}</p></div>`; }
}

// ============================================================ buyurtmalar tarixi
async function renderOrders() {
    const g = gate();
    const head = `<h1 class="page-title">${esc(t('w_orders'))}</h1>`;
    if (g) { view.innerHTML = head + g; return; }
    view.innerHTML = `${head}<div id="o-list"><div class="skeleton" style="height:140px"></div></div>`;
    loadOrders();
}
async function loadOrders() {
    const box = $('o-list');
    if (!box) return;
    try {
        const orders = await api('/api/orders');
        if (!$('o-list')) return;
        box.innerHTML = orders.length ? orders.map(o => `<button class="card order-card" data-o="${o.id}"><div class="top"><b>${esc(t('w_order_number'))} #${o.id}</b>${statusBadge(o.status)}</div>
            <div class="meta">${icon('calendar')} ${esc(fmtDate(o.created_at))}</div>
            <div class="thumbs">${o.items.slice(0, 5).map(i => `<span class="mini-thumb">${imgTag(i.image_url, i.product_name)}</span>`).join('')}${o.items.length > 5 ? `<span class="mini-thumb more">+${o.items.length - 5}</span>` : ''}</div>
            <div class="foot"><b>${esc(money(o.total_price))}</b><span class="muted go">${icon('chevron')}</span></div></button>`).join('')
            : `<div class="empty">${icon('orders', 'xl')}<p>${esc(t('w_no_orders'))}</p></div>`;
        box.querySelectorAll('[data-o]').forEach(b => b.onclick = () => openOrderDetail(orders.find(o => o.id === +b.dataset.o)));
    } catch (e) { box.innerHTML = `<div class="empty">${icon('x', 'xl')}<p>${esc(t('w_error'))}</p></div>`; }
}
function openOrderDetail(o) {
    openSheet(`<h2>${esc(t('w_order_number'))} #${o.id} ${statusBadge(o.status)}</h2>
        <div class="meta">${icon('calendar')} ${esc(fmtDate(o.created_at))}</div>
        <div class="meta">${icon('location')} ${esc(o.address)}</div>
        ${o.comment ? `<div class="meta">${icon('bell')} ${esc(o.comment)}</div>` : ''}
        <div class="block-title">${esc(t('w_items'))}</div>
        ${o.items.map(i => `<div class="od-item"><span class="mini-thumb">${imgTag(i.image_url, i.product_name)}</span>
            <div class="info"><b>${esc(i.product_name)} × ${i.quantity}</b>${i.addons.length ? `<small>+ ${i.addons.map(a => esc(`${a.code && DICT['w_addon_' + a.code] || a.name}${a.unit ? ' ' + unitText(a.unit) : ''} ×${a.qty}`)).join(', ')}</small>` : ''}</div>
            <b class="sum">${esc(money(i.price))}</b></div>`).join('')}
        <div class="total-row"><span>${esc(t('w_total'))}</span><b>${esc(money(o.total_price))}</b></div>`);
}

// ============================================================ profil
async function renderProfile() {
    const g = gate();
    const head = `<h1 class="page-title">${esc(t('w_profile'))}</h1>`;
    if (g) { view.innerHTML = head + g; return; }
    const me = S.me, st = me.stats || { orders: 0, spent: 0 };
    // Telegramdagi profil rasmi (bo'lmasa yoki yuklanmasa ismning bosh harfi ko'rinadi)
    const photo = tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.photo_url;
    let addrs = [];
    try { addrs = await api('/api/addresses'); } catch (e) {}
    view.innerHTML = `<div class="profile-head"><div class="avatar"><span>${esc((me.first_name || '?').trim().charAt(0).toUpperCase())}</span>${photo ? `<img src="${esc(photo)}" alt="" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}</div>
            <div><h2>${esc(me.first_name || '')}</h2><div class="muted">${me.username ? '@' + esc(me.username) : ''}</div>
            ${me.phone_number ? `<div class="meta" style="margin:4px 0 0">${icon('phone')} ${esc(me.phone_number)}</div>` : ''}</div></div>
        <div class="stat-grid">
            <div class="stat"><div class="row"><i class="tile blue">${icon('orders')}</i><span>${esc(t('w_stat_orders'))}</span></div><b>${fmt(st.orders)}</b></div>
            <div class="stat"><div class="row"><i class="tile pink">${icon('heart')}</i><span>${esc(t('w_stat_favs'))}</span></div><b>${S.menu.favorites.size}</b></div>
            <div class="stat"><div class="row"><i class="tile amber">${icon('location')}</i><span>${esc(t('w_stat_addrs'))}</span></div><b>${addrs.length}</b></div></div>
        <div class="meta" style="margin:0 0 16px">${icon('calendar')} ${esc(t('w_member_since'))}: ${esc(fmtDate(me.created_at))}</div>
        <div class="sec-head"><h3>${esc(t('w_addresses'))}</h3><button class="btn sm" id="addr-add">${icon('plus')} ${esc(t('w_add_address'))}</button></div>
        <div id="addr-list">${addrs.length ? addrs.map(a => `<div class="card addr-card">${icon('location', 'lg')}
            <div class="txt"><b>${esc(a.title)} ${a.is_default ? `<span class="tag-default">${esc(t('w_default'))}</span>` : ''}</b><p>${esc(a.address)}</p>
                ${a.is_default ? '' : `<button class="btn sm" data-def="${a.id}" style="margin-top:8px">${esc(t('w_make_default'))}</button>`}</div>
            <div class="addr-actions"><button class="icon-btn" data-edit="${a.id}" aria-label="${esc(t('w_edit'))}">${icon('edit')}</button>
                <button class="icon-btn" data-del="${a.id}" aria-label="${esc(t('w_delete'))}">${icon('trash')}</button></div></div>`).join('')
            : `<div class="empty" style="padding:26px">${icon('location', 'xl')}<p>${esc(t('w_no_addresses'))}</p></div>`}</div>
        ${me.is_admin ? `<a class="btn block" style="margin-top:18px;text-decoration:none" href="/admin">${icon('shield')} ${esc(t('w_admin_panel'))}</a>` : ''}`;
    $('addr-add').onclick = () => openAddressForm();
    view.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openAddressForm(addrs.find(a => a.id === +b.dataset.edit)));
    view.querySelectorAll('[data-def]').forEach(b => b.onclick = async () => { await api(`/api/addresses/${b.dataset.def}/default`, { method: 'POST' }); renderProfile(); });
    view.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
        if (!confirm(t('w_delete') + '?')) return;
        await api(`/api/addresses/${b.dataset.del}`, { method: 'DELETE' }); renderProfile();
    });
}
function openAddressForm(a) {
    const sh = openSheet(`<h2>${esc(a ? t('w_edit') : t('w_add_address'))}</h2>
        <div class="field"><label class="label" for="a-title">${esc(t('w_address_title'))}</label><input id="a-title" maxlength="40" value="${esc(a ? a.title : '')}"></div>
        <div class="field"><label class="label" for="a-addr">${esc(t('w_address'))}</label><textarea id="a-addr" rows="3" maxlength="300">${esc(a ? a.address : '')}</textarea></div>
        <label class="check" style="margin-bottom:16px"><input type="checkbox" id="a-def" ${a && a.is_default ? 'checked' : ''}> ${esc(t('w_default'))}</label>
        <button class="btn primary block" id="a-save">${icon('check')} ${esc(t('w_save'))}</button>`);
    $('a-save').onclick = async () => {
        const body = { title: $('a-title').value.trim(), address: $('a-addr').value.trim(), is_default: $('a-def').checked };
        if (!body.title || body.address.length < 3) { toast(t('w_fill_address'), 'err'); return; }
        $('a-save').disabled = true;
        try {
            await api(a ? `/api/addresses/${a.id}` : '/api/addresses', { method: a ? 'PUT' : 'POST', body });
            closeSheet(); toast(t('w_saved')); renderProfile();
        } catch (e) { $('a-save').disabled = false; toast(t('w_error'), 'err'); }
    };
}

// ============================================================ til
const LANG_LABEL = { uz: "O'zbekcha", ru: 'Русский', en: 'English' };
function langBlock() {
    return `<div class="sec-head"><h3>${icon('globe')} ${esc(t('w_language'))}</h3></div>
        <div class="seg" id="lang-seg">${['uz', 'ru', 'en'].map(l => `<button data-l="${l}" class="${l === LANG ? 'on' : ''}">${LANG_LABEL[l]}</button>`).join('')}</div>`;
}
function bindLang() { document.querySelectorAll('#lang-seg button').forEach(b => b.onclick = () => changeLang(b.dataset.l)); }
function openLangSheet() {
    const sh = openSheet(`<h2>${icon('globe')} ${esc(t('w_language'))}</h2>${langBlock().replace(/<div class="sec-head">.*?<\/div>/, '')}`);
    sh.querySelectorAll('#lang-seg button').forEach(b => b.onclick = async () => { await changeLang(b.dataset.l); closeSheet(); });
}
async function changeLang(l) {
    if (l === LANG) return;
    await loadLang(l);
    if (S.me.registered) { try { await api('/api/me/language', { method: 'POST', body: { language: l } }); S.me.language = l; } catch (e) {} }
    renderAll();
}
