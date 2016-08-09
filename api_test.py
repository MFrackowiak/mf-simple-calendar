from requests import Session
from datetime import datetime, timezone, timedelta


def time_string(d, t, save_timezone=True):
    d = d.replace(tzinfo=timezone(timedelta(hours=t)))

    if save_timezone:
        print(d.strftime("%Y-%m-%d %H:%M:%S %z"))
        return d.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        return d.strftime("%Y-%m-%d %H:%M:%S")


api_adr = "http://localhost:5000/"

if __name__ == '__main__':
    s_1, s_2, s_3 = Session(), Session(), Session()

    test_access, test_get = False, False

    result = s_1.put(api_adr + 'user', json={'username': 'sessionUser1', 'password': '12341234', 'timezone': 4})
    print(result.json())

    if test_access:
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

    result = s_2.put(api_adr + 'user', json={'username': 'sessionUser2', 'password': 'qwerqwer', 'timezone': -6}).json()
    if not result['success']:
        s_2.post(api_adr + 'auth', json={'username': 'sessionUser2', 'password': 'qwerqwer'})

    result = s_3.put(api_adr + 'user', json={'username': 'sessionUser3', 'password': 'qwerqwer', 'timezone': 13}).json()
    if not result['success']:
        s_3.post(api_adr + 'auth', json={'username': 'sessionUser3', 'password': 'qwerqwer'})

    if test_get:
        print(s_2.get(api_adr + 'calendar/{}'.format(c_1)).json())
        print(s_1.get(api_adr + 'calendar/{}'.format(c_1)).json())
        print(s_1.get(api_adr + 'calendar/{}'.format(999)).json())

    us = s_1.get(api_adr + 'users/{}'.format('sessionUser')).json()
    print(us)
    us = us['users_like']

    u1, u2, u3 = us[0]['user_id'], us[1]['user_id'], us[2]['user_id']

    s_c_1_u_2 = s_1.put(api_adr + 'calendar/{}/share'.format(c_1), json={'user_id': u2,
                                                                         'write_permission': False}).json()['share_id']

    t = datetime.utcnow()
    print(s_2.put(api_adr + 'calendar/{}/event'.format(c_1), json={'event_name': 'test1', 'event_description': 'desc',
                                                                   'start_time': time_string(t, -5),
                                                                   'end_time': time_string(t + timedelta(hours=24), -5),
                                                                   'all_day_event': True}).json())
    s_1.post(api_adr + 'share/{}'.format(s_c_1_u_2), json={'write_permission': True})

    event_json = s_2.put(api_adr + 'calendar/{}/event'.format(c_1),
                         json={'event_name': 'test1', 'event_description': 'desc',
                               'start_time': time_string(t, -5),
                               'end_time': time_string(t + timedelta(hours=24), -5),
                               'all_day_event': True}).json()
    print(event_json)

    print(s_1.get(api_adr + 'calendar/{}'.format(c_1)).json())
    print(s_2.get(api_adr + 'calendar/{}'.format(c_1)).json())

    print(s_2.put(api_adr + 'event/{}/invite'.format(event_json['event_id']), json={'user_id': u3}).json())
    print(s_3.get(api_adr + 'invites').json())
