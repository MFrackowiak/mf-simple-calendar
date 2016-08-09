from requests import Session
from datetime import datetime, timezone, timedelta


def time_string(d, t=None):
    if t is None:
        return d.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone(timedelta(hours=t)))
        return d.strftime("%Y-%m-%d %H:%M:%S")


api_adr = "http://localhost:5000/"


if __name__ == '__main__':
    s_1, s_2, s_3 = Session(), Session(), Session()

    result = s_1.put(api_adr + 'user', json={'username': 'sessionUser1', 'password': '12341234', 'timezone': 4})
    print(result.json())
    result = s_1.post(api_adr + 'logout')
    print(result.json())
    result = s_1.get(api_adr + 'calendars')
    print(result.json())
    result = s_1.post(api_adr + 'auth', json={'username': 'sessionUser1', 'password': '12341234'})
    print(result.json(), s_1.get(api_adr + 'calendars').json())

    s_1.put()
