from calendar_app.calendar import Calendar


if __name__ == '__main__':
    calendar = Calendar()

    print(calendar.add_user('user1', '1234512345', 0))
    print(calendar.add_user('user2', '43214321', -11))
    print(calendar.add_user('user3', 'qwerqwer', 12))
    print(calendar.add_user('user4', 'testtest', 2))

    u = calendar.authorize_user('user1', '1234512345')
    print(u)
    u1_id, u1_tz = u['user_id'], u['tz']

    u = calendar.authorize_user('user2', '43214321')
    print(u)
    u2_id, u2_tz = u['user_id'], u['tz']

    u = calendar.authorize_user('user3', 'qwerqwer')
    print(u)
    u3_id, u3_tz = u['user_id'], u['tz']

    u = calendar.authorize_user('user4', 'testtest')
    print(u)
    u4_id, u4_tz = u['user_id'], u['tz']

    c = calendar.add_calendar(u1_id, '1calendar', 'meh')
    print(c)
    c = calendar.add_calendar(u1_id, '1calendar', 'red')
    print(c)
    print(calendar.get_calendars(u1_id))
    print(calendar.edit_calendar(u1_id, c['calendar_id'], '1calednar2', 'pink'))
    print(calendar.get_calendars(u1_id))

    print(calendar.get_events(u2_id, u2_tz, c['calendar_id']))
    print(calendar.share_calendar(u1_id, c['calendar_id'], u2_id, False))
    print(calendar.get_events(u2_id, u2_tz, c['calendar_id']))
    print(calendar.get_calendars(u2_id))


