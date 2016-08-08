from calendar_app.calendar import Calendar
from datetime import datetime, timezone, timedelta


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
    s = calendar.share_calendar(u1_id, c['calendar_id'], u2_id, False)
    print(s)
    print(calendar.get_events(u2_id, u2_tz, c['calendar_id']))
    print(calendar.get_calendars(u2_id))

    e = calendar.add_event(u1_id, c['calendar_id'], 'event_test_name', 'event_test_description',
                           datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                           (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S"), 4, False)
    print(e)
    print(calendar.invite_user(u2_id, e['event_id'], u3_id))
    calendar.edit_share_permission(u1_id, s['share_id'], True)
    i2_id = calendar.invite_user(u2_id, e['event_id'], u3_id)['invite_id']
    print(i2_id)

    i1_id = calendar.get_invites(u1_id, u1_tz)['invites'][0]['invite_id']
    print(calendar.get_invites(u2_id, u2_tz))
    print(calendar.get_invites(u3_id, u3_tz))
    print(calendar.get_invites(u4_id, u4_tz))

    print(calendar.get_guests(u4_id, e['event_id']))
    print(calendar.get_guests(u2_id, e['event_id']))

    print(calendar.edit_invite_attendance(u3_id, i2_id, 4))
    print(calendar.edit_invite_attendance(u3_id, i2_id, 3))

    print(calendar.get_guests(u2_id, e['event_id']))

    print(calendar.get_invites(u3_id, u3_tz))

    calendar.edit_invite(u3_id, i2_id, 'my_own_name', None, None, None, None, True)
    print(calendar.get_invites(u3_id, u3_tz))

    calendar.edit_invite(u1_id, i1_id, None, 'new_desc',
                         (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
                         (datetime.utcnow() + timedelta(days=10, hours=8)).strftime("%Y-%m-%d %H:%M:%S"), 4, False)
    # print(calendar.get_invites(u3_id, u3_tz))

    calendar.edit_invite(u1_id, i1_id, 'new_name', 'new_desc',
                         (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
                         (datetime.utcnow() + timedelta(days=10, hours=8)).strftime("%Y-%m-%d %H:%M:%S"), 4, False)
    print(calendar.get_invites(u3_id, u3_tz))

    # calendar.delete_event(u1_id, e['event_id'])
    # calendar.delete_calendar(u1_id, c['calendar_id'])

    print(calendar.get_invites(u3_id, u3_tz))

    print(calendar.invite_user(u1_id, c['calendar_id'], 999))
