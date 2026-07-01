import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
SECRET = re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S+")


def sanitize_message(message: str) -> str:
    message = EMAIL.sub("[邮箱已脱敏]", message)
    message = PHONE.sub("[手机号已脱敏]", message)
    return SECRET.sub("[密钥已脱敏]", message)

