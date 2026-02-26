import hashlib
import hmac
import os
import secrets

# "Pepper" secret (server-side). Put in .env later.
API_KEY_PEPPER = os.getenv("LARIBA_API_KEY_PEPPER", "CHANGE_ME_PEPPER")

def generate_api_key() -> str:
    # URL-safe random token (~43 chars)
    return secrets.token_urlsafe(32)

def key_prefix(raw_key: str, length: int = 8) -> str:
    return raw_key[:length]

def hash_api_key(raw_key: str) -> str:
    # HMAC-SHA256(key=pepper, msg=raw_key)
    digest = hmac.new(API_KEY_PEPPER.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest
