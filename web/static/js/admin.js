// Choy Plov - Admin panel (o'zbek tilida)
DICT = { w_currency: "so'm" };
const A = { page: 'dashboard', days: 14, metric: 'revenue', orders: { status: '', search: '', page: 1 }, users: { search: '', page: 1 }, cats: [], pending: 0 };
const main = $('main');
const STATUS_UZ = { pending: 'Kutilmoqda', completed: 'Tasdiqlandi', delivered: 'Yetkazib berildi', cancelled: 'Bekor qilindi' };
const statusBadge = (s) => `<span class="status ${esc(s)}">${esc(STATUS_UZ[s] || s)}</span>`;

// ============================================================ kirish
(async function boot() {
    try {
        await api('/api/admin/session');
        start();
    } catch (e) {
        showLogin(e.status === 403);
    }
})();

function showLogin(forbidden) {
    $('shell').classList.add('hidden');
    const box = $('login');
    box.classList.remove('hidden');
    box.innerHTML = `<div class="login-card"><div class="badge-ic">${icon('shield', 'lg')}</div>
        <h2>Admin panel</h2>
        <p class="muted" style="margin-top:6px">${forbidden ? "Bu akkaunt admin emas. Parol bilan kiring." : "Kirish uchun parolni kiriting"}</p>
        <div class="field"><input type="password" id="pw" class="input" style="width:100%" placeholder="Parol" autocomplete="current-password"></div>
        <button class="btn primary block" id="pw-go">Kirish</button></div>`;
    const go = async () => {
        try {
            const r = await api('/api/admin/login', { method: 'POST', body: { password: $('pw').value } });
            store.sset('cp_admin_token', r.token);
            box.classList.add('hidden');
            start();
        } catch (e) { toast("Parol noto'g'ri yoki ADMIN_PASSWORD sozlanmagan", 'err'); }
    };
    $('pw-go').onclick = go;
    $('pw').onkeydown = (e) => { if (e.key === 'Enter') go(); };
}

function start() {
    $('shell').classList.remove('hidden');
    if (store.sget('cp_admin_token')) {
        $('logout').classList.remove('hidden');
        $('logout').onclick = () => { try { sessionStorage.removeItem('cp_admin_token'); } catch (e) {} location.reload(); };
    }
    document.querySelectorAll('#nav button').forEach(b => b.onclick = () => go(b.dataset.page));
    window.addEventListener('resize', debounce(() => { if (A.page === 'dashboard' && A.stats) drawCharts(); }, 150));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
    go('dashboard');
    startIncoming();
}
function go(page) {
    A.page = page;
    document.querySelectorAll('#nav button').forEach(b => b.classList.toggle('active', b.dataset.page === page));
    ({ dashboard: pageDashboard, orders: pageOrders, products: pageProducts, addons: pageAddons, users: pageUsers, support: pageSupport })[page]();
}
function debounce(fn, ms) { let t0; return (...a) => { clearTimeout(t0); t0 = setTimeout(() => fn(...a), ms); }; }
const loading = () => { main.innerHTML = '<div class="skeleton" style="height:140px;margin-bottom:14px"></div><div class="skeleton" style="height:300px"></div>'; };
function setPending(n) {
    A.pending = n;
    const d = $('pending-dot'); d.textContent = n; d.classList.toggle('hidden', !n);
}

// ============================================================ dashboard
async function pageDashboard() {
    loading();
    try { A.stats = await api(`/api/admin/stats?days=${A.days}`); } catch (e) { return fail(e); }
    const s = A.stats, tt = s.totals;
    setPending(tt.pending);
    main.innerHTML = `
        <div class="page-head"><h1>Dashboard</h1>
            <div class="seg range" id="range">${[7, 14, 30].map(d => `<button data-d="${d}" class="${d === A.days ? 'on' : ''}">${d} kun</button>`).join('')}</div></div>
        <div class="kpis">
            <div class="kpi"><span>${icon('orders')} Bugungi buyurtmalar</span><b>${fmt(tt.today_orders)}</b></div>
            <div class="kpi"><span>${icon('chart')} Bugungi tushum</span><b>${fmt(tt.today_revenue)}</b><small>so'm</small></div>
            <div class="kpi"><span>${icon('chart')} Jami tushum</span><b>${fmt(tt.revenue)}</b><small>so'm (bekor qilinganlarsiz)</small></div>
            <div class="kpi"><span>${icon('users')} Foydalanuvchilar</span><b>${fmt(tt.users)}</b></div>
            <div class="kpi"><span>${icon('clock')} Kutilayotgan</span><b>${fmt(tt.pending)}</b><small>${tt.orders} ta buyurtmadan</small></div>
        </div>
        <div class="panels">
            <div class="panel"><h3><span>Kunlik dinamika</span>
                <div class="seg small" id="metric"><button data-m="revenue" class="${A.metric === 'revenue' ? 'on' : ''}">Tushum</button><button data-m="orders" class="${A.metric === 'orders' ? 'on' : ''}">Buyurtmalar</button></div></h3>
                <div class="chart" id="chart-daily"></div></div>
            <div class="panel"><h3>Buyurtma holatlari</h3><div id="chart-status" class="donut-wrap"></div></div>
            <div class="panel panel-full"><h3>Eng ko'p sotilgan mahsulotlar</h3><div id="chart-top"></div></div>
        </div>`;
    $('range').querySelectorAll('button').forEach(b => b.onclick = () => { A.days = +b.dataset.d; pageDashboard(); });
    $('metric').querySelectorAll('button').forEach(b => b.onclick = () => { A.metric = b.dataset.m; $('metric').querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); drawDaily(); });
    drawCharts();
}
function drawCharts() { drawDaily(); drawStatus(); drawTop(); }

function niceMax(v) {
    if (v <= 0) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(v))), n = v / p;
    return ([1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].find(s => n <= s)) * p;
}
function short(n) { return n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(n % 1e3 ? 1 : 0) + 'k' : String(n); }

function drawDaily() {
    const el = $('chart-daily'); if (!el) return;
    const data = A.stats.daily.map(d => ({ label: d.date.slice(5).replace('-', '.'), value: d[A.metric], date: d.date }));
    const W = el.clientWidth || 560, H = 240, L = 46, R = 6, T = 10, B = 26;
    const pw = W - L - R, ph = H - T - B, max = niceMax(Math.max(...data.map(d => d.value), 0));
    const slot = pw / data.length, bw = Math.max(4, Math.min(34, slot * 0.62));
    const step = Math.ceil(data.length / Math.max(2, Math.floor(pw / 56)));
    let g = '';
    for (let i = 0; i <= 4; i++) {
        const y = T + ph - (ph * i) / 4;
        g += `<line class="grid-line" x1="${L}" x2="${W - R}" y1="${y}" y2="${y}"/><text class="axis" x="${L - 8}" y="${y + 4}" text-anchor="end">${short(max * i / 4)}</text>`;
    }
    const bars = data.map((d, i) => {
        const h = Math.max(d.value ? 3 : 0, (d.value / max) * ph), x = L + slot * i + (slot - bw) / 2, y = T + ph - h, r = Math.min(4, h, bw / 2);
        const path = h ? `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + bw - r} Q${x + bw},${y} ${x + bw},${y + r} V${y + h} Z` : '';
        return `<path class="bar" data-i="${i}" d="${path}"/>` + (i % step === 0 ? `<text class="axis" x="${x + bw / 2}" y="${H - 6}" text-anchor="middle">${d.label}</text>` : '')
            + `<rect data-i="${i}" x="${L + slot * i}" y="${T}" width="${slot}" height="${ph}" fill="transparent"/>`;
    }).join('');
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" height="${H}" role="img" aria-label="Kunlik ${A.metric === 'revenue' ? 'tushum' : 'buyurtmalar'}">${g}${bars}</svg><div class="chart-tip hidden" id="tip"></div>`;
    const tip = $('tip');
    el.querySelectorAll('rect[data-i]').forEach(r => {
        r.onmouseenter = r.onmousemove = r.ontouchstart = () => {
            const i = +r.dataset.i, d = data[i], x = L + slot * i + slot / 2;
            el.querySelectorAll('.bar').forEach(b => b.classList.toggle('hot', +b.dataset.i === i));
            tip.innerHTML = `${esc(d.date)}<b>${A.metric === 'revenue' ? fmt(d.value) + " so'm" : d.value + ' ta'}</b>`;
            tip.style.left = Math.min(Math.max(x, 60), W - 60) + 'px'; tip.style.top = (T + ph - Math.max(3, (d.value / max) * ph)) + 'px';
            tip.classList.remove('hidden');
        };
        r.onmouseleave = () => { tip.classList.add('hidden'); el.querySelectorAll('.bar').forEach(b => b.classList.remove('hot')); };
    });
}

function drawStatus() {
    const el = $('chart-status'); if (!el) return;
    const st = A.stats.statuses, total = st.pending + st.completed + st.delivered + st.cancelled;
    const rows = [['delivered', 'Yetkazib berildi', 'var(--good)'], ['completed', 'Tasdiqlandi', 'var(--accent)'], ['pending', 'Kutilmoqda', 'var(--warn)'], ['cancelled', 'Bekor qilindi', 'var(--bad)']];
    const R = 62, C = 2 * Math.PI * R;
    let off = 0, arcs = '';
    if (total) rows.forEach(([k, , col]) => {
        const len = (st[k] / total) * C; if (!len) return;
        const gap = len > 4 ? 2 : 0;
        arcs += `<circle cx="80" cy="80" r="${R}" fill="none" stroke="${col}" stroke-width="18" stroke-dasharray="${len - gap} ${C - len + gap}" stroke-dashoffset="${-off}" transform="rotate(-90 80 80)"/>`;
        off += len;
    });
    el.innerHTML = `<svg viewBox="0 0 160 160" width="160" height="160" role="img" aria-label="Buyurtma holatlari">
        <circle cx="80" cy="80" r="${R}" fill="none" stroke="var(--surface-2)" stroke-width="18"/>${arcs}
        <text x="80" y="80" text-anchor="middle" fill="var(--text)" font-size="26" font-weight="700">${total}</text>
        <text x="80" y="98" text-anchor="middle" fill="var(--muted)" font-size="11">buyurtma</text></svg>
        <div class="legend">${rows.map(([k, n, col]) => `<div><i style="background:${col}"></i>${n}<b>${st[k]}</b></div>`).join('')}</div>`;
}

function drawTop() {
    const el = $('chart-top'); if (!el) return;
    const top = A.stats.top_products;
    if (!top.length) { el.innerHTML = '<p class="muted">Hali ma\'lumot yo\'q</p>'; return; }
    const max = Math.max(...top.map(p => p.qty));
    el.innerHTML = top.map(p => `<div class="hbar"><span class="name" title="${esc(p.name)}">${esc(p.name)}</span>
        <div class="track"><div class="fill" style="width:${(p.qty / max) * 100}%"></div></div><b>${p.qty} ta</b></div>`).join('');
}

function fail(e) { main.innerHTML = `<div class="empty">${icon('x', 'xl')}<p>Xatolik: ${esc(e.message)}</p></div>`; }

// ============================================================ buyurtmalar
async function pageOrders() {
    const f = A.orders;
    main.innerHTML = `<div class="page-head"><h1>Buyurtmalar</h1>
        <div class="toolbar"><input class="input" id="o-search" placeholder="Qidirish: #id, telefon, ism..." value="${esc(f.search)}"></div></div>
        <div class="chips" style="margin-bottom:14px">${['', 'pending', 'completed', 'delivered', 'cancelled'].map(s =>
            `<button class="chip sm ${f.status === s ? 'active' : ''}" data-s="${s}">${s ? STATUS_UZ[s] : 'Hammasi'}</button>`).join('')}</div>
        <div id="o-table"></div>`;
    main.querySelectorAll('.chip').forEach(b => b.onclick = () => { f.status = b.dataset.s; f.page = 1; pageOrders(); });
    $('o-search').oninput = debounce((e) => { f.search = e.target.value.trim(); f.page = 1; loadOrdersTable(); }, 300);
    loadOrdersTable();
}
async function loadOrdersTable() {
    const f = A.orders, box = $('o-table');
    try {
        const q = new URLSearchParams({ page: f.page });
        if (f.status) q.set('status', f.status);
        if (f.search) q.set('search', f.search);
        const r = await api('/api/admin/orders?' + q);
        A.orderRows = Object.fromEntries(r.items.map(o => [o.id, o]));
        box.innerHTML = r.items.length ? `<div class="table-wrap"><table><thead><tr><th>#</th><th>Mijoz</th><th>Telefon</th><th>Manzil</th><th>Vaqt</th><th>Holat</th><th class="num">Summa</th></tr></thead><tbody>
            ${r.items.map(o => `<tr class="click" data-id="${o.id}"><td><b>#${o.id}</b></td><td>${esc(o.first_name || '—')}${o.username ? `<div class="muted">@${esc(o.username)}</div>` : ''}</td>
            <td>${esc(o.phone_number)}</td><td style="max-width:240px">${esc(o.address)}</td><td class="muted">${esc(fmtDate(o.created_at))}</td><td>${statusBadge(o.status)}</td><td class="num"><b>${fmt(o.total_price)}</b></td></tr>`).join('')}</tbody></table></div>
            ${pager(r, f, loadOrdersTable)}` : `<div class="empty">${icon('orders', 'xl')}<p>Buyurtmalar topilmadi</p></div>`;
        box.querySelectorAll('tr.click').forEach(tr => tr.onclick = () => openOrder(A.orderRows[tr.dataset.id]));
        bindPager(box, f, loadOrdersTable);
    } catch (e) { fail(e); }
}
function pager(r, f) {
    const pages = Math.max(1, Math.ceil(r.total / r.per_page));
    return `<div class="pager"><span>Jami: ${r.total}</span><div class="toolbar"><button class="btn sm" data-p="-1" ${f.page <= 1 ? 'disabled' : ''}>${icon('back')}</button><span>${f.page} / ${pages}</span><button class="btn sm" data-p="1" ${f.page >= pages ? 'disabled' : ''}>${icon('chevron')}</button></div></div>`;
}
function bindPager(box, f, reload) { box.querySelectorAll('[data-p]').forEach(b => b.onclick = () => { f.page += +b.dataset.p; reload(); }); }

function openOrder(o) {
    const sh = openSheet(`<h2>Buyurtma #${o.id} ${statusBadge(o.status)}</h2>
        <div class="meta">${icon('user')} ${esc(o.first_name || '—')} ${o.username ? '@' + esc(o.username) : ''}</div>
        <div class="meta">${icon('phone')} ${esc(o.phone_number)}</div>
        <div class="meta">${icon('location')} ${esc(o.address)}</div>
        <a class="btn sm" href="${esc(mapLink(o))}" target="_blank" rel="noopener" style="text-decoration:none;margin:2px 0 6px">${icon('location')} Yandex xaritada ochish</a>
        ${hasLoc(o) ? `<iframe class="map-frame" loading="lazy" src="https://yandex.com/map-widget/v1/?ll=${o.lon}%2C${o.lat}&z=16&pt=${o.lon}%2C${o.lat}%2Cpm2rdm" title="Xarita"></iframe>` : ''}
        <div class="meta">${icon('clock')} ${esc(fmtDate(o.created_at))}</div>
        ${o.comment ? `<div class="meta">${icon('bell')} ${esc(o.comment)}</div>` : ''}
        <div class="order-items" style="margin-top:14px">${o.items.map(i => `<div><span>${esc(i.product_name)} × ${i.quantity}${i.addons.length ? `<small>+ ${i.addons.map(a => esc(`${a.name} ${a.unit || ''} ×${a.qty}`)).join(', ')}</small>` : ''}</span><b>${fmt(i.price)}</b></div>`).join('')}</div>
        <div class="total-row"><span>Jami</span><b>${fmt(o.total_price)} so'm</b></div>
        ${o.status === 'pending' || o.status === 'completed' ? `<button class="btn block" id="o-edit" style="margin-top:14px">${icon('edit')} Buyurtmani tahrirlash (qo'shish / olib tashlash)</button>` : ''}
        <div class="toolbar" style="margin-top:18px">
            ${o.status === 'pending' ? `<button class="btn primary" data-st="completed">${icon('check')} Tasdiqlash</button>` : ''}
            ${o.status === 'completed' ? `<button class="btn primary" data-st="delivered">${icon('check')} Yetkazib berildi</button>` : ''}
            ${o.status === 'pending' || o.status === 'completed' ? `<button class="btn danger" data-st="cancelled">${icon('x')} Bekor qilish</button>` : ''}
            ${o.status === 'cancelled' ? `<button class="btn" data-st="pending">${icon('clock')} Kutilmoqda</button>` : ''}</div>
        <p class="muted" style="margin-top:10px;font-size:12.5px">Tasdiqlash/bekor qilishda mijozga Telegram orqali xabar yuboriladi.</p>`);
    if ($('o-edit')) $('o-edit').onclick = () => openOrderEdit(o);
    sh.querySelectorAll('[data-st]').forEach(b => b.onclick = async () => {
        b.disabled = true;
        try { await api(`/api/admin/orders/${o.id}/status`, { method: 'POST', body: { status: b.dataset.st } }); closeSheet(); toast('Holat yangilandi'); loadOrdersTable(); refreshPending(); }
        catch (e) { b.disabled = false; toast('Xatolik', 'err'); }
    });
}
const hasLoc = o => o.lat != null && o.lon != null;
const mapLink = o => hasLoc(o) ? `https://yandex.com/maps/?pt=${o.lon},${o.lat}&z=17&l=map` : `https://yandex.com/maps/?text=${encodeURIComponent(o.address || '')}`;

// Buyurtma tarkibini tahrirlash: sonini o'zgartirish, olib tashlash (qaytarish bilan), qo'shimchalar, yangi mahsulot qo'shish (qidiruv + kategoriya)
async function openOrderEdit(o) {
    let prods = [], adds = [], cats = [];
    try {
        [prods, adds, cats] = await Promise.all([api('/api/admin/products'), api('/api/admin/addons'), api('/api/admin/categories')]);
    } catch (e) { toast('Xatolik', 'err'); return; }
    prods = prods.filter(p => p.is_active);
    adds = adds.filter(a => a.is_active !== false);
    const P = Object.fromEntries(prods.map(p => [p.id, p])), AD = Object.fromEntries(adds.map(a => [a.id, a]));
    const snap = (ls) => JSON.stringify(ls.map(l => [l.pid, l.qty, l.addons.map(a => [a.id, a.qty]).sort()]));
    // har bir qator: {pid, name, qty, addons:[{id,qty}], fallback: eski narx (mahsulot topilmasa)}
    let lines = o.items.map(i => ({ pid: i.product_id, name: i.product_name, qty: i.quantity, addons: i.addons.map(x => ({ id: x.id, qty: x.qty })), fallback: i.price }));
    const orig = snap(lines);
    let removed = null, q = '', cat = 0;
    const lineSum = (l) => {
        const p = P[l.pid];
        if (!p) return l.fallback;
        return (p.price + l.addons.reduce((t, a) => t + (AD[a.id] ? AD[a.id].price * a.qty : 0), 0)) * l.qty;
    };
    const total = () => lines.reduce((t, l) => t + lineSum(l), 0);
    const addonOptions = (l) => {
        const p = P[l.pid], ids = new Set([...(p ? p.addon_ids : []), ...l.addons.map(a => a.id)]);
        return [...ids].map(id => AD[id]).filter(Boolean);
    };
    const sh = openSheet('<div id="oe"></div>');
    const draw = () => {
        const dirty = snap(lines) !== orig, diff = total() - o.total_price;
        const list = prods.filter(p => (!cat || p.category_id === cat) && (!q || p.name.toLowerCase().includes(q.toLowerCase())));
        $('oe').innerHTML = `<h2>${icon('edit')} Buyurtma #${o.id} tarkibi</h2>
            <div class="oe-lines">${lines.length ? lines.map((l, k) => {
                const opts = addonOptions(l);
                return `<div class="oe-line"><div class="oe-top"><div class="oe-name"><b>${esc(l.name)}</b>${P[l.pid] ? '' : '<small>(mahsulot menyudan olib tashlangan)</small>'}</div>
                    <b class="oe-sum">${fmt(lineSum(l))}</b></div>
                    <div class="oe-ctl"><span class="qty"><button data-d="${k}:-1" aria-label="Kamaytirish">${icon('minus')}</button><b>${l.qty}</b><button data-d="${k}:1" aria-label="Ko'paytirish">${icon('plus')}</button></span>
                    <button class="btn sm danger" data-rm="${k}" aria-label="Olib tashlash">${icon('trash')} Olib tashlash</button></div>
                    ${opts.length ? `<div class="oe-adds">${opts.map(a => { const cur = l.addons.find(x => x.id === a.id); return cur
                        ? `<span class="chip sm active oe-add-on">${esc(a.name)}${a.unit ? ' ' + esc(a.unit) : ''} ×${cur.qty} <button data-aq="${k}:${a.id}:-1" aria-label="Kamaytirish">−</button><button data-aq="${k}:${a.id}:1" aria-label="Ko'paytirish">+</button></span>`
                        : `<button class="chip sm" data-ad="${k}:${a.id}">+ ${esc(a.name)}${a.unit ? ' ' + esc(a.unit) : ''} <small>${fmt(a.price)}</small></button>`; }).join('')}</div>` : ''}</div>`;
            }).join('') : '<p class="muted">Buyurtma bo\'sh — kamida bitta mahsulot kerak</p>'}</div>
            ${removed ? `<div class="oe-undo"><span>«${esc(removed.line.name)}» olib tashlandi</span><button class="btn sm" id="oe-undo">Qaytarish</button></div>` : ''}
            <div class="oe-total"><span>Jami</span><span><b>${fmt(total())} so'm</b>${dirty && diff ? `<small class="${diff > 0 ? 'up' : 'down'}">${diff > 0 ? '+' : '−'}${fmt(Math.abs(diff))} (oldin ${fmt(o.total_price)})</small>` : ''}</span></div>
            <label class="label" style="margin-top:14px">Mahsulot qo'shish</label>
            <input class="input" id="oe-q" placeholder="Qidirish..." value="${esc(q)}" autocomplete="off">
            <div class="chips" style="margin:8px 0"><button class="chip sm ${cat ? '' : 'active'}" data-cat="0">Hammasi</button>${cats.map(c => `<button class="chip sm ${cat === c.id ? 'active' : ''}" data-cat="${c.id}">${esc(c.name)}</button>`).join('')}</div>
            <div class="oe-pick">${list.length ? list.map(p => `<button class="oe-prod" data-pick="${p.id}"><span>${esc(p.name)}${p.is_available ? '' : '<small>hozir mavjud emas</small>'}</span><b>${fmt(p.price)}</b>${icon('plus')}</button>`).join('') : '<p class="muted" style="padding:10px">Hech narsa topilmadi</p>'}</div>
            <div class="toolbar" style="margin-top:18px"><button class="btn primary" id="oe-save" ${lines.length && dirty ? '' : 'disabled'}>${icon('check')} Saqlash</button><button class="btn" id="oe-back">Orqaga</button></div>
            <p class="muted" style="margin-top:10px;font-size:12.5px">Saqlansa, mijozga Telegram orqali yangi jami yuboriladi.</p>`;
        const scroll = () => { };
        sh.querySelectorAll('[data-d]').forEach(b => b.onclick = () => { const [k, d] = b.dataset.d.split(':').map(Number); lines[k].qty = Math.min(50, Math.max(1, lines[k].qty + d)); draw(); });
        sh.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { const k = +b.dataset.rm; removed = { line: lines[k], k }; lines.splice(k, 1); draw(); });
        if ($('oe-undo')) $('oe-undo').onclick = () => { lines.splice(Math.min(removed.k, lines.length), 0, removed.line); removed = null; draw(); };
        sh.querySelectorAll('[data-ad]').forEach(b => b.onclick = () => { const [k, id] = b.dataset.ad.split(':').map(Number); lines[k].addons.push({ id, qty: 1 }); draw(); });
        sh.querySelectorAll('[data-aq]').forEach(b => b.onclick = () => {
            const [k, id, d] = b.dataset.aq.split(':').map(Number), l = lines[k], a = l.addons.find(x => x.id === id);
            a.qty += d; if (a.qty < 1) l.addons = l.addons.filter(x => x.id !== id); else a.qty = Math.min(20, a.qty); draw();
        });
        sh.querySelectorAll('[data-cat]').forEach(b => b.onclick = () => { cat = +b.dataset.cat; draw(); });
        sh.querySelectorAll('[data-pick]').forEach(b => b.onclick = () => {
            const p = P[+b.dataset.pick]; if (!p) return;
            const ex = lines.find(l => l.pid === p.id && !l.addons.length);
            if (ex) ex.qty = Math.min(50, ex.qty + 1); else lines.push({ pid: p.id, name: p.name, qty: 1, addons: [] });
            removed = null; draw();
            const box = sh.querySelector('.oe-lines'); if (box) box.lastElementChild && box.lastElementChild.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        });
        $('oe-q').oninput = (e) => { q = e.target.value.trim(); const pos = e.target.selectionStart; draw(); const n = $('oe-q'); n.focus(); n.setSelectionRange(pos, pos); };
        $('oe-back').onclick = () => { if (snap(lines) !== orig && !confirm("Saqlanmagan o'zgarishlar bekor qilinsinmi?")) return; closeSheet(); openOrder(o); };
        $('oe-save').onclick = async () => {
            $('oe-save').disabled = true;
            try {
                await api(`/api/admin/orders/${o.id}/items`, { method: 'PUT', body: { cart: lines.map(l => ({ product_id: l.pid, quantity: l.qty, addons: l.addons })) } });
                closeSheet(); toast('Buyurtma yangilandi'); loadOrdersTable(); refreshPending();
            } catch (e) { $('oe-save').disabled = false; toast("Xatolik (buyurtma holati o'zgargan bo'lishi mumkin)", 'err'); }
        };
    };
    draw();
}
async function refreshPending() { try { setPending((await api('/api/admin/stats?days=1')).totals.pending); } catch (e) {} }

// ============================================================ mahsulotlar
async function pageProducts() {
    loading();
    try {
        const [cats, prods, adds] = await Promise.all([api('/api/admin/categories'), api('/api/admin/products'), api('/api/admin/addons')]);
        A.cats = cats; A.addonList = adds; A.prods = Object.fromEntries(prods.map(p => [p.id, p]));
        main.innerHTML = `<div class="page-head"><h1>Mahsulotlar</h1>
            <div class="toolbar"><button class="btn primary" id="new-prod">${icon('plus')} Mahsulot qo'shish</button></div></div>
            <div class="panel" style="margin-bottom:8px"><h3>Kategoriyalar</h3>
                ${cats.map(c => `<div class="cat-row">${icon(categoryIcon(c.name))}<span>${esc(c.name)}</span><small>${c.products_count} ta</small>
                    <button class="icon-btn" style="width:34px;height:34px" data-ren="${c.id}" title="Nomini o'zgartirish">${icon('edit')}</button>
                    <button class="icon-btn" style="width:34px;height:34px" data-delcat="${c.id}" title="O'chirish">${icon('trash')}</button></div>`).join('') || '<p class="muted">Kategoriya yo\'q</p>'}
                <div class="toolbar" style="margin-top:10px"><input class="input" id="new-cat" placeholder="Yangi kategoriya nomi" maxlength="60"><button class="btn" id="add-cat">${icon('plus')} Qo'shish</button></div></div>
            ${cats.map(c => {
                const list = prods.filter(p => p.category_id === c.id);
                return `<div class="cat-group">${icon(categoryIcon(c.name))} ${esc(c.name)}</div>` + (list.length ? `<div class="table-wrap"><table class="fixed"><colgroup><col style="width:68px"><col><col style="width:100px"><col style="width:84px"><col style="width:84px"><col style="width:104px"></colgroup><thead><tr><th></th><th>Nomi</th><th class="num">Narx</th><th>Rasmlar</th><th>Mavjud</th><th></th></tr></thead><tbody>
                    ${list.map(p => `<tr><td><div class="thumb-sm">${p.images[0] ? `<img src="${esc(p.images[0].url)}" alt="">` : icon('plov')}</div></td>
                    <td><b>${esc(p.name)}</b>${p.description ? `<div class="muted" style="max-width:300px">${esc(p.description.slice(0, 70))}</div>` : ''}</td>
                    <td class="num">${fmt(p.price)}</td><td>${p.images.length}/5</td>
                    <td><button class="switch ${p.is_available ? 'on' : ''}" data-tog="${p.id}" aria-label="Mavjudligi"></button></td>
                    <td class="num"><button class="icon-btn" style="width:34px;height:34px;display:inline-grid" data-edit="${p.id}">${icon('edit')}</button>
                        <button class="icon-btn" style="width:34px;height:34px;display:inline-grid" data-delp="${p.id}">${icon('trash')}</button></td></tr>`).join('')}</tbody></table></div>`
                    : '<p class="muted">Mahsulot yo\'q</p>');
            }).join('')}`;
        $('new-prod').onclick = () => openProductForm();
        $('add-cat').onclick = async () => { const n = $('new-cat').value.trim(); if (!n) return; await api('/api/admin/categories', { method: 'POST', body: { name: n } }); pageProducts(); };
        main.querySelectorAll('[data-ren]').forEach(b => b.onclick = async () => {
            const c = A.cats.find(x => x.id === +b.dataset.ren), n = prompt('Yangi nom:', c.name);
            if (n && n.trim()) { await api(`/api/admin/categories/${c.id}`, { method: 'PUT', body: { name: n.trim() } }); pageProducts(); }
        });
        main.querySelectorAll('[data-delcat]').forEach(b => b.onclick = async () => {
            if (confirm("Kategoriya va undagi barcha mahsulotlar o'chirilsinmi?")) { await api(`/api/admin/categories/${b.dataset.delcat}`, { method: 'DELETE' }); pageProducts(); }
        });
        main.querySelectorAll('[data-tog]').forEach(b => b.onclick = async () => { const r = await api(`/api/admin/products/${b.dataset.tog}/toggle`, { method: 'POST' }); b.classList.toggle('on', r.is_available); });
        main.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openProductForm(A.prods[b.dataset.edit]));
        main.querySelectorAll('[data-delp]').forEach(b => b.onclick = async () => {
            if (confirm("Mahsulot o'chirilsinmi?")) { await api(`/api/admin/products/${b.dataset.delp}`, { method: 'DELETE' }); pageProducts(); }
        });
    } catch (e) { fail(e); }
}

function openProductForm(p) {
    if (!A.cats.length) { toast("Avval kategoriya qo'shing", 'err'); return; }
    const pending = [];          // yangi tanlangan fayllar
    let images = p ? [...p.images] : [];
    const sh = openSheet(`<h2>${p ? 'Mahsulotni tahrirlash' : "Yangi mahsulot"}</h2>
        <div class="form-grid">
            <div class="full"><span class="label">Kategoriya</span><div class="field"><select id="p-cat">${A.cats.map(c => `<option value="${c.id}" ${p && p.category_id === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}</select></div></div>
            <div><span class="label">Nomi</span><div class="field"><input id="p-name" maxlength="120" value="${esc(p ? p.name : '')}"></div></div>
            <div><span class="label">Narx (so'm)</span><div class="field"><input id="p-price" type="number" min="1" step="500" value="${p ? p.price : ''}"></div></div>
            <div class="full"><span class="label">Tavsif</span><div class="field"><textarea id="p-desc" rows="3" maxlength="1000">${esc(p && p.description ? p.description : '')}</textarea></div></div>
            <div class="full"><span class="label">Qo'shimchalar (shu mahsulotga qaysilari qo'shiladi)</span>
                <div class="checks" id="p-addons">${A.addonList.length ? A.addonList.map(x => `<label class="check"><input type="checkbox" value="${x.id}" ${(p ? p.addon_ids.includes(x.id) : true) ? 'checked' : ''}> ${esc(x.name)} ${esc(x.unit || '')}${x.is_available ? '' : ' <small class="muted">(o\'chiq)</small>'}</label>`).join('') : '<span class="muted">Avval "Qo\'shimchalar" bo\'limida qo\'shimcha yarating</span>'}</div></div>
            <div class="full"><span class="label">Galereya (3-5 ta rasm tavsiya etiladi · JPG/PNG/WEBP · 5MB gacha)</span><div class="img-grid" id="p-imgs"></div>
                <input type="file" id="p-file" accept="image/jpeg,image/png,image/webp" multiple class="hidden"></div>
        </div>
        <button class="btn primary block" id="p-save">${icon('check')} Saqlash</button>`);
    sh.classList.add('wide');

    const drawImgs = () => {
        const room = 5 - images.length - pending.length;
        $('p-imgs').innerHTML = images.map(i => `<div class="img-item"><img src="${esc(i.url)}" alt=""><button data-rm="${i.id}" aria-label="O'chirish">${icon('x')}</button></div>`).join('')
            + pending.map((f, k) => `<div class="img-item new"><img src="${URL.createObjectURL(f)}" alt=""><button data-pn="${k}" aria-label="Olib tashlash">${icon('x')}</button></div>`).join('')
            + (room > 0 ? `<div class="drop" id="p-drop">${icon('plus', 'lg')}<span>Rasm</span></div>` : '');
        $('p-imgs').querySelectorAll('[data-rm]').forEach(b => b.onclick = async () => {
            try { await api(`/api/admin/images/${b.dataset.rm}`, { method: 'DELETE' }); images = images.filter(i => i.id !== +b.dataset.rm); drawImgs(); } catch (e) { toast('Xatolik', 'err'); }
        });
        $('p-imgs').querySelectorAll('[data-pn]').forEach(b => b.onclick = () => { pending.splice(+b.dataset.pn, 1); drawImgs(); });
        const drop = $('p-drop'); if (drop) drop.onclick = () => $('p-file').click();
    };
    $('p-file').onchange = (e) => {
        [...e.target.files].forEach(f => { if (images.length + pending.length < 5) pending.push(f); });
        e.target.value = ''; drawImgs();
    };
    drawImgs();

    $('p-save').onclick = async () => {
        const body = { category_id: +$('p-cat').value, name: $('p-name').value.trim(), price: parseFloat($('p-price').value), description: $('p-desc').value.trim() || null,
            addon_ids: [...document.querySelectorAll('#p-addons input:checked')].map(i => +i.value) };
        if (!body.name || !(body.price > 0)) { toast('Nom va narxni kiriting', 'err'); return; }
        $('p-save').disabled = true;
        try {
            const id = p ? p.id : (await api('/api/admin/products', { method: 'POST', body })).id;
            if (p) await api(`/api/admin/products/${p.id}`, { method: 'PUT', body });
            for (const f of pending) {
                const fd = new FormData(); fd.append('file', f);
                try { await api(`/api/admin/products/${id}/images`, { method: 'POST', formData: fd }); }
                catch (e) { toast(`${f.name}: ${e.message}`, 'err'); }
            }
            closeSheet(); toast('Saqlandi'); pageProducts();
        } catch (e) { $('p-save').disabled = false; toast('Xatolik: ' + e.message, 'err'); }
    };
}

// ============================================================ foydalanuvchilar
async function pageUsers() {
    const f = A.users;
    main.innerHTML = `<div class="page-head"><h1>Foydalanuvchilar</h1>
        <div class="toolbar"><input class="input" id="u-search" placeholder="Qidirish: ism, telefon, @username" value="${esc(f.search)}"></div></div><div id="u-table"></div>`;
    $('u-search').oninput = debounce((e) => { f.search = e.target.value.trim(); f.page = 1; loadUsers(); }, 300);
    loadUsers();
}
async function loadUsers() {
    const f = A.users, box = $('u-table');
    try {
        const r = await api(`/api/admin/users?page=${f.page}&search=${encodeURIComponent(f.search)}`);
        box.innerHTML = r.items.length ? `<div class="table-wrap"><table><thead><tr><th>Foydalanuvchi</th><th>Telefon</th><th>Til</th><th class="num">Buyurtmalar</th><th class="num">Sarflagan (so'm)</th><th>Ro'yxatdan o'tgan</th></tr></thead><tbody>
            ${r.items.map(u => `<tr><td><b>${esc(u.first_name || '—')}</b><div class="muted">${u.username ? '@' + esc(u.username) : 'ID ' + u.user_id}</div></td><td>${esc(u.phone_number || '—')}</td>
            <td>${esc((u.language || 'uz').toUpperCase())}</td><td class="num">${u.orders_count}</td><td class="num">${fmt(u.spent)}</td><td class="muted">${esc(fmtDate(u.created_at))}</td></tr>`).join('')}</tbody></table></div>${pager(r, f)}`
            : `<div class="empty">${icon('users', 'xl')}<p>Foydalanuvchilar topilmadi</p></div>`;
        bindPager(box, f, loadUsers);
    } catch (e) { fail(e); }
}

// ============================================================ qo'shimchalar (go'sht, bedana tuxumi, qazi...)
async function pageAddons() {
    loading();
    try {
        const [list, prods] = await Promise.all([api('/api/admin/addons'), api('/api/admin/products')]);
        A.addons = Object.fromEntries(list.map(x => [x.id, x])); A.allProducts = prods;
        main.innerHTML = `<div class="page-head"><h1>Qo'shimchalar</h1>
            <div class="toolbar"><button class="btn primary" id="new-addon">${icon('plus')} Qo'shimcha qo'shish</button></div></div>
            <p class="muted" style="margin-bottom:14px">Mijoz mahsulotga har bir qo'shimchadan istalgancha porsiya qo'sha oladi. Narx — bitta porsiya uchun.</p>
            ${list.length ? `<div class="table-wrap"><table><thead><tr><th>Nomi</th><th>Porsiya</th><th class="num">Narx (so'm)</th><th>Mahsulotlar</th><th>Mavjud</th><th></th></tr></thead><tbody>
                ${list.map(x => `<tr><td><b>${esc(x.name)}</b></td><td>${esc(x.unit || '—')}</td><td class="num">${fmt(x.price)}</td>
                <td class="muted">${x.product_ids.length} ta</td>
                <td><button class="switch ${x.is_available ? 'on' : ''}" data-atog="${x.id}" aria-label="Mavjudligi"></button></td>
                <td class="num"><button class="icon-btn" style="width:34px;height:34px;display:inline-grid" data-edit="${x.id}">${icon('edit')}</button>
                <button class="icon-btn" style="width:34px;height:34px;display:inline-grid" data-del="${x.id}">${icon('trash')}</button></td></tr>`).join('')}</tbody></table></div>`
                : `<div class="empty">${icon('plus', 'xl')}<p>Qo'shimchalar yo'q</p></div>`}`;
        $('new-addon').onclick = () => openAddonForm();
        main.querySelectorAll('[data-atog]').forEach(b => b.onclick = async () => { const r = await api(`/api/admin/addons/${b.dataset.atog}/toggle`, { method: 'POST' }); b.classList.toggle('on', r.is_available); });
        main.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openAddonForm(A.addons[b.dataset.edit]));
        main.querySelectorAll('[data-del]').forEach(b => b.onclick = async () => {
            if (confirm("Qo'shimcha menyudan olib tashlansinmi? (eski buyurtmalar saqlanadi)")) { await api(`/api/admin/addons/${b.dataset.del}`, { method: 'DELETE' }); pageAddons(); }
        });
    } catch (e) { fail(e); }
}
function openAddonForm(x) {
    openSheet(`<h2>${x ? "Qo'shimchani tahrirlash" : "Yangi qo'shimcha"}</h2>
        <div class="field"><span class="label">Nomi (masalan: Go'sht)</span><input id="ad-name" maxlength="60" value="${esc(x ? x.name : '')}"></div>
        <span class="label">Qaysi mahsulotlarga qo'shiladi</span>
        <div class="checks" id="ad-products"><label class="check all"><input type="checkbox" id="ad-all"> Hammasi</label>${A.allProducts.map(p => `<label class="check"><input type="checkbox" value="${p.id}" ${x && x.product_ids.includes(p.id) ? 'checked' : ''}> ${esc(p.name)}</label>`).join('')}</div>
        <div class="form-grid"><div><span class="label">Porsiya (50 gr, 25 gr, 1 dona)</span><div class="field"><input id="ad-unit" maxlength="20" value="${esc(x && x.unit ? x.unit : '')}"></div></div>
        <div><span class="label">Narx (so'm)</span><div class="field"><input id="ad-price" type="number" min="0" step="500" value="${x ? x.price : ''}"></div></div></div>
        <button class="btn primary block" id="ad-save">${icon('check')} Saqlash</button>`);
    const boxes = () => [...document.querySelectorAll('#ad-products input[value]')];
    $('ad-all').onchange = (e) => boxes().forEach(b => b.checked = e.target.checked);
    $('ad-save').onclick = async () => {
        const body = { product_ids: boxes().filter(b => b.checked).map(b => +b.value), name: $('ad-name').value.trim(), unit: $('ad-unit').value.trim() || null, price: parseFloat($('ad-price').value) };
        if (!body.name || !(body.price >= 0)) { toast('Nom va narxni kiriting', 'err'); return; }
        $('ad-save').disabled = true;
        try { await api(x ? `/api/admin/addons/${x.id}` : '/api/admin/addons', { method: x ? 'PUT' : 'POST', body }); closeSheet(); toast('Saqlandi'); pageAddons(); }
        catch (e) { $('ad-save').disabled = false; toast('Xatolik: ' + e.message, 'err'); }
    };
}

// ============================================================ yangi buyurtmalar soni (chap menyudagi belgi)
function startIncoming() {
    refreshPending(); refreshSupUnread();
    setInterval(() => { if (!document.hidden) { refreshPending(); if (A.page !== 'support') refreshSupUnread(); } }, 15000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) { refreshPending(); refreshSupUnread(); } });
}

// ============================================================ murojaatlar (mijozlar bilan chat)
A.sup = { search: '', unread: 0, uid: null, lastId: 0, items: [] };
let supPrev = null;
function setSupDot(n) {
    const d = $('sup-dot'); if (!d) return;
    d.textContent = n; d.classList.toggle('hidden', !n);
    if (supPrev !== null && n > supPrev) toast('Yangi murojaat keldi');
    supPrev = n;
}
async function refreshSupUnread() { try { setSupDot((await api('/api/admin/support/unread')).count); } catch (e) {} }

function pageSupport() {
    const f = A.sup;
    f.uid = null; f.lastId = 0;
    main.innerHTML = `<div class="page-head"><h1>Murojaatlar</h1>
        <div class="toolbar"><input class="input" id="sa-search" placeholder="Qidirish: ism, telefon, @username" value="${esc(f.search)}">
            <label class="check" style="margin:0"><input type="checkbox" id="sa-unread" ${f.unread ? 'checked' : ''}> Faqat javobsizlar</label></div></div>
        <div class="sup-admin" id="sa"><div class="sa-list" id="sa-list"></div>
            <div class="sa-chat" id="sa-chat"><div class="empty">${icon('bell', 'xl')}<p>Chapdan mijozni tanlang</p></div></div></div>`;
    $('sa-search').oninput = debounce((e) => { f.search = e.target.value.trim(); loadThreads(); }, 300);
    $('sa-unread').onchange = (e) => { f.unread = e.target.checked ? 1 : 0; loadThreads(); };
    loadThreads();
}
async function loadThreads() {
    const f = A.sup, box = $('sa-list');
    if (!box) return;
    try {
        const r = await api(`/api/admin/support?search=${encodeURIComponent(f.search)}&unread=${f.unread}`);
        setSupDot(r.unread_total);
        f.items = r.items;
        box.innerHTML = r.items.length ? r.items.map(u => `<button class="sa-item ${u.user_id === f.uid ? 'on' : ''}" data-uid="${u.user_id}">
            <span class="avatar sm"><span>${esc((u.first_name || '?').trim().charAt(0).toUpperCase())}</span></span>
            <span class="sa-txt"><b>${esc(u.first_name || '—')}</b><small>${u.username ? '@' + esc(u.username) : esc(u.phone_number || 'ID ' + u.user_id)}</small>
                <em>${u.last_sender === 'admin' ? 'Siz: ' : ''}${esc(u.last_body)}</em></span>
            <span class="sa-meta"><small>${esc(fmtDate(u.last_at))}</small>${u.unread ? `<i class="badge-dot">${u.unread}</i>` : ''}</span></button>`).join('')
            : `<div class="empty" style="padding:30px 10px"><p>Murojaatlar yo'q</p></div>`;
        box.querySelectorAll('.sa-item').forEach(b => b.onclick = () => openThread(+b.dataset.uid));
    } catch (e) { /* keyingi so'rovda yangilanadi */ }
}

async function openThread(uid) {
    const f = A.sup, chat = $('sa-chat');
    f.uid = uid; f.lastId = 0;
    $('sa').classList.add('chat-open');
    document.querySelectorAll('.sa-item').forEach(b => b.classList.toggle('on', +b.dataset.uid === uid));
    chat.innerHTML = '<div class="skeleton" style="height:100%;min-height:300px"></div>';
    let r;
    try { r = await api(`/api/admin/support/${uid}`); } catch (e) { chat.innerHTML = `<div class="empty"><p>Xatolik: ${esc(e.message)}</p></div>`; return; }
    const u = r.user, st = u.stats || {};
    const info = (k, v) => `<div><span>${k}</span><b>${v}</b></div>`;
    const tel = (u.phone_number || '').replace(/[^\d+]/g, '');
    chat.innerHTML = `<div class="sa-head"><button class="icon-btn sa-back" id="sa-back" aria-label="Orqaga">${icon('back')}</button>
            <span class="avatar sm"><span>${esc((u.first_name || '?').trim().charAt(0).toUpperCase())}</span></span>
            <div><b>${esc(u.first_name || '—')}</b><div class="muted">${u.username ? `<a href="https://t.me/${esc(u.username)}" target="_blank" rel="noopener">@${esc(u.username)}</a>` : 'ID ' + u.user_id}</div></div></div>
        <details class="sa-info" ${window.innerWidth > 900 ? 'open' : ''}><summary>Mijoz ma'lumotlari</summary>
            <div class="sa-grid">
                ${info('Telefon', tel ? `<a href="tel:${esc(tel)}">${esc(u.phone_number)}</a>` : '—')}
                ${info('Telegram ID', esc(u.user_id))}
                ${info('Til', esc((u.language || 'uz').toUpperCase()))}
                ${info("Ro'yxatdan o'tgan", esc(fmtDate(u.created_at)))}
                ${info('Buyurtmalar', fmt(st.orders) + ' ta (' + fmt(st.completed) + ' ta bajarilgan)')}
                ${info("Sarflagan", fmt(st.spent) + " so'm")}
            </div>
            ${u.addresses.length ? `<div class="sa-sub"><span>Saqlangan manzillar</span>${u.addresses.map(a => `<div>${icon('location')} <b>${esc(a.title)}</b>: ${esc(a.address)}</div>`).join('')}</div>` : ''}
            ${u.orders.length ? `<div class="sa-sub"><span>Oxirgi buyurtmalar</span>${u.orders.map(o => `<div>#${o.id} ${statusBadge(o.status)} ${fmt(o.total_price)} so'm · ${esc(o.phone_number)} · <span class="muted">${esc(fmtDate(o.created_at))}</span></div>`).join('')}</div>` : ''}
        </details>
        <div class="sup-list" id="sa-msgs"></div>
        <div class="sup-compose"><textarea id="sa-in" rows="1" maxlength="1000" placeholder="Javob yozing... (Enter — yuborish, Shift+Enter — yangi qator)"></textarea>
            <button class="sup-send" id="sa-send" aria-label="Yuborish">${icon('chevron')}</button></div>`;
    $('sa-back').onclick = () => { f.uid = null; $('sa').classList.remove('chat-open'); loadThreads(); };
    const input = $('sa-in');
    input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 140) + 'px'; });
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendReply(); } });
    $('sa-send').onclick = sendReply;
    addThreadMessages(r.messages, true);
    loadThreads();               // ochilgach "o'qilgan" bo'ladi — chap ro'yxat va belgi yangilanadi
    if (window.innerWidth > 900) input.focus();
}
function addThreadMessages(msgs, first) {
    const box = $('sa-msgs'), f = A.sup;
    if (!box) return;
    const fresh = msgs.filter(m => m.id > f.lastId);
    if (!fresh.length) { if (first) box.innerHTML = '<div class="sup-empty"><p>Hali xabar yo\'q</p></div>'; return; }
    const stick = first || box.scrollHeight - box.scrollTop - box.clientHeight < 80;
    box.querySelectorAll('.sup-empty').forEach(x => x.remove());
    box.insertAdjacentHTML('beforeend', fresh.map(m => `<div class="bub ${m.sender === 'admin' ? 'me' : 'them'}" data-id="${m.id}"><span>${esc(m.body)}</span><small>${esc(fmtDate(m.created_at))}</small></div>`).join(''));
    f.lastId = fresh[fresh.length - 1].id;
    if (stick) box.scrollTop = box.scrollHeight;
}
async function sendReply() {
    const f = A.sup, input = $('sa-in');
    const text = input.value.trim();
    if (!text || !f.uid) return;
    $('sa-send').disabled = true;
    try {
        const m = await api(`/api/admin/support/${f.uid}`, { method: 'POST', body: { text } });
        input.value = ''; input.style.height = 'auto';
        addThreadMessages([m]);
        loadThreads();
    } catch (e) { toast('Yuborilmadi: ' + e.message, 'err'); }
    $('sa-send').disabled = false; input.focus();
}
// Ochiq suhbat va ro'yxat har 5 soniyada yangilanadi (faqat shu sahifada va oyna ko'rinib turganda)
setInterval(async () => {
    if (document.hidden || A.page !== 'support') return;
    const f = A.sup;
    loadThreads();
    if (f.uid && $('sa-msgs')) {
        try { addThreadMessages((await api(`/api/admin/support/${f.uid}?after=${f.lastId}`)).messages); } catch (e) {}
    }
}, 5000);
