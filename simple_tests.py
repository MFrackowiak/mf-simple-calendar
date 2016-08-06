from calendar.var_utils import get_password_hash
from datetime import datetime, timedelta, timezone


if __name__ == '__main__':
    a = get_password_hash("admin1")
    print(a)
    print(len(a))

    b = get_password_hash("ęąśćłó")
    print(b)
    print(len(b))

    d = datetime.now(timezone(timedelta(hours=0)))
    print(d.isoformat())
    print(d.timetz())
    print(d.astimezone(timezone(timedelta(hours=2))))

    d = datetime.now()
    d = d.replace(tzinfo=timezone(timedelta(hours=0)))
    print(d.isoformat())
    print(d.timetz())
    print(d.astimezone(timezone(timedelta(hours=2))))
