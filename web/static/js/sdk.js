/**
 * Mini Telegram WebApp SDK - tashqi kutubxonasiz
 * Faqat kerakli funksiyalar: initData, user, expand, haptic, theme
 */
(function () {
    'use strict';

    const tg = window.Telegram?.WebApp || {};

    // initDataUnsafe - URL hash dan o'qish
    function parseInitData() {
        const hash = window.location.hash.slice(1);
        if (!hash) return {};
        try {
            const params = new URLSearchParams(hash);
            const initData = params.get('tgWebAppData');
            if (!initData) return {};
            
            const parsed = {};
            for (const [key, value] of new URLSearchParams(initData)) {
                if (key === 'user' || key === 'chat' || key === 'receiver') {
                    try { parsed[key] = JSON.parse(value); }
                    catch { parsed[key] = value; }
                } else {
                    parsed[key] = value;
                }
            }
            return parsed;
        } catch (e) {
            return {};
        }
    }

    // Haptic feedback - vibratsiya
    function haptic(type) {
        if (navigator.vibrate) {
            const patterns = {
                light: [10],
                medium: [20],
                heavy: [30],
                success: [10, 50, 10],
                error: [50, 100, 50]
            };
            try {
                navigator.vibrate(patterns[type] || patterns.light);
            } catch (e) {}
        }
    }

    // WebApp obyektini yig'ish
    window.Telegram = {
        WebApp: {
            initData: tg.initData || '',
            initDataUnsafe: Object.keys(tg.initDataUnsafe || {}).length
                ? tg.initDataUnsafe
                : parseInitData(),
            platform: tg.platform || 'web',
            version: tg.version || '6.0',
            colorScheme: tg.colorScheme || 'dark',
            themeParams: tg.themeParams || {},
            
            ready: () => {
                if (tg.ready) tg.ready();
                console.log('[SDK] ready');
            },
            
            expand: () => {
                if (tg.expand) tg.expand();
                document.documentElement.style.height = '100vh';
                document.body.style.height = '100vh';
            },
            
            close: () => {
                if (tg.close) tg.close();
                else window.history.back();
            },
            
            showAlert: (msg, cb) => {
                if (tg.showAlert) tg.showAlert(msg, cb);
                else alert(msg);
                if (cb) cb();
            },
            
            showConfirm: (msg, cb) => {
                if (tg.showConfirm) tg.showConfirm(msg, cb);
                else cb(confirm(msg));
            },
            
            HapticFeedback: {
                impactOccurred: (style) => haptic(style),
                notificationOccurred: (type) => haptic(type),
                selectionChanged: () => haptic('light')
            },
            
            // Asosiy tugma (ixtiyoriy)
            MainButton: {
                text: '',
                isVisible: false,
                show() { if (tg.MainButton) tg.MainButton.show(); },
                hide() { if (tg.MainButton) tg.MainButton.hide(); },
                setText(t) { if (tg.MainButton) tg.MainButton.setText(t); },
                onClick(cb) { if (tg.MainButton) tg.MainButton.onClick(cb); }
            }
        }
    };

    // Tema ranglarini CSS o'zgaruvchilarga qo'llash
    if (tg.themeParams) {
        const root = document.documentElement;
        if (tg.themeParams.bg_color) root.style.setProperty('--tg-bg', tg.themeParams.bg_color);
        if (tg.themeParams.text_color) root.style.setProperty('--tg-text', tg.themeParams.text_color);
        if (tg.themeParams.button_color) root.style.setProperty('--tg-button', tg.themeParams.button_color);
    }

    console.log('[SDK] loaded. User:', window.Telegram.WebApp.initDataUnsafe?.user);
})();
