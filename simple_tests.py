from calendar_app.var_utils import get_password_hash
from datetime import datetime, timedelta, timezone

import requests

if __name__ == '__main__':
    a = get_password_hash("admin1")
    print(a)
    print(len(a))

    b = get_password_hash("ęąśćłó")
    print(b)
    print(len(b))

    d = datetime.now(timezone(timedelta(hours=0)))
    print(d)
    print(d.isoformat())
    print(d.timetz())
    print(d.astimezone(timezone(timedelta(hours=2))))

    d = datetime.now()
    print(d)
    d = d.replace(tzinfo=timezone(timedelta(hours=0)))
    print(d.isoformat())
    print(d.timetz())
    print(d.astimezone(timezone(timedelta(hours=2))))

    res = requests.post('http://localhost:5000/test',
                        json={'date': datetime.utcnow().replace(tzinfo=timezone(timedelta(hours=2))).strftime(
                            "%Y-%m-%d %H:%M:%S %z")})
    res = requests.post('http://localhost:5000/test',
                        json={'date': datetime.utcnow().replace(tzinfo=timezone(timedelta(hours=2))).strftime(
                            "%Y-%m-%d %H:%M:%S"), 'tz': 2})
