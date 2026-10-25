// Telegram Web App API
let tg = window.Telegram.WebApp;
tg.expand();
tg.MainButton.hide();
tg.setHeaderColor('#0a0e27');
tg.setBackgroundColor('#0a0e27');

// Global variables
let currentProduct = null;
let currentCategory = null;
let cart = [];
let userData = null;
let currentSection = 'menu';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    // Get user data from Telegram
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        userData = tg.initDataUnsafe.user;
        console.log('User:', userData);
    }

    // Load categories
    await loadCategories();
    updateCartCount();

    // Tab navigation
    setupTabs();
});

// Setup tabs
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.dataset.tab;
            if (tab === 'menu') {
                loadCategories();
            } else if (tab === 'drinks') {
                // Load drinks category
                loadCategoryProducts('drinks');
            }
        });
    });
}

// Load categories
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();

        const container = document.getElementById('categories-list');
        container.innerHTML = '';

        if (categories.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📂</div>
                    <p>Kategoriyalar mavjud emas</p>
                </div>
            `;
            return;
        }

        categories.forEach(category => {
            const card = document.createElement('div');
            card.className = 'category-card';
            card.onclick = () => showProducts(category.id, category.name);

            // Category icons
            const icons = {
                'Plov': '🍚',
                'Plovlar': '🍚',
                'Choy': '☕',
                'Ichimliklar': '🥤',
                'Shirinliklar': '🍰'
            };

            const icon = icons[category.name] || '🍽';

            card.innerHTML = `
                <div class="icon">${icon}</div>
                <h3>${category.name}</h3>
                <div class="count">3 ta mahsulot</div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
        showError('Kategoriyalarni yuklashda xatolik');
    }
}

// Show products
async function showProducts(categoryId, categoryName) {
    currentCategory = categoryId;

    try {
        const response = await fetch(`/api/products/${categoryId}`);
        const products = await response.json();

        document.getElementById('category-title').textContent = categoryName;
        document.getElementById('categories-section').classList.add('hidden');
        document.getElementById('products-section').classList.remove('hidden');

        const container = document.getElementById('products-list');
        container.innerHTML = '';

        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📦</div>
                    <p>Bu kategoriyada mahsulot yo'q</p>
                </div>
            `;
            return;
        }

        products.forEach(product => {
            const card = document.createElement('div');
            card.className = `product-card ${!product.is_available ? 'unavailable' : ''}`;

            if (product.is_available) {
                card.onclick = () => showProductModal(product);
            }

            // Product image
            let imageHTML = '<div class="product-image">📸</div>';
            if (product.image_url) {
                if (product.image_url.startsWith('http')) {
                    imageHTML = `<div class="product-image"><img src="${product.image_url}" alt="${product.name}"></div>`;
                } else {
                    // Telegram file_id
                    imageHTML = `<div class="product-image"><img src="/api/image/${product.image_url}" alt="${product.name}"></div>`;
                }
            }

            card.innerHTML = `
                ${imageHTML}
                <div class="product-info">
                    <h3>${product.name}</h3>
                    ${product.description ? `<p>${product.description}</p>` : ''}
                    <p class="price">${formatPrice(product.price)} so'm</p>
                </div>
                <div class="product-badge ${!product.is_available ? 'unavailable' : ''}">
                    ${product.is_available ? '✓' : '✗'}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading products:', error);
        showError('Mahsulotlarni yuklashda xatolik');
    }
}

// Show categories
function showCategories() {
    document.getElementById('products-section').classList.add('hidden');
    document.getElementById('categories-section').classList.remove('hidden');
}

// Show product modal
function showProductModal(product) {
    currentProduct = product;

    document.getElementById('modal-product-name').textContent = product.name;
    document.getElementById('modal-product-description').textContent = product.description || '';
    document.getElementById('modal-product-price').textContent = `${formatPrice(product.price)} so'm`;
    document.getElementById('quantity').value = 1;

    // Product image in modal
    const imageContainer = document.getElementById('modal-product-image');
    if (product.image_url) {
        if (product.image_url.startsWith('http')) {
            imageContainer.innerHTML = `<img src="${product.image_url}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 12px;">`;
        } else {
            imageContainer.innerHTML = `<img src="/api/image/${product.image_url}" alt="${product.name}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 12px;">`;
        }
    } else {
        imageContainer.innerHTML = '📸';
    }

    // Reset addons
    document.querySelectorAll('input[name="addon"]').forEach(cb => cb.checked = false);

    const modal = document.getElementById('product-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

// Close product modal
function closeProductModal() {
    const modal = document.getElementById('product-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

// Change quantity
function changeQuantity(delta) {
    const input = document.getElementById('quantity');
    let value = parseInt(input.value) + delta;
    if (value < 1) value = 1;
    if (value > 10) value = 10;
    input.value = value;
}

// Add to cart
function addToCart() {
    if (!currentProduct) return;

    const quantity = parseInt(document.getElementById('quantity').value);
    const selectedAddons = [];

    document.querySelectorAll('input[name="addon"]:checked').forEach(cb => {
        selectedAddons.push(cb.value);
    });

    // Calculate price
    let price = currentProduct.price * quantity;
    const addonPrices = {
        'meat': 15000,
        'egg': 5000,
        'qazi': 20000
    };

    let addonsText = [];
    selectedAddons.forEach(addon => {
        price += addonPrices[addon] * quantity;
        const addonNames = {
            'meat': '🍖 Go\'sht',
            'egg': '🥚 Tuxum',
            'qazi': '🧀 Qazi'
        };
        addonsText.push(addonNames[addon]);
    });

    // Add to cart
    cart.push({
        product_id: currentProduct.id,
        name: currentProduct.name,
        quantity: quantity,
        addons: selectedAddons,
        addonsText: addonsText.join(', '),
        price: price
    });

    updateCartCount();
    closeProductModal();

    // Show haptic feedback
    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred('success');
    }

    // Show notification
    tg.showPopup({
        title: 'Muvaffaqiyatli!',
        message: `"${currentProduct.name}" savatchaga qo'shildi`,
        buttons: [{type: 'ok'}]
    });
}

// Update cart count
function updateCartCount() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    const badge = document.getElementById('cart-count');
    badge.textContent = count;

    if (count > 0) {
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

// Show cart
function showCart() {
    if (cart.length === 0) {
        tg.showPopup({
            title: 'Savat bo\'sh',
            message: 'Hozircha savatingizda mahsulot yo\'q',
            buttons: [{type: 'ok'}]
        });
        return;
    }

    const container = document.getElementById('cart-items');
    container.innerHTML = '';

    let total = 0;

    cart.forEach((item, index) => {
        total += item.price;

        const cartItem = document.createElement('div');
        cartItem.className = 'cart-item';
        cartItem.innerHTML = `
            <div class="cart-item-info">
                <h4>${item.name} ×${item.quantity}</h4>
                ${item.addonsText ? `<p>${item.addonsText}</p>` : ''}
                <p class="cart-item-price">${formatPrice(item.price)} so'm</p>
            </div>
            <div class="cart-item-actions">
                <button class="cart-item-remove" onclick="removeFromCart(${index})">🗑</button>
            </div>
        `;
        container.appendChild(cartItem);
    });

    document.getElementById('cart-total').textContent = `${formatPrice(total)} so'm`;

    const modal = document.getElementById('cart-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

// Close cart
function closeCart() {
    const modal = document.getElementById('cart-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

// Remove from cart
function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartCount();

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred('light');
    }

    if (cart.length === 0) {
        closeCart();
    } else {
        showCart();
    }
}

// Checkout
function checkout() {
    if (cart.length === 0) {
        tg.showAlert('Savat bo\'sh');
        return;
    }

    closeCart();

    // Pre-fill user data
    if (userData) {
        const phone = userData.phone_number || '';
        document.getElementById('phone').value = phone;
    }

    // Show checkout items
    const container = document.getElementById('checkout-items');
    container.innerHTML = '';

    let total = 0;

    cart.forEach(item => {
        total += item.price;

        const checkoutItem = document.createElement('div');
        checkoutItem.className = 'checkout-item';
        checkoutItem.innerHTML = `
            <div>
                <div class="checkout-item-name">${item.name} ×${item.quantity}</div>
                ${item.addonsText ? `<div class="checkout-item-qty">${item.addonsText}</div>` : ''}
            </div>
            <div class="checkout-item-price">${formatPrice(item.price)}</div>
        `;
        container.appendChild(checkoutItem);
    });

    document.getElementById('checkout-total').textContent = `${formatPrice(total)} so'm`;

    const modal = document.getElementById('checkout-modal');
    modal.classList.remove('hidden');
    setTimeout(() => modal.classList.add('show'), 10);
}

// Close checkout
function closeCheckout() {
    const modal = document.getElementById('checkout-modal');
    modal.classList.remove('show');
    setTimeout(() => modal.classList.add('hidden'), 300);
}

// Confirm order
async function confirmOrder() {
    const phone = document.getElementById('phone').value.trim();
    const address = document.getElementById('address').value.trim();
    const comment = document.getElementById('comment').value.trim();

    if (!phone) {
        tg.showAlert('Telefon raqamni kiriting!');
        return;
    }

    if (!address) {
        tg.showAlert('Manzilni kiriting!');
        return;
    }

    if (!userData) {
        tg.showAlert('Foydalanuvchi ma\'lumotlari topilmadi!');
        return;
    }

    try {
        tg.MainButton.showProgress();

        const response = await fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                initData: tg.initData,
                user_id: userData.id,
                phone: phone,
                address: address,
                comment: comment || null,
                cart: cart
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('order-number').textContent = result.order_id;

            closeCheckout();

            const modal = document.getElementById('success-modal');
            modal.classList.remove('hidden');
            setTimeout(() => modal.classList.add('show'), 10);

            // Haptic feedback
            if (tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('success');
            }

            // Clear cart
            cart = [];
            updateCartCount();

            // Clear form
            document.getElementById('phone').value = '';
            document.getElementById('address').value = '';
            document.getElementById('comment').value = '';
        } else {
            tg.showAlert('Buyurtmani rasmiylashtirish xatolik!');
        }
    } catch (error) {
        console.error('Error creating order:', error);
        tg.showAlert('Xatolik yuz berdi. Qaytadan urinib ko\'ring.');
    } finally {
        tg.MainButton.hideProgress();
    }
}

// Close success modal
function closeSuccess() {
    const modal = document.getElementById('success-modal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.classList.add('hidden');
        showCategories();
    }, 300);
}

// Show section (bottom nav)
function showSection(section) {
    currentSection = section;

    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');

    // Handle sections
    if (section === 'menu') {
        showCategories();
    } else if (section === 'favorites') {
        tg.showAlert('Sevimli mahsulotlar tez orada!');
    } else if (section === 'orders') {
        tg.showAlert('Buyurtmalar tarixi tez orada!');
    } else if (section === 'profile') {
        tg.showAlert('Profil sahifasi tez orada!');
    }
}

// Format price
function formatPrice(price) {
    return new Intl.NumberFormat('uz-UZ').format(price);
}

// Show error
function showError(message) {
    tg.showAlert(message);
}

// Close modal on backdrop click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            const modalId = modal.id;
            if (modalId === 'product-modal') closeProductModal();
            else if (modalId === 'cart-modal') closeCart();
            else if (modalId === 'checkout-modal') closeCheckout();
            else if (modalId === 'success-modal') closeSuccess();
        }
    });
});
