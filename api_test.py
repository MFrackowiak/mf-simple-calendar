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

    result = s_1.put(api_adr + 'calendar', json={'calendar_name': 'My First Calendar',
                                                 'calendar_color': 'darkred'}).json()
    print(result)
    c_1 = result['calendar_id']

    result = s_2.put(api_adr + 'user', json={'username': 'user_2', 'password': 'qwerqwer', 'timezone': -6}).json()
    if not result['success']:
        s_2.post(api_adr + 'auth', json={'username': 'user_2', 'password': 'qwerqwer'})

    result = s_3.put(api_adr + 'user', json={'username': 'user_3', 'password': 'qwerqwer', 'timezone': 13}).json()
    if not result['success']:
        s_3.post(api_adr + 'auth', json={'username': 'user_3', 'password': 'qwerqwer'})

    print(s_2.get(api_adr + 'calendar/{}'.format(c_1)).json())
    print(s_1.get(api_adr + 'calendar/{}'.format(c_1)).json())
    print(s_1.get(api_adr + 'calendar/{}'.format(999)).json())

    print(s_1.get(api_adr + 'users/{}'.format('user_')).json())

    print(s_1.put(api_adr + 'calendar/{}/share'.format(c_1)).json())
