import hashlib

from datetime import timezone, timedelta

from .config import salt_1, salt_2


def get_password_hash(password):
    return hashlib.sha256((salt_1 + password + salt_2).encode()).hexdigest()


def set_utc(d):
    return d.replace(tzinfo=timezone(timedelta(hours=0)))
