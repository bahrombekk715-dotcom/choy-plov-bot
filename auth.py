"""Telegram Web App initData tekshiruvi va admin tokenlari."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from config import BOT_TOKEN, SECRET_KEY


def validate_init_data(init_data: str, max_age: int = 86400):
    """initData ni Telegram qoidasi bo'yicha tekshiradi. To'g'ri bo'lsa user dict, aks holda None."""
    if not init_data or not BOT_TOKEN:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = pairs.pop('hash', None)
        if not received_hash:
            return None
        check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, received_hash):
            return None
        if time.time() - int(pairs.get('auth_date', 0)) > max_age:
            return None
        user = json.loads(pairs.get('user', 'null'))
        return user if user and 'id' in user else None
    except Exception:
        return None


def make_admin_token(ttl: int = 12 * 3600) -> str:
    exp = str(int(time.time()) + ttl)
    sig = hmac.new(SECRET_KEY.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def verify_admin_token(token: str) -> bool:
    try:
        exp, sig = token.split('.', 1)
        good = hmac.new(SECRET_KEY.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, good) and int(exp) > time.time()
    except Exception:
        return False
