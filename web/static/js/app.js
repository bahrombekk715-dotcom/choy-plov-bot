// SDK orqali Telegram obyekti (agar mavjud bo'lmasa - fallback)
const tg = window.Telegram?.WebApp || {
    initData: '',
    initDataUnsafe: { user: null },
    ready: () => {},
    expand: () => {},
    close: () => {},
    showAlert: alert,
    HapticFeedback: { impactOccurred: () => {}, notificationOccurred: () => {} }
};

tg.expand?.();
tg.ready?.();

// ============ STATE ============
const state = {
    user: tg.initDataUnsafe?.user || null,
    categories: [],
    products: [],
    cart: [],
    currentCategory: null,
    currentTab: 'menu',
    orderFilter: 'all',
    userOrders: [],
    userInfo: null,
    lang: localStorage.getItem('lang') || 'uz'
};

// ============ HELPERS ============
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const fmt = (n) => Number(n || 0).toLocaleString('uz-UZ') + " so'm";

function toast(msg, duration = 2000) {
    const el = $('#toast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._timer);
    el._timer = setTimeout(() => el.classList.remove('show'), duration);
    tg.HapticFeedback?.impactOccurred?.('light');
}

function imgUrl(u) {
    if (!u) return null;
    if (/^https?:\/\//i.test(u)) return u;
    if (u.startsWith('/')) return u;
    return `/api/image/${encodeURIComponent(u)}`;
}

// ============ INIT ============
document.addEventListener('DOMContentLoaded', async () => {
    // Skeleton
    $('#products').innerHTML = Array(4).fill('<div class="skeleton skeleton-card"></div>').join('');
    
    if (state.user) await loadUserInfo();
    await loadCategories();
    loadCart();
});

async function loadUserInfo() {
    try {
        const res = await fetch(`/api/user/${state.user.id}`);
        if (res.ok) {
            const data = await res.json();
            state.userInfo = data;
            if (data.phone_number && data.phone_number !== 'temp') {
                $('#input-phone').value = data.phone_number;
            }
            if (data.language) state.lang = data.language;
        }
    } catch (e) { console.error(e); }
}

// ============ KATEGORIYALAR ============
async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        state.categories = await res.json();
        renderCategories();
        if (state.categories.length > 0) {
            state.currentCategory = state.categories[0].id;
            await loadProducts(state.currentCategory);
        } else {
            $('#products').innerHTML = emptyHTML('📂', "Kategoriyalar yo'q");
        }
    } catch (e) {
        console.error(e);
        toast("Xatolik yuz berdi");
    }
}

function renderCategories() {
    $('#categories').innerHTML = state.categories.map(cat => `
        <button class="cat-chip ${cat.id === state.currentCategory ? 'active' : ''}"
                onclick="selectCategory(${cat.id})">${cat.name}</button>
    `).join('');
}

async function selectCategory(id) {
    state.currentCategory = id;
    renderCategories();
    $('#products').innerHTML = Array(4).fill('<div class="skeleton skeleton-card"></div>').join('');
    await loadProducts(id);
}

// ============ MAHSULOTLAR ============
async function loadProducts(categoryId) {
    try {
        const res = await fetch(`/api/products/${categoryId}`);
        state.products = await res.json();
        renderProducts();
    } catch (e) { console.error(e); }
}

function renderProducts() {
    const container = $('#products');
    if (state.products.length === 0) {
        container.innerHTML = emptyHTML('🍽', "Bu kategoriyada mahsulot yo'q");
        return;
    }
    container.innerHTML = state.products.map(prod => {
        const img = imgUrl(prod.image_url);
        return `
            <div class="product-card" onclick="openProduct(${prod.id})">
                <div class="product-img">
                    ${img
                        ? `<img src="${img}" alt="${prod.name}" onerror="this.parentElement.innerHTML='🍲'">`
                        : '🍲'}
                </div>
                <div class="product-info">
                    <div class="product-name">${prod.name}</div>
                    <div class="product-desc">${prod.description || 'Mazali taom'}</div>
                    <div class="product-price">${fmt(prod.price)}</div>
                </div>
            </div>`;
    }).join('');
}

function emptyHTML(icon, text) {
    return `<div class="empty" style="grid-column:1/-1;">
        <div class="empty-icon">${icon}</div><p>${text}</p>
    </div>`;
}

// ============ MAHSULOT DETAL ============
async function openProduct(id) {
    try {
        const res = await fetch(`/api/product/${id}`);
        const prod = await res.json();
        const img = imgUrl(prod.image_url);
        $('#product-detail').innerHTML = `
            <div class="detail-image">
                ${img ? `<img src="${img}" onerror="this.parentElement.innerHTML='🍲'">` : '🍲'}
            </div>
            <div class="detail-name">${prod.name}</div>
            <div class="detail-desc">${prod.description || ''}</div>
            <div class="detail-price">${fmt(prod.price)}</div>
            <button class="btn-primary" onclick="addToCart(${prod.id}, '${(prod.name||'').replace(/'/g,"\\'")}', ${prod.price})">
                🛒 Savatga qo'shish
            </button>`;
        $('#product-modal').classList.add('active');
    } catch (e) { toast("Xatolik"); }
}

function closeProductModal() {
    $('#product-modal').classList.remove('active');
}

// ============ SAVAT ============
function loadCart() {
    try {
        const saved = localStorage.getItem('cart');
        if (saved) state.cart = JSON.parse(saved);
    } catch (e) { state.cart = []; }
    updateCartBadge();
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(state.cart));
    updateCartBadge();
}

function updateCartBadge() {
    const total = state.cart.reduce((s, i) => s + i.quantity, 0);
    $('#cart-count').textContent = total;
}

function addToCart(id, name, price) {
    const existing = state.cart.find(i => i.product_id === id);
    if (existing) existing.quantity++;
    else state.cart.push({ product_id: id, name, price, quantity: 1 });
    saveCart();
    closeProductModal();
    toast(`✓ ${name} savatga qo'shildi`);
}

function showCart() {
    renderCartItems();
    $('#cart-modal').classList.add('active');
}
function hideCart() { $('#cart-modal').classList.remove('active'); }

function renderCartItems() {
    const c = $('#cart-items');
    if (state.cart.length === 0) {
        c.innerHTML = emptyHTML('🛒', "Savat bo'sh");
        $('#cart-total').textContent = fmt(0);
        return;
    }
    c.innerHTML = state.cart.map((item, idx) => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-name">${item.name}</div>
                <div class="cart-item-price">${fmt(item.price)}</div>
            </div>
            <div class="qty-controls">
                <button class="qty-btn" onclick="changeQty(${idx}, -1)">−</button>
                <span>${item.quantity}</span>
                <button class="qty-btn" onclick="changeQty(${idx}, 1)">+</button>
            </div>
        </div>`).join('');
    const total = state.cart.reduce((s, i) => s + i.price * i.quantity, 0);
    $('#cart-total').textContent = fmt(total);
}

function changeQty(idx, delta) {
    state.cart[idx].quantity += delta;
    if (state.cart[idx].quantity <= 0) state.cart.splice(idx, 1);
    saveCart();
    renderCartItems();
}

// ============ CHECKOUT ============
function openCheckout() {
    if (state.cart.length === 0) { toast("Savat bo'sh!"); return; }
    hideCart();
    const total = state.cart.reduce((s, i) => s + i.price * i.quantity, 0);
    $('#checkout-total').textContent = fmt(total);
    $('#checkout-modal').classList.add('active');
}
function closeCheckout() { $('#checkout-modal').classList.remove('active'); }

async function submitOrder() {
    const phone = $('#input-phone').value.trim();
    const address = $('#input-address').value.trim();
    const comment = $('#input-comment').value.trim();

    if (!phone || !address) { toast("Telefon va manzilni to'ldiring!"); return; }
    if (!state.user) { toast("Foydalanuvchi topilmadi!"); return; }

    const btn = event.target;
    btn.disabled = true;
    btn.textContent = "Yuborilmoqda...";

    try {
        const res = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                initData: tg.initData || 'web',
                user_id: state.user.id,
                phone, address, comment,
                cart: state.cart.map(i => ({
                    product_id: i.product_id,
                    quantity: i.quantity,
                    addons: []
                }))
            })
        });
        const data = await res.json();
        if (data.success) {
            state.cart = [];
            saveCart();
            closeCheckout();
            toast("✅ Buyurtmangiz qabul qilindi!");
            tg.HapticFeedback?.notificationOccurred?.('success');
            setTimeout(() => switchTab('orders', $$('.nav-btn')[1]), 500);
        } else {
            toast("Xatolik: " + (data.detail || "Noma'lum"));
        }
    } catch (e) {
        toast("Server bilan bog'lanishda xatolik");
    } finally {
        btn.disabled = false;
        btn.textContent = "✓ Buyurtmani tasdiqlash";
    }
}

// ============ TABLAR ============
function switchTab(tab, btn) {
    state.currentTab = tab;
    $$('.page').forEach(p => p.classList.remove('active'));
    $$('.nav-btn').forEach(b => b.classList.remove('active'));
    $(`#page-${tab}`).classList.add('active');
    if (btn) btn.classList.add('active');
    if (tab === 'orders') loadOrders();
    if (tab === 'profile') loadProfile();
}

// ============ BUYURTMALAR ============
async function loadOrders() {
    if (!state.user) return;
    try {
        const res = await fetch(`/api/orders/${state.user.id}`);
        state.userOrders = await res.json();
        renderOrders();
    } catch (e) { console.error(e); }
}

function filterOrders(f, btn) {
    state.orderFilter = f;
    $$('.filter-tab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderOrders();
}

function renderOrders() {
    const c = $('#orders-list');
    let orders = state.userOrders;
    if (state.orderFilter !== 'all') orders = orders.filter(o => o.status === state.orderFilter);

    if (orders.length === 0) { c.innerHTML = emptyHTML('📭', "Buyurtmalar yo'q"); return; }

    const st = {
        pending: { t: "Kutilmoqda", c: "badge-pending" },
        completed: { t: "Tasdiqlangan", c: "badge-completed" },
        cancelled: { t: "Bekor", c: "badge-cancelled" }
    };
    c.innerHTML = orders.map(o => {
        const s = st[o.status] || st.pending;
        const d = new Date(o.created_at).toLocaleString('uz-UZ', {
            day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
        });
        return `
            <div class="order-card">
                <div class="order-header">
                    <span class="order-number">#${o.id}</span>
                    <span class="order-badge ${s.c}">${s.t}</span>
                </div>
                <div class="order-meta">📅 ${d}</div>
                <div class="order-meta">📍 ${o.address}</div>
                <div class="order-items-mini">
                    ${o.items.map(i => `<div><span>${i.product_name} × ${i.quantity}</span>
                        <span>${fmt(i.price)}</span></div>`).join('')}
                </div>
                <div class="order-total">
                    <strong>${fmt(o.total_price)}</strong>
                    <button class="btn-reorder" onclick="reorder(${o.id})">🔄 Qayta buyurtma</button>
                </div>
            </div>`;
    }).join('');
}

async function reorder(orderId) {
    const order = state.userOrders.find(o => o.id === orderId);
    if (!order) return;
    for (const item of order.items) {
        const r = await fetch(`/api/product/${item.product_id}`);
        if (!r.ok) continue;
        const p = await r.json();
        addToCart(p.id, p.name, p.price);
    }
    showCart();
}

// ============ PROFIL ============
async function loadProfile() {
    const c = $('#profile-content');
    if (!state.user) { c.innerHTML = emptyHTML('❓', "Ma'lumot yo'q"); return; }

    const orders = state.userOrders.length
        ? state.userOrders
        : await fetch(`/api/orders/${state.user.id}`).then(r => r.json()).catch(() => []);
    const completed = orders.filter(o => o.status === 'completed');
    const total = completed.reduce((s, o) => s + o.total_price, 0);
    const initial = (state.user.first_name || 'U')[0].toUpperCase();
    const reg = state.userInfo?.created_at
        ? new Date(state.userInfo.created_at).toLocaleDateString('uz-UZ')
        : '-';

    c.innerHTML = `
        <div class="profile-header">
            <div class="avatar">${initial}</div>
            <div class="profile-info">
                <h3>${state.user.first_name || 'Foydalanuvchi'}</h3>
                <p>@${state.user.username || 'username'}</p>
                <p>📞 ${state.userInfo?.phone_number || '-'}</p>
                <p>📅 ${reg}</p>
            </div>
        </div>
        <div class="profile-stats">
            <div class="stat-box"><small>Buyurtmalar</small><strong>${orders.length}</strong></div>
            <div class="stat-box"><small>Sarflangan</small><strong>${total.toLocaleString()}</strong></div>
        </div>
        <div class="settings-section">
            <h4>🌐 Til</h4>
            <div class="lang-buttons">
                <button class="lang-btn ${state.lang==='uz'?'active':''}" onclick="changeLang('uz')">O'zbekcha</button>
                <button class="lang-btn ${state.lang==='ru'?'active':''}" onclick="changeLang('ru')">Русский</button>
                <button class="lang-btn ${state.lang==='en'?'active':''}" onclick="changeLang('en')">English</button>
            </div>
        </div>`;
}

function changeLang(lang) {
    state.lang = lang;
    localStorage.setItem('lang', lang);
    loadProfile();
    toast("Til o'zgartirildi");
}
