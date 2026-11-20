import hmac
import hashlib
import time
import secrets
import json
import base64
from typing import Dict, Any, Optional
from shared.config.settings import settings
from logging_helper import LOGGER

try:
    from jose import jwt, JWTError
except ImportError:
    class JWTError(Exception):
        pass

    class _FallbackJWT:
        @staticmethod
        def encode(payload: dict, key: str, algorithm: str = "HS256") -> str:
            def b64url(data: bytes) -> str:
                return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')
            header = {"typ": "JWT", "alg": algorithm}
            seg1 = b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))
            seg2 = b64url(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
            signing_input = f"{seg1}.{seg2}".encode('utf-8')
            sig = hmac.new(key.encode('utf-8'), signing_input, hashlib.sha256).digest()
            seg3 = b64url(sig)
            return f"{seg1}.{seg2}.{seg3}"

        @staticmethod
        def decode(token: str, key: str, algorithms: list = None) -> dict:
            try:
                parts = token.split(".")
                if len(parts) != 3:
                    raise JWTError("Invalid token structure")
                seg1, seg2, seg3 = parts
                def b64url_decode(s: str) -> bytes:
                    padding = 4 - (len(s) % 4)
                    if padding != 4:
                        s += "=" * padding
                    return base64.urlsafe_b64decode(s)
                signing_input = f"{seg1}.{seg2}".encode('utf-8')
                expected_sig = hmac.new(key.encode('utf-8'), signing_input, hashlib.sha256).digest()
                actual_sig = b64url_decode(seg3)
                if not hmac.compare_digest(expected_sig, actual_sig):
                    raise JWTError("Invalid signature")
                payload = json.loads(b64url_decode(seg2).decode('utf-8'))
                if "exp" in payload and payload["exp"] < time.time():
                    raise JWTError("Token expired")
                return payload
            except Exception as e:
                raise JWTError(str(e))

    jwt = _FallbackJWT()

def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """Generate signed JWT access token"""
    to_encode = data.copy()
    expire = time.time() + (expires_delta or (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and cryptographically verify signed JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_telegram_auth(auth_data: Dict[str, Any]) -> bool:
    """Verify cryptographic authenticity of Telegram Login Widget data using SHA256 HMAC"""
    if "hash" not in auth_data:
        return False
    check_hash = auth_data["hash"]
    data_check_arr = []
    for k, v in sorted(auth_data.items()):
        if k != "hash":
            data_check_arr.append(f"{k}={v}")
    data_check_string = "\n".join(data_check_arr)

    # Use bot token as HMAC secret
    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_hash, check_hash)

def hash_password(password: str) -> str:
    """Generate salted SHA-256 hash for secure local web user credentials"""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored salted hash"""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, key_hex = hashed_password.split("$", 1)
        expected_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(expected_key.hex(), key_hex)
    except Exception:
        return False
